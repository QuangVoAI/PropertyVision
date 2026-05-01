from __future__ import annotations

import random
from datetime import datetime, timedelta

import pandas as pd

from src.db import get_connection, initialize_schema
from src.etl import clean_price


random.seed(42)


CITIES = {
    "TP.HCM": {
        "districts": {
            "Quận 1": (10.7769, 106.7009, 220),
            "Quận 2": (10.7870, 106.7498, 145),
            "Quận 7": (10.7342, 106.7218, 110),
            "Bình Thạnh": (10.8106, 106.7091, 125),
            "Thủ Đức": (10.8491, 106.7537, 95),
        }
    },
    "Hà Nội": {
        "districts": {
            "Ba Đình": (21.0338, 105.8142, 180),
            "Cầu Giấy": (21.0362, 105.7906, 130),
            "Đống Đa": (21.0181, 105.8292, 140),
            "Hoàng Mai": (20.9728, 105.8632, 90),
            "Hà Đông": (20.9713, 105.7788, 85),
        }
    },
}

PROPERTY_TYPES = ["Chung cư", "Nhà phố", "Biệt thự", "Đất nền"]
LEGAL_STATUS = ["Sổ hồng", "Sổ đỏ", "Đang chờ sổ"]
OWNER_NAMES = [
    "Nguyen Van An",
    "Tran Minh Chau",
    "Le Thu Ha",
    "Pham Quoc Dat",
    "Hoang Gia Linh",
    "Vo Tuan Kiet",
]
STREET_NAMES = [
    "Nguyen Hue",
    "Vo Van Kiet",
    "Le Loi",
    "Pham Van Dong",
    "Tran Duy Hung",
    "Nguyen Trai",
]


def format_price_text(price_vnd: float) -> str:
    billions = price_vnd / 1_000_000_000
    if billions >= 1:
        whole = int(billions)
        remainder = round((billions - whole) * 10)
        return f"{whole} tỷ {remainder}" if remainder else f"{whole} tỷ"
    return f"{round(price_vnd / 1_000_000)} triệu"


def generate_address(district_name: str) -> str:
    street_no = random.randint(10, 999)
    street = random.choice(STREET_NAMES)
    return f"{street_no} {street}, {district_name}"


def generate_listing_rows(records_per_district: int = 36) -> pd.DataFrame:
    rows = []
    start_date = datetime(2024, 1, 1)

    for city_name, city_data in CITIES.items():
        for district_name, (lat, lon, base_price_sqm_million) in city_data["districts"].items():
            for index in range(records_per_district):
                property_type = random.choice(PROPERTY_TYPES)
                area_sqm = round(random.uniform(45, 220), 1)
                bedrooms = random.randint(1, 5)
                legal_status = random.choice(LEGAL_STATUS)
                posted_date = start_date + timedelta(days=30 * (index % 12) + random.randint(0, 26))
                market_factor = random.uniform(0.84, 1.18)
                type_factor = {
                    "Chung cư": 1.0,
                    "Nhà phố": 1.12,
                    "Biệt thự": 1.35,
                    "Đất nền": 0.88,
                }[property_type]
                price_per_sqm_million = base_price_sqm_million * market_factor * type_factor
                price_vnd = price_per_sqm_million * area_sqm * 1_000_000
                price_text = format_price_text(price_vnd)
                cleaned_price = clean_price(price_text)

                rows.append(
                    {
                        "city_name": city_name,
                        "district_name": district_name,
                        "property_type_name": property_type,
                        "owner_name": random.choice(OWNER_NAMES),
                        "address": generate_address(district_name),
                        "area_sqm": area_sqm,
                        "bedrooms": bedrooms,
                        "legal_status": legal_status,
                        "posted_date": posted_date.strftime("%Y-%m-%d"),
                        "price_text": price_text,
                        "price_vnd": cleaned_price,
                        "price_per_sqm": round(cleaned_price / area_sqm, 2),
                        "latitude": lat + random.uniform(-0.015, 0.015),
                        "longitude": lon + random.uniform(-0.015, 0.015),
                        "description": f"{property_type} tại {district_name}, pháp lý {legal_status}.",
                    }
                )

    return pd.DataFrame(rows)


def load_to_sqlite(df: pd.DataFrame) -> None:
    conn = get_connection()
    initialize_schema(conn)

    conn.executescript(
        """
        DELETE FROM mart_district_monthly;
        DELETE FROM fact_listings;
        DELETE FROM dim_district;
        DELETE FROM dim_city;
        DELETE FROM dim_property_type;
        """
    )

    city_ids = {}
    for city_name in sorted(df["city_name"].unique()):
        cursor = conn.execute("INSERT INTO dim_city(city_name) VALUES (?)", (city_name,))
        city_ids[city_name] = cursor.lastrowid

    type_ids = {}
    for property_type in sorted(df["property_type_name"].unique()):
        cursor = conn.execute(
            "INSERT INTO dim_property_type(property_type_name) VALUES (?)",
            (property_type,),
        )
        type_ids[property_type] = cursor.lastrowid

    district_ids = {}
    district_meta = (
        df.groupby(["city_name", "district_name"], as_index=False)[["latitude", "longitude"]]
        .mean()
        .to_dict("records")
    )
    for row in district_meta:
        cursor = conn.execute(
            """
            INSERT INTO dim_district(city_id, district_name, latitude, longitude)
            VALUES (?, ?, ?, ?)
            """,
            (
                city_ids[row["city_name"]],
                row["district_name"],
                row["latitude"],
                row["longitude"],
            ),
        )
        district_ids[(row["city_name"], row["district_name"])] = cursor.lastrowid

    fact_rows = []
    for row in df.to_dict("records"):
        fact_rows.append(
            (
                city_ids[row["city_name"]],
                district_ids[(row["city_name"], row["district_name"])],
                type_ids[row["property_type_name"]],
                row["owner_name"],
                row["address"],
                row["area_sqm"],
                row["bedrooms"],
                row["legal_status"],
                row["posted_date"],
                row["price_text"],
                row["price_vnd"],
                row["price_per_sqm"],
                row["latitude"],
                row["longitude"],
                row["description"],
            )
        )

    conn.executemany(
        """
        INSERT INTO fact_listings(
            city_id, district_id, property_type_id, owner_name, address, area_sqm,
            bedrooms, legal_status, posted_date, price_text, price_vnd, price_per_sqm,
            latitude, longitude, description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        fact_rows,
    )

    monthly = df.copy()
    monthly["month"] = pd.to_datetime(monthly["posted_date"]).dt.to_period("M").astype(str)
    mart = (
        monthly.groupby(["city_name", "district_name", "month"], as_index=False)
        .agg(avg_price_per_sqm=("price_per_sqm", "mean"), listing_count=("price_per_sqm", "size"))
    )
    mart_rows = []
    for row in mart.to_dict("records"):
        mart_rows.append(
            (
                district_ids[(row["city_name"], row["district_name"])],
                row["month"],
                round(row["avg_price_per_sqm"], 2),
                row["listing_count"],
            )
        )

    conn.executemany(
        """
        INSERT INTO mart_district_monthly(district_id, month, avg_price_per_sqm, listing_count)
        VALUES (?, ?, ?, ?)
        """,
        mart_rows,
    )
    conn.commit()
    conn.close()


def main() -> None:
    df = generate_listing_rows()
    load_to_sqlite(df)
    print(f"Loaded {len(df)} synthetic listings into SQLite.")


if __name__ == "__main__":
    main()

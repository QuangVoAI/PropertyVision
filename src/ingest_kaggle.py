from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.db import get_connection, initialize_schema
from src.etl import clean_area_sqm, clean_integer, clean_price, extract_district
from src.generate_sample import load_to_sqlite


RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
BASE_DIR = Path(__file__).resolve().parent.parent

HCMC_DISTRICT_COORDS = {
    "Quận 1": (10.7769, 106.7009),
    "Quận 2": (10.7870, 106.7498),
    "Quận 3": (10.7846, 106.6870),
    "Quận 4": (10.7592, 106.7044),
    "Quận 5": (10.7540, 106.6634),
    "Quận 7": (10.7342, 106.7218),
    "Quận 10": (10.7720, 106.6676),
    "Bình Thạnh": (10.8106, 106.7091),
    "Phú Nhuận": (10.7991, 106.6801),
    "Gò Vấp": (10.8387, 106.6658),
    "Tân Bình": (10.8033, 106.6520),
    "Thủ Đức": (10.8491, 106.7537),
    "Khác - TP.HCM": (10.8231, 106.6297),
}

HANOI_DISTRICT_COORDS = {
    "Ba Đình": (21.0338, 105.8142),
    "Cầu Giấy": (21.0362, 105.7906),
    "Đống Đa": (21.0181, 105.8292),
    "Hai Bà Trưng": (21.0058, 105.8570),
    "Hoàng Mai": (20.9728, 105.8632),
    "Hà Đông": (20.9713, 105.7788),
    "Thanh Xuân": (20.9937, 105.8099),
    "Hoàn Kiếm": (21.0285, 105.8542),
    "Long Biên": (21.0481, 105.8887),
    "Tây Hồ": (21.0707, 105.8188),
    "Nam Từ Liêm": (21.0123, 105.7658),
    "Bắc Từ Liêm": (21.0711, 105.7618),
    "Khác - Hà Nội": (21.0278, 105.8342),
}


def safe_parse_area(value) -> float | None:
    try:
        return clean_area_sqm(value)
    except Exception:
        return None


def safe_parse_price(value) -> float | None:
    try:
        return clean_price(value)
    except Exception:
        return None


def normalize_hcmc(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    column_map = {
        "Location": "address",
        "Price": "price_text",
        "Type of House": "property_type_name",
        "Land Area": "area_raw",
        "Bedrooms": "bedrooms",
        "Toilets": "toilets",
        "Total Floors": "total_floors",
        "Legal Documents": "legal_status",
    }
    df = df.rename(columns=column_map)
    missing = {"address", "price_text", "property_type_name", "area_raw"} - set(df.columns)
    if missing:
        raise ValueError(f"HCM dataset thiếu cột bắt buộc: {sorted(missing)}")

    work = pd.DataFrame(index=df.index)
    work["city_name"] = "TP.HCM"
    work["address"] = df["address"].astype(str).str.strip()
    work["district_name"] = work["address"].map(lambda x: extract_district(x, "TP.HCM"))
    work["property_type_name"] = df["property_type_name"].fillna("Khác").astype(str).str.strip()
    work["owner_name"] = "Kaggle HCM Source"
    work["area_sqm"] = df["area_raw"].map(safe_parse_area)
    work["bedrooms"] = df["bedrooms"].map(clean_integer)
    work["legal_status"] = df.get("legal_status", pd.Series(["Không rõ"] * len(df))).fillna("Không rõ")
    work["posted_date"] = "2025-01-01"
    work["price_text"] = df["price_text"].astype(str).str.strip()
    work["price_vnd"] = work["price_text"].map(safe_parse_price)
    work = work.dropna(subset=["area_sqm", "price_vnd"])
    work = work[work["area_sqm"] > 0]
    work["price_per_sqm"] = work["price_vnd"] / work["area_sqm"]
    work["description"] = (
        work["property_type_name"] + " | " + work["district_name"] + " | " + work["legal_status"].astype(str)
    )

    coords = work["district_name"].map(lambda name: HCMC_DISTRICT_COORDS.get(name, (10.8231, 106.6297)))
    work["latitude"] = coords.map(lambda x: x[0])
    work["longitude"] = coords.map(lambda x: x[1])
    return work


def normalize_hanoi(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    column_map = {
        "Ngày": "posted_date",
        "Địa chỉ": "address",
        "Quận": "district",
        "Huyện": "ward",
        "Loại hình nhà ở": "property_type_name",
        "Giấy tờ pháp lý": "legal_status",
        "Số tầng": "total_floors",
        "Số phòng ngủ": "bedrooms",
        "Diện tích": "area_raw",
        "Giá/m2": "price_per_sqm_text",
    }
    df = df.rename(columns=column_map)
    required = {"address", "property_type_name", "area_raw", "price_per_sqm_text"} - set(df.columns)
    if required:
        raise ValueError(f"Hanoi dataset thiếu cột bắt buộc: {sorted(required)}")

    work = pd.DataFrame(index=df.index)
    work["city_name"] = "Hà Nội"
    work["address"] = df["address"].astype(str).str.strip()
    if "district" in df.columns:
        work["district_name"] = (
            df["district"]
            .fillna("")
            .astype(str)
            .str.replace("^Quận\\s+", "", regex=True)
            .str.strip()
        )
        work["district_name"] = work["district_name"].where(work["district_name"] != "", work["address"].map(lambda x: extract_district(x, "Hà Nội")))
    else:
        work["district_name"] = work["address"].map(lambda x: extract_district(x, "Hà Nội"))
    work["owner_name"] = "Kaggle Hanoi Source"
    work["property_type_name"] = df["property_type_name"].fillna("Khác").astype(str).str.strip()
    work["area_sqm"] = df["area_raw"].map(safe_parse_area)
    work["bedrooms"] = df["bedrooms"].map(clean_integer) if "bedrooms" in df.columns else 0
    work["legal_status"] = df["legal_status"].fillna("Không rõ").astype(str).str.strip() if "legal_status" in df.columns else "Không rõ"
    work["posted_date"] = (
        pd.to_datetime(df["posted_date"], errors="coerce").fillna(pd.Timestamp("2025-01-01")).dt.strftime("%Y-%m-%d")
        if "posted_date" in df.columns
        else "2025-01-01"
    )
    work["price_text"] = df["price_per_sqm_text"].astype(str).str.strip()
    price_per_sqm_vnd = work["price_text"].map(safe_parse_price)
    work["price_vnd"] = price_per_sqm_vnd * work["area_sqm"]
    work = work.dropna(subset=["area_sqm", "price_vnd"])
    work = work[work["area_sqm"] > 0]
    work["price_per_sqm"] = work["price_vnd"] / work["area_sqm"]
    work["description"] = (
        work["property_type_name"].astype(str) + " | " + work["district_name"] + " | " + work["legal_status"].astype(str)
    )

    coords = work["district_name"].map(lambda name: HANOI_DISTRICT_COORDS.get(name, (21.0278, 105.8342)))
    work["latitude"] = coords.map(lambda x: x[0])
    work["longitude"] = coords.map(lambda x: x[1])
    return work


def import_kaggle_datasets(hcmc_csv: Path, hanoi_csv: Path) -> pd.DataFrame:
    hcm_df = normalize_hcmc(hcmc_csv)
    hanoi_df = normalize_hanoi(hanoi_csv)
    combined = pd.concat([hcm_df, hanoi_df], ignore_index=True)
    combined = combined.dropna(subset=["price_vnd", "area_sqm"])
    combined = combined[combined["area_sqm"] > 0]
    combined["price_per_sqm"] = combined["price_vnd"] / combined["area_sqm"]
    combined["address"] = combined["address"].fillna(combined["district_name"]).astype(str).str.strip()
    combined = combined[combined["address"] != ""]
    combined = combined[combined["price_per_sqm"] >= 1_000_000]
    return combined


def main() -> None:
    candidate_hcmc = [
        BASE_DIR / "real_estate_listings.csv",
        RAW_DIR / "real_estate_listings.csv",
        RAW_DIR / "vietnam_housing_hcm.csv",
    ]
    candidate_hanoi = [
        BASE_DIR / "VN_housing_dataset.csv",
        RAW_DIR / "VN_housing_dataset.csv",
    ]
    hcmc_csv = next((path for path in candidate_hcmc if path.exists()), None)
    hanoi_csv = next((path for path in candidate_hanoi if path.exists()), None)
    if hcmc_csv is None or hanoi_csv is None:
        raise FileNotFoundError(
            "Thiếu file CSV. Hãy đặt file HCM/Hà Nội vào root repo hoặc `data/raw/`."
        )

    df = import_kaggle_datasets(hcmc_csv, hanoi_csv)
    conn = get_connection()
    initialize_schema(conn)
    conn.close()
    load_to_sqlite(df)
    print(f"Imported {len(df)} listings from Kaggle CSV files.")


if __name__ == "__main__":
    main()

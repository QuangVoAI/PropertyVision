from __future__ import annotations

import asyncio
import hashlib
import math
import re
import sqlite3
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download
from pydantic import BaseModel, Field
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT_DIR / "datasets"
MERGED_DATA_PATH = DATASETS_DIR / "clean_dataset.csv"
DATA_PATH = DATASETS_DIR / "raw" / "clean_data.csv"
HANOI_DATA_PATH = DATASETS_DIR / "raw" / "clean_hanoi.csv"
DB_PATH = ROOT_DIR / "data" / "propertyvision.db"
HF_DATASET_REPO = "SpringWang08/hanoi-hcmc-real-estate"
HF_DATASET_FILENAME = "clean_dataset.csv"
VND_BILLION = 1_000_000_000
VND_MILLION = 1_000_000
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODELS = ["qwen2.5:14b", "llama3.1:latest", "llama3:latest"]
DEFAULT_CITY = "TP Hồ Chí Minh"
CITY_LABELS = ["TP Hồ Chí Minh", "Hà Nội"]
LAND_TYPES = {"Đất thổ cư", "Đất dự án, Khu dân cư", "Đất nông nghiệp, kho bãi"}
CITY_CENTERS = {
    "TP Hồ Chí Minh": {"latitude": 10.7769, "longitude": 106.7009, "zoom": 10},
    "Hà Nội": {"latitude": 21.0285, "longitude": 105.8542, "zoom": 11},
}
FALLBACK_DISTRICT_COORDS = {
    "quận 1": {"latitude": 10.7756, "longitude": 106.7009},
    "quận 3": {"latitude": 10.7829, "longitude": 106.6864},
    "quận 4": {"latitude": 10.7579, "longitude": 106.7043},
    "quận 5": {"latitude": 10.7540, "longitude": 106.6638},
    "quận 6": {"latitude": 10.7460, "longitude": 106.6353},
    "quận 7": {"latitude": 10.7342, "longitude": 106.7218},
    "quận 8": {"latitude": 10.7243, "longitude": 106.6285},
    "quận 10": {"latitude": 10.7722, "longitude": 106.6679},
    "quận 11": {"latitude": 10.7631, "longitude": 106.6438},
    "quận 12": {"latitude": 10.8678, "longitude": 106.6416},
    "quận bình thạnh": {"latitude": 10.8106, "longitude": 106.7091},
    "quận bình tân": {"latitude": 10.7659, "longitude": 106.6030},
    "quận gò vấp": {"latitude": 10.8387, "longitude": 106.6653},
    "quận phú nhuận": {"latitude": 10.7991, "longitude": 106.6800},
    "quận tân bình": {"latitude": 10.8016, "longitude": 106.6520},
    "quận tân phú": {"latitude": 10.7915, "longitude": 106.6279},
    "huyện bình chánh": {"latitude": 10.6906, "longitude": 106.5955},
    "huyện củ chi": {"latitude": 11.0047, "longitude": 106.5004},
    "huyện hóc môn": {"latitude": 10.8894, "longitude": 106.5923},
    "huyện nhà bè": {"latitude": 10.6953, "longitude": 106.7353},
    "quận 2": {"latitude": 10.7873, "longitude": 106.7498},
    "quận 9": {"latitude": 10.8428, "longitude": 106.8287},
    "quận thủ đức": {"latitude": 10.8506, "longitude": 106.7550},
    "cầu giấy": {"latitude": 21.0363, "longitude": 105.7906},
    "ba đình": {"latitude": 21.0358, "longitude": 105.8142},
    "bắc từ liêm": {"latitude": 21.0714, "longitude": 105.7706},
    "thanh xuân": {"latitude": 20.9931, "longitude": 105.8048},
    "hai bà trưng": {"latitude": 21.0059, "longitude": 105.8575},
    "hoàn kiếm": {"latitude": 21.0281, "longitude": 105.8544},
    "hoàng mai": {"latitude": 20.9740, "longitude": 105.8632},
    "hà đông": {"latitude": 20.9714, "longitude": 105.7788},
    "long biên": {"latitude": 21.0549, "longitude": 105.8885},
    "nam từ liêm": {"latitude": 21.0123, "longitude": 105.7658},
    "tây hồ": {"latitude": 21.0702, "longitude": 105.8188},
    "đống đa": {"latitude": 21.0181, "longitude": 105.8295},
    "thị xã sơn tây": {"latitude": 21.1405, "longitude": 105.5060},
    "huyện ba vì": {"latitude": 21.1996, "longitude": 105.4234},
    "huyện chương mỹ": {"latitude": 20.8860, "longitude": 105.6544},
    "huyện gia lâm": {"latitude": 21.0288, "longitude": 105.9500},
    "huyện hoài đức": {"latitude": 21.0336, "longitude": 105.7055},
    "huyện mê linh": {"latitude": 21.1804, "longitude": 105.7077},
    "huyện mỹ đức": {"latitude": 20.7458, "longitude": 105.7232},
    "huyện phú xuyên": {"latitude": 20.7292, "longitude": 105.9088},
    "huyện phúc thọ": {"latitude": 21.1174, "longitude": 105.5937},
    "huyện quốc oai": {"latitude": 20.9950, "longitude": 105.6423},
    "huyện sóc sơn": {"latitude": 21.2592, "longitude": 105.8486},
    "huyện thanh oai": {"latitude": 20.8575, "longitude": 105.7698},
    "huyện thanh trì": {"latitude": 20.9369, "longitude": 105.8418},
    "huyện thường tín": {"latitude": 20.8416, "longitude": 105.8613},
    "huyện thạch thất": {"latitude": 21.0471, "longitude": 105.5617},
    "huyện đan phượng": {"latitude": 21.1054, "longitude": 105.6710},
    "huyện đông anh": {"latitude": 21.1368, "longitude": 105.8460},
}

PUBLIC_SOURCES = [
    {
        "name": "HCMGIS Portal",
        "type": "GIS / planning",
        "url": "https://portal.hcmgis.vn/",
        "status": "public-source",
    },
    {
        "name": "HCMGIS GeoNode registry",
        "type": "GIS metadata",
        "url": "https://dateno.io/registry/catalog/cdi00001949/",
        "status": "public-source",
    },
    {
        "name": "HCMC online land data platform",
        "type": "land / planning news source",
        "url": "https://vietnam.opendevelopmentmekong.net/news/hcmc-launches-online-land-data-platform/",
        "status": "public-source",
    },
    {
        "name": "Cổng tra cứu quy hoạch TP.HCM",
        "type": "planning lookup",
        "url": "https://thongtinquyhoach.hochiminhcity.gov.vn",
        "status": "public-source",
    },
    {
        "name": "Kaggle HCMC Real Estate Data 2025",
        "type": "market listing / transaction proxy",
        "url": "https://www.kaggle.com/datasets/cnglmph/ho-chi-minh-city-real-estate-data-2025",
        "status": "cached-local-proxy",
    },
    {
        "name": "Kaggle House Pricing HCM",
        "type": "time-series market proxy",
        "url": "https://www.kaggle.com/datasets/trnduythanhkhttt/housepricinghcm/data",
        "status": "cached-local-proxy",
    },
]

app = FastAPI(title="PropertyVision BI API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Filters(BaseModel):
    city: str | None = DEFAULT_CITY
    districts: list[str] = Field(default_factory=list)
    property_types: list[str] = Field(default_factory=list)
    price_min: float | None = None
    price_max: float | None = None
    area_min: float | None = None
    area_max: float | None = None
    roi_min: float | None = None
    roi_max: float | None = None


class PredictionRequest(BaseModel):
    district: str
    property_type: str
    legal_documents: str
    area: float = Field(gt=0)
    bedrooms: float | None = None
    toilets: float | None = None
    floors: float | None = None
    roi_expected: float = Field(default=0.14, ge=0, le=1)


class WhatIfRequest(PredictionRequest):
    budget_vnd: float = Field(gt=0)
    annual_growth_pct: float = Field(default=8.0, ge=-20, le=50)
    years: int = Field(default=5, ge=1, le=15)


class AssistantRequest(BaseModel):
    question: str
    filters: Filters = Field(default_factory=Filters)
    top_k: int = Field(default=5, ge=1, le=10)


class SliceDiceRequest(BaseModel):
    filters: Filters = Field(default_factory=Filters)
    row_dimension: str = "district"
    column_dimension: str = "Type of House"
    metric: str = "avg_roi"


class FutureRecommendationRequest(WhatIfRequest):
    filters: Filters = Field(default_factory=Filters)
    top_k: int = Field(default=5, ge=1, le=10)


def parse_number(value: object) -> float:
    if pd.isna(value):
        return np.nan
    match = re.search(r"\d+(?:[,.]\d+)?", str(value))
    if not match:
        return np.nan
    return float(match.group(0).replace(",", "."))


def clean_value(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if pd.isna(value):
        return None
    return value


def clamp_int(value: float, lower: int, upper: int) -> int:
    return int(max(lower, min(upper, round(value))))


def records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [{key: clean_value(value) for key, value in row.items()} for row in df.to_dict(orient="records")]


def filters_summary(filters: Filters) -> str:
    parts: list[str] = []
    if filters.city:
        parts.append(filters.city)
    if filters.districts:
        parts.append(f"{len(filters.districts)} khu vực")
    if filters.property_types:
        parts.append(f"{len(filters.property_types)} loại tài sản")
    if filters.price_max is not None:
        parts.append(f"gia <= {filters.price_max:.1f} ty")
    if filters.roi_min is not None:
        parts.append(f"ROI >= {filters.roi_min:.1f}%")
    return ", ".join(parts) if parts else "toan thi truong"


@lru_cache(maxsize=1)
def district_city_lookup() -> dict[str, str]:
    df = load_data()
    rows = (
        df[["district", "city"]]
        .dropna()
        .drop_duplicates()
        .itertuples(index=False)
    )
    return {str(row.district): str(row.city) for row in rows}


def infer_document_city(title: str | None, source_name: str | None, source_url: str | None) -> str | None:
    haystack = " ".join([str(title or ""), str(source_name or ""), str(source_url or "")]).lower()
    if any(token in haystack for token in ["hcm", "hochiminh", "ho chi minh", "tp.hcm"]):
        return "TP Hồ Chí Minh"
    if any(token in haystack for token in ["ha noi", "hanoi", "hà nội"]):
        return "Hà Nội"
    return None


def district_key(name: str) -> str:
    value = str(name).strip()
    for prefix in ["TP. Thủ Đức - ", "Quận ", "Huyện ", "Thành phố ", "TP. "]:
        value = value.replace(prefix, "")
    return value.strip().lower()


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def infer_residential_floors(area: float, property_type: str, price_per_m2: float) -> int:
    if property_type in LAND_TYPES:
        return 0
    if property_type == "Biệt thự, Villa":
        return 3 if area >= 160 else 2 if area >= 90 else 1
    if property_type == "Nhà mặt tiền":
        if area < 30:
            return 4
        return 5 if price_per_m2 >= 180 * VND_MILLION and area >= 40 else 4 if area >= 45 else 3
    return 4 if area >= 45 else 3 if area >= 25 else 2


def infer_residential_bedrooms(area: float, property_type: str, floors: int) -> int:
    if property_type in LAND_TYPES:
        return 0
    if property_type == "Biệt thự, Villa":
        return clamp_int((floors + 1) + area / 70, 3, 8)
    if property_type == "Nhà mặt tiền":
        return clamp_int((floors - 1) + area / 55, 2, 8)
    return clamp_int((floors - 1) + area / 45, 1, 7)


def bedroom_bounds(area: float, property_type: str, floors: int) -> tuple[int, int, int]:
    if property_type in LAND_TYPES:
        return 0, 0, 0

    target = infer_residential_bedrooms(area, property_type, floors)
    lower = max(1, target - 1)
    upper = target + 1

    if area < 35:
        upper = min(upper, 4 if property_type == "Nhà mặt tiền" else 3)
    if floors <= 2:
        upper = min(upper, 6 if property_type == "Biệt thự, Villa" else 5)

    return lower, max(lower, upper), target


def infer_residential_toilets(area: float, property_type: str, bedrooms: int, floors: int) -> int:
    if property_type in LAND_TYPES:
        return 0
    if property_type == "Biệt thự, Villa":
        return clamp_int(max(math.ceil(bedrooms * 0.7), floors + 1, 2 + area / 90), 2, 7)
    return clamp_int(
        max(math.ceil(bedrooms / 2), floors - 2 + (1 if area >= 40 else 0) + (1 if area >= 120 else 0)),
        1,
        6,
    )


def toilet_bounds(area: float, property_type: str, bedrooms: int, floors: int) -> tuple[int, int, int]:
    if property_type in LAND_TYPES:
        return 0, 0, 0

    target = infer_residential_toilets(area, property_type, bedrooms, floors)
    lower = max(1, target - 1)
    upper = target + 1

    if bedrooms >= 6 or floors >= 5:
        lower = max(lower, 3)
    elif bedrooms >= 3 or floors >= 3:
        lower = max(lower, 2)

    if area < 35:
        upper = min(upper, 4 if property_type == "Nhà mặt tiền" else 3)

    upper = min(upper, bedrooms if property_type == "Biệt thự, Villa" else bedrooms + 1)
    upper = min(upper, 7 if property_type == "Biệt thự, Villa" else 6)

    return lower, max(lower, upper), target


def normalize_dataset_dates(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    synthetic_span = result["date"].max() - result["date"].min()
    if pd.notna(synthetic_span) and synthetic_span.days > 3650:
        month_offsets = np.arange(len(result)) % 48
        result["date"] = pd.to_datetime("2022-01-01") + pd.to_timedelta(month_offsets * 30, unit="D")
    return result


def normalize_property_types(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    area = pd.to_numeric(result.get("area"), errors="coerce").fillna(0)
    price_per_m2 = pd.to_numeric(result.get("price_per_m2"), errors="coerce").fillna(0)
    city = result.get("city", "").astype(str)

    oversized_residential = (
        city.eq("Hà Nội")
        & result["Type of House"].eq("Biệt thự, Villa")
        & area.ge(1000)
    )

    result.loc[oversized_residential & price_per_m2.ge(30 * VND_MILLION), "Type of House"] = "Đất thổ cư"
    result.loc[oversized_residential & price_per_m2.lt(30 * VND_MILLION), "Type of House"] = "Đất dự án, Khu dân cư"
    return result


def sanitize_property_fields(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["bedrooms_num"] = result["Bedrooms"].map(parse_number)
    result["toilets_num"] = result["Toilets"].map(parse_number)
    result["floor_num"] = pd.to_numeric(result["Total Floors"], errors="coerce")

    for index, row in result.iterrows():
        property_type = str(row.get("Type of House") or "").strip()
        area = float(row.get("area") or 0)
        price_per_m2 = float(row.get("price_per_m2") or 0)

        if property_type in LAND_TYPES:
            result.at[index, "Bedrooms"] = "0 phòng"
            result.at[index, "Toilets"] = "0 WC"
            result.at[index, "Total Floors"] = 0
            result.at[index, "bedrooms_num"] = 0
            result.at[index, "toilets_num"] = 0
            result.at[index, "floor_num"] = 0
            continue

        floors = row["floor_num"]
        if pd.isna(floors) or floors < 1:
            floors = infer_residential_floors(area, property_type, price_per_m2)
        else:
            floors = clamp_int(floors, 1, 7)

        bedrooms = row["bedrooms_num"]
        bedroom_lower, bedroom_upper, inferred_bedrooms = bedroom_bounds(area, property_type, int(floors))
        if pd.isna(bedrooms) or bedrooms < 1:
            bedrooms = inferred_bedrooms
        else:
            bedrooms = clamp_int(bedrooms, bedroom_lower, bedroom_upper)

        toilets = row["toilets_num"]
        toilet_lower, toilet_upper, inferred_toilets = toilet_bounds(area, property_type, int(bedrooms), int(floors))
        if pd.isna(toilets) or toilets < 1:
            toilets = inferred_toilets
        else:
            toilets = clamp_int(toilets, toilet_lower, toilet_upper)

        result.at[index, "Bedrooms"] = f"{int(bedrooms)} phòng"
        result.at[index, "Toilets"] = f"{int(toilets)} WC"
        result.at[index, "Total Floors"] = int(floors)
        result.at[index, "bedrooms_num"] = int(bedrooms)
        result.at[index, "toilets_num"] = int(toilets)
        result.at[index, "floor_num"] = int(floors)

    return result


def resolve_dataset_path() -> Path:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        downloaded_path = hf_hub_download(
            repo_id=HF_DATASET_REPO,
            filename=HF_DATASET_FILENAME,
            repo_type="dataset",
            local_dir=DATASETS_DIR,
        )
        return Path(downloaded_path)
    except Exception:
        if MERGED_DATA_PATH.exists():
            return MERGED_DATA_PATH
        raise


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(resolve_dataset_path(), low_memory=False)
    except Exception:
        base_df = pd.read_csv(DATA_PATH, low_memory=False)
        base_df["city"] = DEFAULT_CITY

        hanoi_df = pd.read_csv(HANOI_DATA_PATH, low_memory=False) if HANOI_DATA_PATH.exists() else pd.DataFrame()
        if not hanoi_df.empty:
            hanoi_df["city"] = "Hà Nội"
            hanoi_df["Location"] = hanoi_df["district"]
            hanoi_df["Price"] = hanoi_df["price_vnd"].map(lambda value: f"{value / VND_BILLION:.2f} tỷ")
            hanoi_df["Type of House"] = "Nhà phố"
            hanoi_df["Land Area"] = hanoi_df["area"].map(lambda value: f"{value:.1f} m²")
            hanoi_df["Bedrooms"] = np.nan
            hanoi_df["Toilets"] = np.nan
            hanoi_df["Total Floors"] = np.nan
            hanoi_df["Main Door Direction"] = ""
            hanoi_df["Balcony Direction"] = ""
            hanoi_df["Legal Documents"] = "Chưa rõ"
            hanoi_df["purchase_price"] = hanoi_df["price_vnd"] / (1 + hanoi_df["ROI"].clip(lower=0.01))
            hanoi_df["current_price"] = hanoi_df["price_vnd"]
            hanoi_df["date"] = pd.to_datetime("2024-01-01") + pd.to_timedelta(np.arange(len(hanoi_df)) * 7, unit="D")
            for column in base_df.columns:
                if column not in hanoi_df.columns:
                    hanoi_df[column] = np.nan
            hanoi_df = hanoi_df[base_df.columns.tolist() + ["city"]]

        df = pd.concat([base_df, hanoi_df], ignore_index=True, sort=False)
    df = normalize_dataset_dates(df)
    df = normalize_property_types(df)
    df = sanitize_property_fields(df)
    df["price_billion"] = df["price_vnd"] / VND_BILLION
    df["price_per_m2_million"] = df["price_per_m2"] / VND_MILLION
    df["roi_pct"] = df["ROI"] * 100
    district_profile = df.groupby("district").agg(
        district_price_m2=("price_per_m2", "mean"),
        district_liquidity=("Location", "count"),
    )
    price_rank = district_profile["district_price_m2"].rank(pct=True)
    liquidity_rank = district_profile["district_liquidity"].rank(pct=True)
    roi_adjustment = ((1 - price_rank) * 0.035 + liquidity_rank * 0.025 - 0.03).to_dict()
    df["business_roi"] = (df["ROI"] + df["district"].map(roi_adjustment).fillna(0)).clip(lower=0.035, upper=0.32)
    df["business_roi_pct"] = df["business_roi"] * 100
    df["ward"] = df["Location"].str.split(",").str[0].str.strip()
    df["city"] = df["city"].fillna(DEFAULT_CITY)
    return df


def ensure_operational_tables() -> None:
    with connect_db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS fact_transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL UNIQUE,
                transaction_date TEXT NOT NULL,
                district TEXT NOT NULL,
                property_type TEXT NOT NULL,
                price_vnd REAL NOT NULL,
                area_sqm REAL NOT NULL,
                price_per_sqm REAL NOT NULL,
                legal_status TEXT,
                roi REAL,
                source_name TEXT NOT NULL,
                source_url TEXT,
                confidence_score REAL NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dim_district (
                district_id INTEGER PRIMARY KEY AUTOINCREMENT,
                district_name TEXT NOT NULL UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dim_planning_zone (
                zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                district TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                zone_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                description TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS legal_documents (
                document_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                document_type TEXT NOT NULL,
                district TEXT,
                content TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS etl_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                records_seen INTEGER NOT NULL,
                records_inserted INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                message TEXT NOT NULL
            );
            """
        )


def seed_district_coordinates() -> None:
    ensure_operational_tables()
    district_rows = load_data()["district"].dropna().drop_duplicates().tolist()
    with connect_db() as con:
        for district in district_rows:
            coord = FALLBACK_DISTRICT_COORDS.get(district_key(str(district)))
            if not coord:
                continue
            con.execute(
                """
                INSERT OR IGNORE INTO dim_district (district_name, latitude, longitude)
                VALUES (?, ?, ?)
                """,
                (str(district), coord["latitude"], coord["longitude"]),
            )


def district_coordinates() -> dict[str, dict[str, float]]:
    seed_district_coordinates()
    coords: dict[str, dict[str, float]] = {}
    with connect_db() as con:
        rows = con.execute("SELECT district_name, latitude, longitude FROM dim_district").fetchall()
    for row in rows:
        coords[district_key(row["district_name"])] = {
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
        }
    coords.update({key: value for key, value in FALLBACK_DISTRICT_COORDS.items() if key not in coords})
    return coords


def risk_level_from_roi(roi: float) -> str:
    if roi >= 0.17:
        return "low"
    if roi >= 0.11:
        return "medium"
    return "high"


def planning_description(district: str, avg_roi: float, avg_price_m2: float) -> tuple[str, str]:
    if avg_price_m2 > 150 * VND_MILLION:
        return (
            "Khu vực lõi đô thị, cần kiểm tra chỉ tiêu quy hoạch, hệ số sử dụng đất, lộ giới và pháp lý từng tài sản.",
            "medium",
        )
    if avg_roi >= 0.17:
        return (
            "Khu vực có tín hiệu lợi suất tốt; ưu tiên xác minh quy hoạch hạ tầng, pháp lý sổ và khả năng chuyển nhượng.",
            "low",
        )
    return (
        "Khu vực cần kiểm soát kỹ thanh khoản và tính pháp lý trước khi giải ngân.",
        "medium",
    )


def seed_planning_and_documents() -> dict[str, int]:
    ensure_operational_tables()
    df = load_data()
    score_df = district_score(df)
    coords = district_coordinates()
    now = pd.Timestamp.utcnow().isoformat()
    zones_inserted = 0
    docs_inserted = 0

    with connect_db() as con:
        for row in score_df.itertuples(index=False):
            coord = coords.get(district_key(row.district))
            if not coord:
                continue
            existing_zone = con.execute(
                "SELECT 1 FROM dim_planning_zone WHERE district = ? LIMIT 1",
                (row.district,),
            ).fetchone()
            description, risk = planning_description(row.district, row.avg_roi, row.avg_price_m2)
            if not existing_zone:
                con.execute(
                    """
                    INSERT INTO dim_planning_zone (
                        district, latitude, longitude, zone_type, risk_level, description,
                        source_name, source_url, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row.district,
                        coord["latitude"],
                        coord["longitude"],
                        "planning-risk-screening",
                        risk,
                        description,
                        "HCMGIS / planning public source cache",
                        "https://portal.hcmgis.vn/",
                        now,
                    ),
                )
                zones_inserted += 1

            existing_doc = con.execute(
                "SELECT 1 FROM legal_documents WHERE title = ? LIMIT 1",
                (f"Hồ sơ pháp lý và quy hoạch sơ bộ - {row.district}",),
            ).fetchone()
            if not existing_doc:
                con.execute(
                    """
                    INSERT INTO legal_documents (
                        title, document_type, district, content, source_name, source_url, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"Hồ sơ pháp lý và quy hoạch sơ bộ - {row.district}",
                        "planning-legal-brief",
                        row.district,
                        (
                            f"{row.district} có ROI trung bình {row.roi_pct:.2f}%, giá/m2 "
                            f"{row.price_m2_million:.1f} triệu và điểm cơ hội {row.opportunity_score:.1f}/100. "
                            f"{description} Nguồn tham chiếu: HCMGIS, cổng tra cứu quy hoạch TP.HCM, "
                            "và dữ liệu thị trường công khai được cache cho demo."
                        ),
                        "PropertyVision public planning cache",
                        "https://thongtinquyhoach.hochiminhcity.gov.vn",
                        now,
                    ),
                )
                docs_inserted += 1

        general_docs = [
            (
                "Cổng HCMGIS và dữ liệu không gian TP.HCM",
                "public-source",
                None,
                "HCMGIS cung cấp nền tảng bản đồ và lớp dữ liệu GIS để tham chiếu vị trí, quy hoạch và bối cảnh không gian đô thị.",
                "HCMGIS Portal",
                "https://portal.hcmgis.vn/",
            ),
            (
                "Nguồn dữ liệu listing và transaction proxy",
                "market-source",
                None,
                "PropertyVision dùng dữ liệu listing công khai và time-series giá làm proxy giao dịch khi dữ liệu giao dịch chính thức chưa mở API ổn định.",
                "Kaggle public datasets",
                "https://www.kaggle.com/datasets/cnglmph/ho-chi-minh-city-real-estate-data-2025",
            ),
            (
                "Data Coverage & Governance",
                "governance",
                None,
                "Hệ thống ghi nguồn, thời gian cập nhật, độ tin cậy và cache snapshot để demo ổn định, đồng thời sẵn sàng thay bằng nguồn chính thức của doanh nghiệp.",
                "PropertyVision governance note",
                "https://vietnam.opendevelopmentmekong.net/news/hcmc-launches-online-land-data-platform/",
            ),
        ]
        for title, doc_type, district, content, source_name, source_url in general_docs:
            existing = con.execute("SELECT 1 FROM legal_documents WHERE title = ? LIMIT 1", (title,)).fetchone()
            if not existing:
                con.execute(
                    """
                    INSERT INTO legal_documents (
                        title, document_type, district, content, source_name, source_url, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, doc_type, district, content, source_name, source_url, now),
                )
                docs_inserted += 1

    clear_rag_cache()
    return {"zones_inserted": zones_inserted, "documents_inserted": docs_inserted}


def run_etl(mode: str = "manual") -> dict[str, Any]:
    ensure_operational_tables()
    started = pd.Timestamp.utcnow().isoformat()
    df = load_data()
    now = pd.Timestamp.utcnow().isoformat()
    source_url = "https://www.kaggle.com/datasets/cnglmph/ho-chi-minh-city-real-estate-data-2025"
    inserted = 0
    seed_counts = seed_planning_and_documents()

    with connect_db() as con:
        for idx, row in df.iterrows():
            source_raw = f"{idx}|{row['Location']}|{row['date']}|{row['price_vnd']}|{row['area']}"
            source_id = "listing-proxy:" + hashlib.sha1(source_raw.encode("utf-8")).hexdigest()
            cursor = con.execute(
                """
                INSERT OR IGNORE INTO fact_transactions (
                    source_id, transaction_date, district, property_type, price_vnd, area_sqm,
                    price_per_sqm, legal_status, roi, source_name, source_url,
                    confidence_score, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else now[:10],
                    row["district"],
                    row["Type of House"],
                    float(row["price_vnd"]),
                    float(row["area"]),
                    float(row["price_per_m2"]),
                    row["Legal Documents"],
                    float(row["ROI"]),
                    "Kaggle/listing public transaction proxy",
                    source_url,
                    0.74,
                    now,
                ),
            )
            inserted += cursor.rowcount

        finished = pd.Timestamp.utcnow().isoformat()
        con.execute(
            """
            INSERT INTO etl_runs (
                source_name, mode, status, records_seen, records_inserted,
                started_at, finished_at, message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Public Data Hub",
                mode,
                "success",
                int(len(df)),
                int(inserted),
                started,
                finished,
                (
                    f"Incremental ingest complete. Transactions inserted: {inserted}. "
                    f"Planning zones inserted: {seed_counts['zones_inserted']}. "
                    f"Legal documents inserted: {seed_counts['documents_inserted']}."
                ),
            ),
        )

    return {
        "status": "success",
        "mode": mode,
        "records_seen": int(len(df)),
        "records_inserted": int(inserted),
        "started_at": started,
        "finished_at": pd.Timestamp.utcnow().isoformat(),
        "message": "Public Data Hub refreshed with cached public-market, GIS, planning and legal sources.",
    }


def etl_status() -> dict[str, Any]:
    ensure_operational_tables()
    with connect_db() as con:
        tx_count = con.execute("SELECT COUNT(*) FROM fact_transactions").fetchone()[0]
        zone_count = con.execute("SELECT COUNT(*) FROM dim_planning_zone").fetchone()[0]
        doc_count = con.execute("SELECT COUNT(*) FROM legal_documents").fetchone()[0]
        runs = con.execute(
            """
            SELECT * FROM etl_runs
            ORDER BY run_id DESC
            LIMIT 12
            """
        ).fetchall()
    return {
        "status": "online",
        "scheduler": "enabled",
        "refresh_interval_seconds": 300,
        "transaction_records": int(tx_count),
        "planning_zones": int(zone_count),
        "legal_documents": int(doc_count),
        "sources": PUBLIC_SOURCES,
        "runs": [dict(row) for row in runs],
    }


async def scheduled_etl_loop() -> None:
    await asyncio.sleep(2)
    while True:
        try:
            run_etl(mode="scheduled")
        except Exception:
            pass
        await asyncio.sleep(300)


@app.on_event("startup")
async def startup_event() -> None:
    ensure_operational_tables()
    seed_planning_and_documents()
    status = etl_status()
    if status["transaction_records"] == 0:
        run_etl(mode="startup")
    asyncio.create_task(scheduled_etl_loop())


def apply_filters(df: pd.DataFrame, filters: Filters) -> pd.DataFrame:
    result = df.copy()
    if filters.city:
        result = result[result["city"] == filters.city]
    if filters.districts:
        result = result[result["district"].isin(filters.districts)]
    if filters.property_types:
        result = result[result["Type of House"].isin(filters.property_types)]
    if filters.price_min is not None:
        result = result[result["price_billion"] >= filters.price_min]
    if filters.price_max is not None:
        result = result[result["price_billion"] <= filters.price_max]
    if filters.area_min is not None:
        result = result[result["area"] >= filters.area_min]
    if filters.area_max is not None:
        result = result[result["area"] <= filters.area_max]
    if filters.roi_min is not None:
        roi_filter_col = "business_roi_pct" if "business_roi_pct" in result.columns else "roi_pct"
        result = result[result[roi_filter_col] >= filters.roi_min]
    if filters.roi_max is not None:
        roi_filter_col = "business_roi_pct" if "business_roi_pct" in result.columns else "roi_pct"
        result = result[result[roi_filter_col] <= filters.roi_max]
    return result


def normalize(series: pd.Series, inverse: bool = False) -> pd.Series:
    values = series.astype(float)
    min_value = values.min()
    max_value = values.max()
    if np.isclose(max_value, min_value):
        output = pd.Series(0.5, index=values.index)
    else:
        output = (values - min_value) / (max_value - min_value)
    return 1 - output if inverse else output


def district_score(df: pd.DataFrame) -> pd.DataFrame:
    roi_column = "business_roi" if "business_roi" in df.columns else "ROI"
    grouped = (
        df.groupby("district")
        .agg(
            listings=("Location", "count"),
            avg_price=("price_vnd", "mean"),
            median_price=("price_vnd", "median"),
            avg_price_m2=("price_per_m2", "mean"),
            avg_roi=(roi_column, "mean"),
            volatility=(roi_column, "std"),
            avg_area=("area", "mean"),
        )
        .reset_index()
    )
    grouped["volatility"] = grouped["volatility"].fillna(0)
    grouped["opportunity_score"] = (
        normalize(grouped["avg_roi"]) * 0.42
        + normalize(grouped["listings"]) * 0.18
        + normalize(grouped["avg_price_m2"], inverse=True) * 0.22
        + normalize(grouped["volatility"], inverse=True) * 0.18
    ) * 100
    grouped["roi_pct"] = grouped["avg_roi"] * 100
    grouped["price_m2_million"] = grouped["avg_price_m2"] / VND_MILLION
    return grouped.sort_values("opportunity_score", ascending=False)


def type_score(df: pd.DataFrame) -> pd.DataFrame:
    roi_column = "business_roi" if "business_roi" in df.columns else "ROI"
    return (
        df.groupby("Type of House")
        .agg(
            listings=("Location", "count"),
            avg_price=("price_vnd", "mean"),
            median_price=("price_vnd", "median"),
            avg_roi=(roi_column, "mean"),
            avg_price_m2=("price_per_m2", "mean"),
            avg_area=("area", "mean"),
        )
        .reset_index()
        .assign(
            roi_pct=lambda x: x["avg_roi"] * 100,
            price_m2_million=lambda x: x["avg_price_m2"] / VND_MILLION,
        )
        .sort_values("avg_roi", ascending=False)
    )


@lru_cache(maxsize=1)
def train_model() -> tuple[Pipeline, dict[str, float]]:
    df = load_data()
    features = [
        "district",
        "Type of House",
        "Legal Documents",
        "area",
        "bedrooms_num",
        "toilets_num",
        "floor_num",
        "price_per_m2",
        "ROI",
        "planning_risk_score",
    ]
    planning_scores = planning_risk_by_district()
    model_df = df.copy()
    model_df["planning_risk_score"] = model_df["district"].map(planning_scores).fillna(0.45)
    model_df = model_df[features + ["price_vnd"]].dropna(subset=["price_vnd", "area", "price_per_m2", "ROI"])
    x = model_df[features]
    y = np.log1p(model_df["price_vnd"])

    categorical = ["district", "Type of House", "Legal Documents"]
    numeric = [column for column in features if column not in categorical]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
            ("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]), numeric),
        ]
    )
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=120,
                    max_depth=18,
                    min_samples_leaf=4,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
    pipeline.fit(x_train, y_train)
    predicted = np.expm1(pipeline.predict(x_test))
    actual = np.expm1(y_test)
    metrics = {
        "mae": float(mean_absolute_error(actual, predicted)),
        "r2": float(r2_score(actual, predicted)),
        "trained_rows": float(len(model_df)),
        "features": features,
        "algorithm": "RandomForestRegressor with legal/planning risk feature",
    }
    return pipeline, metrics


def planning_risk_by_district() -> dict[str, float]:
    ensure_operational_tables()
    mapping = {"low": 0.2, "medium": 0.55, "high": 0.85}
    with connect_db() as con:
        rows = con.execute("SELECT district, risk_level FROM dim_planning_zone").fetchall()
    return {row["district"]: mapping.get(row["risk_level"], 0.55) for row in rows}


def dynamic_risk_level(row: Any) -> str:
    if row.opportunity_score >= 68 and row.price_m2_million < 90:
        return "low"
    if row.roi_pct < 13 or row.price_m2_million > 160:
        return "high"
    return "medium"


def transactions_summary(filters: Filters) -> dict[str, Any]:
    ensure_operational_tables()
    clauses: list[str] = []
    params: list[Any] = []
    districts = filters.districts
    if filters.city and not districts:
        districts = sorted(load_data().loc[load_data()["city"] == filters.city, "district"].dropna().unique().tolist())
    if districts:
        clauses.append("district IN (%s)" % ",".join("?" for _ in districts))
        params.extend(districts)
    if filters.property_types:
        clauses.append("property_type IN (%s)" % ",".join("?" for _ in filters.property_types))
        params.extend(filters.property_types)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect_db() as con:
        row = con.execute(
            f"""
            SELECT
                COUNT(*) AS transaction_count,
                AVG(price_vnd) AS avg_transaction_price,
                AVG(price_per_sqm) AS avg_transaction_price_m2,
                AVG(confidence_score) AS avg_confidence,
                MAX(updated_at) AS last_updated
            FROM fact_transactions
            {where}
            """,
            params,
        ).fetchone()
    return dict(row)


def add_bi_buckets(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["price_band"] = pd.cut(
        result["price_billion"],
        bins=[0, 3, 7, 15, np.inf],
        labels=["< 3 tỷ", "3-7 tỷ", "7-15 tỷ", "> 15 tỷ"],
        include_lowest=True,
    ).astype(str)
    result["area_band"] = pd.cut(
        result["area"],
        bins=[0, 45, 80, 130, np.inf],
        labels=["< 45m²", "45-80m²", "80-130m²", "> 130m²"],
        include_lowest=True,
    ).astype(str)
    result["roi_band"] = pd.cut(
        result["business_roi_pct"],
        bins=[0, 10, 15, 20, np.inf],
        labels=["ROI < 10%", "ROI 10-15%", "ROI 15-20%", "ROI > 20%"],
        include_lowest=True,
    ).astype(str)
    return result


SLICE_DIMENSIONS = {
    "district": "Khu vực",
    "Type of House": "Loại tài sản",
    "Legal Documents": "Pháp lý",
    "price_band": "Nhóm giá",
    "area_band": "Nhóm diện tích",
    "roi_band": "Nhóm ROI",
}

SLICE_METRICS = {
    "listings": "Số tin",
    "avg_price": "Giá TB",
    "median_price": "Giá trung vị",
    "avg_price_m2": "Giá/m² TB",
    "avg_roi": "ROI TB",
    "total_value": "Tổng giá trị",
    "opportunity_score": "Điểm cơ hội",
}


def aggregate_slice(df: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    grouped = (
        df.groupby(dimensions, dropna=False)
        .agg(
            listings=("Location", "count"),
            avg_price=("price_vnd", "mean"),
            median_price=("price_vnd", "median"),
            avg_price_m2=("price_per_m2", "mean"),
            avg_roi=("business_roi_pct", "mean"),
            total_value=("price_vnd", "sum"),
            volatility=("business_roi_pct", "std"),
        )
        .reset_index()
    )
    grouped["volatility"] = grouped["volatility"].fillna(0)
    grouped["opportunity_score"] = (
        normalize(grouped["avg_roi"]) * 0.44
        + normalize(grouped["listings"]) * 0.2
        + normalize(grouped["avg_price_m2"], inverse=True) * 0.2
        + normalize(grouped["volatility"], inverse=True) * 0.16
    ) * 100
    return grouped


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/metadata")
def metadata() -> dict[str, Any]:
    df = load_data()
    districts_by_city = {
        city: sorted(df.loc[df["city"] == city, "district"].dropna().unique().tolist()) for city in CITY_LABELS if city in df["city"].unique()
    }
    return {
        "rows": len(df),
        "districts": sorted(df["district"].dropna().unique().tolist()),
        "cities": [city for city in CITY_LABELS if city in df["city"].unique()],
        "districts_by_city": districts_by_city,
        "property_types": sorted(df["Type of House"].dropna().unique().tolist()),
        "legal_documents": sorted(df["Legal Documents"].dropna().unique().tolist()),
        "price_range": [float(df["price_billion"].quantile(0.01)), float(df["price_billion"].quantile(0.99))],
        "area_range": [float(df["area"].quantile(0.01)), float(df["area"].quantile(0.99))],
        "roi_range": [float(df["business_roi_pct"].min()), float(df["business_roi_pct"].max())],
    }


@app.get("/api/methodology")
def methodology() -> dict[str, Any]:
    status = etl_status()
    return {
        "problem": "Doanh nghiệp cần hệ thống MIS/DSS/EIS để dự đoán giá bất động sản, so sánh ROI, kiểm soát rủi ro pháp lý/quy hoạch và chọn chiến lược đầu tư.",
        "data": {
            "primary_dataset": "datasets/clean_dataset.csv",
            "raw_inputs": ["datasets/raw/clean_data.csv", "datasets/raw/clean_hanoi.csv"],
            "public_data_hub": PUBLIC_SOURCES,
            "governance": "Nguồn công khai được cache, ghi nguồn, timestamp và confidence score để demo ổn định.",
        },
        "methods": [
            "BI dashboard: KPI, trend, phân khúc, khu vực.",
            "DSS scoring: opportunity_score = ROI + thanh khoản proxy + giá/m2 + biến động ROI.",
            "Prediction: Random Forest dự đoán giá, bổ sung legal/planning risk score.",
            "RAG: retrieve tài liệu pháp lý/quy hoạch, gọi local Ollama LLM nếu khả dụng.",
            "Realtime ETL: manual refresh + scheduled refresh + incremental insert bằng source_id.",
        ],
        "information_systems": [
            {"type": "MIS", "mapping": "Báo cáo KPI, thị trường, phân khúc và pipeline dữ liệu."},
            {"type": "DSS", "mapping": "Dự đoán giá, opportunity score, khuyến nghị đầu tư."},
            {"type": "EIS", "mapping": "Executive dashboard cho lãnh đạo."},
            {"type": "KWS", "mapping": "RAG/LLM giúp khai thác tri thức pháp lý/quy hoạch."},
            {"type": "TPS", "mapping": "fact_transactions là lớp ghi nhận giao dịch/proxy giao dịch."},
            {"type": "OAS", "mapping": "Demo script, citation và báo cáo hỗ trợ truyền thông nội bộ."},
        ],
        "etl": status,
    }


@app.get("/api/model-info")
def model_info() -> dict[str, Any]:
    _, metrics = train_model()
    return metrics


@app.post("/api/analytics")
def analytics(filters: Filters) -> dict[str, Any]:
    df = apply_filters(load_data(), filters)
    if df.empty:
        return {"empty": True, "kpis": {}, "timeline": [], "districts": [], "types": [], "samples": []}

    district_df = district_score(df)
    type_df = type_score(df)
    timeline = (
        df.set_index("date")
        .sort_index()
        .resample("ME")
        .agg(price_billion=("price_billion", "mean"), roi_pct=("business_roi_pct", "mean"), listings=("Location", "count"))
        .dropna()
        .reset_index()
    )
    best = district_df.iloc[0]
    risky = district_df.sort_values(["roi_pct", "volatility"], ascending=[True, False]).head(5)
    samples = df.sort_values("ROI", ascending=False).head(80)
    tx = transactions_summary(filters)

    return {
        "empty": False,
        "kpis": {
            "listings": int(len(df)),
            "total_value": float(df["price_vnd"].sum()),
            "median_price": float(df["price_vnd"].median()),
            "avg_price_m2": float(df["price_per_m2"].mean()),
            "avg_roi": float(df["business_roi_pct"].mean()),
            "best_district": str(best["district"]),
            "best_score": float(best["opportunity_score"]),
            "transaction_count": int(tx.get("transaction_count") or 0),
            "avg_transaction_price": float(tx.get("avg_transaction_price") or 0),
            "avg_confidence": float(tx.get("avg_confidence") or 0),
            "last_data_refresh": tx.get("last_updated"),
        },
        "timeline": records(timeline),
        "districts": records(district_df),
        "types": records(type_df),
        "risky": records(risky),
        "samples": records(
            samples[
                [
                    "Location",
                    "district",
                    "Type of House",
                    "Legal Documents",
                    "price_vnd",
                    "area",
                    "price_per_m2",
                    "ROI",
                    "date",
                ]
            ]
        ),
    }


@app.post("/api/slice-dice")
def slice_dice(payload: SliceDiceRequest) -> dict[str, Any]:
    row_dimension = payload.row_dimension if payload.row_dimension in SLICE_DIMENSIONS else "district"
    column_dimension = payload.column_dimension if payload.column_dimension in SLICE_DIMENSIONS else "Type of House"
    metric = payload.metric if payload.metric in SLICE_METRICS else "avg_roi"
    if row_dimension == column_dimension:
        column_dimension = "Type of House" if row_dimension != "Type of House" else "district"

    base_df = load_data()
    filtered = add_bi_buckets(apply_filters(base_df, payload.filters))
    overall = add_bi_buckets(base_df)
    if filtered.empty:
        return {
            "empty": True,
            "dimensions": SLICE_DIMENSIONS,
            "metrics": SLICE_METRICS,
            "matrix": [],
            "rows": [],
            "columns": [],
            "top_segments": [],
            "filter_context": {},
            "benchmark": {},
        }

    grouped = aggregate_slice(filtered, [row_dimension, column_dimension])
    row_grouped = aggregate_slice(filtered, [row_dimension]).sort_values(metric, ascending=False)
    overall_grouped = aggregate_slice(overall, [row_dimension])
    matrix = grouped.pivot_table(index=row_dimension, columns=column_dimension, values=metric, aggfunc="mean").fillna(0)
    matrix_records = []
    for row_name, values in matrix.iterrows():
        item: dict[str, Any] = {"segment": str(row_name)}
        for col_name, value in values.items():
            item[str(col_name)] = float(value)
        matrix_records.append(item)

    active_filters = []
    if payload.filters.city:
        active_filters.append(payload.filters.city)
    if payload.filters.districts:
        active_filters.append(f"{len(payload.filters.districts)} khu vực")
    if payload.filters.property_types:
        active_filters.append(f"{len(payload.filters.property_types)} loại tài sản")
    if payload.filters.price_max is not None:
        active_filters.append(f"giá <= {payload.filters.price_max:.1f} tỷ")
    if payload.filters.roi_min is not None:
        active_filters.append(f"ROI >= {payload.filters.roi_min:.1f}%")

    return {
        "empty": False,
        "dimensions": SLICE_DIMENSIONS,
        "metrics": SLICE_METRICS,
        "row_dimension": row_dimension,
        "column_dimension": column_dimension,
        "metric": metric,
        "metric_label": SLICE_METRICS[metric],
        "rows": records(row_grouped.head(20)),
        "matrix": matrix_records,
        "columns": [str(col) for col in matrix.columns.tolist()],
        "top_segments": records(grouped.sort_values(metric, ascending=False).head(15)),
        "filter_context": {
            "active": active_filters or ["Toàn thị trường"],
            "filtered_records": int(len(filtered)),
            "total_records": int(len(base_df)),
            "coverage_pct": float(len(filtered) / len(base_df) * 100),
            "sample_warning": bool(len(filtered) < 100),
        },
        "benchmark": {
            "market_avg_roi": float(base_df["business_roi_pct"].mean()),
            "filtered_avg_roi": float(filtered["business_roi_pct"].mean()),
            "market_avg_price_m2": float(base_df["price_per_m2"].mean()),
            "filtered_avg_price_m2": float(filtered["price_per_m2"].mean()),
            "market_records": int(len(base_df)),
            "filtered_records": int(len(filtered)),
        },
        "overall_rows": records(overall_grouped.head(20)),
    }


@app.post("/api/predict")
def predict(payload: PredictionRequest) -> dict[str, Any]:
    df = load_data()
    model, metrics = train_model()
    local = df[(df["district"] == payload.district) & (df["Type of House"] == payload.property_type)]
    if local.empty:
        local = df[df["district"] == payload.district]
    if local.empty:
        local = df
    planning_scores = planning_risk_by_district()
    planning_risk_score = planning_scores.get(payload.district, 0.45)
    price_per_m2 = float(local["price_per_m2"].median())
    input_df = pd.DataFrame(
        [
            {
                "district": payload.district,
                "Type of House": payload.property_type,
                "Legal Documents": payload.legal_documents,
                "area": payload.area,
                "bedrooms_num": payload.bedrooms,
                "toilets_num": payload.toilets,
                "floor_num": payload.floors,
                "price_per_m2": price_per_m2,
                "ROI": payload.roi_expected,
                "planning_risk_score": planning_risk_score,
            }
        ]
    )
    predicted = float(np.expm1(model.predict(input_df)[0]))
    market_median = float(local["price_vnd"].median())
    gap_pct = (predicted - market_median) / market_median * 100
    return {
        "predicted_price": predicted,
        "lower_bound": max(0, predicted - metrics["mae"]),
        "upper_bound": predicted + metrics["mae"],
        "price_per_m2": predicted / payload.area,
        "market_median": market_median,
        "gap_pct": gap_pct,
        "planning_risk_score": planning_risk_score,
        "planning_risk_label": "low" if planning_risk_score < 0.35 else "medium" if planning_risk_score < 0.7 else "high",
        "model": metrics,
    }


def projection_rows(initial_value: float, growth_pct: float, years: int, mae: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year in range(0, years + 1):
        pessimistic_growth = max(-0.2, (growth_pct - 4.0) / 100)
        base_growth = growth_pct / 100
        optimistic_growth = (growth_pct + 4.0) / 100
        pessimistic = initial_value * ((1 + pessimistic_growth) ** year)
        base = initial_value * ((1 + base_growth) ** year)
        optimistic = initial_value * ((1 + optimistic_growth) ** year)
        confidence_width = mae * math.sqrt(max(year, 1)) * 1.25
        rows.append(
            {
                "year": year,
                "pessimistic": float(pessimistic),
                "base": float(base),
                "optimistic": float(optimistic),
                "confidence_low": float(max(0, base - confidence_width)),
                "confidence_high": float(base + confidence_width),
            }
        )
    return rows


@app.post("/api/what-if")
def what_if(payload: WhatIfRequest) -> dict[str, Any]:
    predicted = predict(payload)
    budget = float(payload.budget_vnd)
    growth = float(payload.annual_growth_pct)
    years = int(payload.years)
    investable_units = budget / predicted["predicted_price"] if predicted["predicted_price"] > 0 else 0
    terminal_value = budget * ((1 + growth / 100) ** years)
    capital_gain = terminal_value - budget
    cumulative_roi_pct = capital_gain / budget * 100
    annualized_roi_pct = (((terminal_value / budget) ** (1 / years)) - 1) * 100
    annual_cash_yield = max(0, budget * payload.roi_expected)
    avg_annual_gain = capital_gain / years if years else 0
    annual_benefit = annual_cash_yield + max(0, avg_annual_gain)
    payback_years = budget / annual_benefit if annual_benefit > 0 else None
    scenario_rows = projection_rows(budget, growth, years, predicted["model"]["mae"])

    return {
        "input": {
            "budget_vnd": budget,
            "annual_growth_pct": growth,
            "years": years,
            "roi_expected": payload.roi_expected,
        },
        "asset_prediction": predicted,
        "summary": {
            "investable_units": float(investable_units),
            "future_value": float(terminal_value),
            "capital_gain": float(capital_gain),
            "cumulative_roi_pct": float(cumulative_roi_pct),
            "annualized_roi_pct": float(annualized_roi_pct),
            "annual_cash_yield": float(annual_cash_yield),
            "payback_years": float(payback_years) if payback_years is not None else None,
        },
        "projection": scenario_rows,
        "scenarios": [
            {"name": "Xấu", "growth_pct": growth - 4.0, "terminal_value": scenario_rows[-1]["pessimistic"]},
            {"name": "Cơ sở", "growth_pct": growth, "terminal_value": scenario_rows[-1]["base"]},
            {"name": "Lạc quan", "growth_pct": growth + 4.0, "terminal_value": scenario_rows[-1]["optimistic"]},
        ],
        "interpretation": (
            "What-if simulation dùng ngân sách làm vốn đầu tư ban đầu, tăng trưởng hằng năm làm giả định tăng giá, "
            "ROI kỳ vọng làm dòng tiền/cash yield. Payback period kết hợp cash yield và capital gain trung bình năm."
        ),
    }


@app.post("/api/recommendation/future")
def future_recommendation(payload: FutureRecommendationRequest) -> dict[str, Any]:
    started = time.perf_counter()
    filtered_df = apply_filters(load_data(), payload.filters)
    if filtered_df.empty:
        filtered_df = load_data()
    analytics_payload = analytics(payload.filters if not apply_filters(load_data(), payload.filters).empty else Filters(city=payload.filters.city))
    what_if_payload = what_if(payload)
    risk_label = what_if_payload["asset_prediction"].get("planning_risk_label", "medium")
    question = (
        f"Nen mua them, giu hay ban bot tai san o {payload.district} trong {payload.years} nam toi "
        f"voi kich ban tang truong {payload.annual_growth_pct:.1f}%/nam, ROI ky vong {payload.roi_expected * 100:.1f}% "
        f"va rui ro quy hoach {risk_label}? Hay neu ro co hoi, suy giam va rui ro hai mat cua thi truong."
    )
    sources, retrieval_mode = retrieve_context(question, filtered_df, payload.top_k, payload.filters)
    recommendation, model_name = call_ollama_future_recommendation(what_if_payload, analytics_payload, payload.filters, sources)
    if not recommendation:
        recommendation = future_recommendation_fallback(what_if_payload, analytics_payload, payload.filters, sources, retrieval_mode)
        model_name = recommendation["model"]

    recommendation["retrieval_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
    recommendation["question"] = question
    recommendation["what_if"] = what_if_payload
    recommendation["analytics_snapshot"] = {
        "best_district": analytics_payload.get("kpis", {}).get("best_district"),
        "avg_roi": analytics_payload.get("kpis", {}).get("avg_roi"),
        "risky": analytics_payload.get("risky", [])[:3],
    }
    recommendation["model"] = model_name or recommendation.get("model")
    return recommendation


@app.post("/api/etl/run")
def etl_run() -> dict[str, Any]:
    result = run_etl(mode="manual")
    return {"result": result, "status": etl_status()}


@app.get("/api/etl/status")
def get_etl_status() -> dict[str, Any]:
    return etl_status()


@app.get("/api/planning/zones")
def planning_zones() -> dict[str, Any]:
    seed_planning_and_documents()
    with connect_db() as con:
        rows = con.execute("SELECT * FROM dim_planning_zone ORDER BY district").fetchall()
    return {"zones": [dict(row) for row in rows], "sources": PUBLIC_SOURCES}


@app.get("/api/map/districts")
def map_districts(city: str | None = None) -> dict[str, Any]:
    selected_city = city or DEFAULT_CITY
    df = load_data()
    if selected_city in df["city"].unique():
        df = df[df["city"] == selected_city]
    score_df = district_score(df)
    coords = district_coordinates()
    zones = {row["district"]: row for row in planning_zones()["zones"]}
    map_rows: list[dict[str, Any]] = []
    for row in score_df.itertuples(index=False):
        coord = coords.get(district_key(row.district))
        if not coord:
            continue
        zone = zones.get(row.district, {})
        risk_level = dynamic_risk_level(row)
        map_rows.append(
            {
                "district": row.district,
                "city": selected_city,
                "latitude": coord["latitude"],
                "longitude": coord["longitude"],
                "listings": int(row.listings),
                "roi_pct": float(row.roi_pct),
                "price_m2_million": float(row.price_m2_million),
                "opportunity_score": float(row.opportunity_score),
                "risk_level": risk_level,
                "planning_note": zone.get("description", "Chưa có ghi chú quy hoạch."),
                "recommendation": (
                    "Mở rộng danh mục"
                    if row.opportunity_score >= 65
                    else "Gom chọn lọc"
                    if row.roi_pct >= 12
                    else "Kiểm soát rủi ro"
                ),
            }
        )
    return {
        "city": selected_city,
        "center": CITY_CENTERS.get(selected_city, CITY_CENTERS[DEFAULT_CITY]),
        "districts": map_rows,
        "sources": PUBLIC_SOURCES,
    }


def analytics_documents(df: pd.DataFrame) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for row in district_score(df).head(20).itertuples(index=False):
        city = df.loc[df["district"] == row.district, "city"].dropna().mode()
        docs.append(
            {
                "title": f"Market intelligence - {row.district}",
                "content": (
                    f"{row.district}: {row.listings} tin, ROI {row.roi_pct:.2f}%, "
                    f"giá trung vị {row.median_price / VND_BILLION:.2f} tỷ, "
                    f"giá/m2 {row.price_m2_million:.1f} triệu, điểm cơ hội {row.opportunity_score:.1f}/100."
                ),
                "source_name": "PropertyVision BI mart",
                "source_url": "datasets/clean_dataset.csv",
                "district": row.district,
                "city": city.iloc[0] if not city.empty else None,
            }
        )
    city_mode = df["city"].dropna().mode()
    for row in type_score(df).itertuples(index=False):
        docs.append(
            {
                "title": f"Property segment - {getattr(row, '_0')}",
                "content": (
                    f"{getattr(row, '_0')}: {row.listings} tin, ROI {row.roi_pct:.2f}%, "
                    f"giá/m2 {row.price_m2_million:.1f} triệu, diện tích TB {row.avg_area:.1f} m2."
                ),
                "source_name": "PropertyVision segment mart",
                "source_url": "datasets/clean_dataset.csv",
                "city": city_mode.iloc[0] if not city_mode.empty else None,
            }
        )
    return docs


def load_rag_documents(df: pd.DataFrame) -> list[dict[str, Any]]:
    seed_planning_and_documents()
    docs = analytics_documents(df)
    city_lookup = district_city_lookup()
    with connect_db() as con:
        legal_rows = con.execute("SELECT * FROM legal_documents").fetchall()
        zone_rows = con.execute("SELECT * FROM dim_planning_zone").fetchall()
    for row in legal_rows:
        inferred_city = (
            city_lookup.get(row["district"])
            if row["district"]
            else infer_document_city(row["title"], row["source_name"], row["source_url"])
        )
        docs.append(
            {
                "title": row["title"],
                "content": row["content"],
                "source_name": row["source_name"],
                "source_url": row["source_url"],
                "district": row["district"],
                "city": inferred_city,
            }
        )
    for row in zone_rows:
        docs.append(
            {
                "title": f"GIS planning zone - {row['district']}",
                "content": (
                    f"{row['district']} có risk level {row['risk_level']}. "
                    f"Loại lớp: {row['zone_type']}. {row['description']}"
                ),
                "source_name": row["source_name"],
                "source_url": row["source_url"],
                "district": row["district"],
                "city": city_lookup.get(row["district"]) if row["district"] else None,
            }
        )
    return docs


_rag_cache: dict[str, Any] = {}


def clear_rag_cache() -> None:
    _rag_cache.clear()


def build_rag_index(df: pd.DataFrame) -> dict[str, Any]:
    docs = load_rag_documents(df)
    texts = [f"{doc['title']}\n{doc['content']}" for doc in docs]
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        matrix = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        nn = NearestNeighbors(n_neighbors=min(10, len(docs)), metric="cosine")
        nn.fit(matrix)
        return {"docs": docs, "texts": texts, "matrix": matrix, "nn": nn, "embedder": model, "mode": "sentence-transformers"}
    except Exception:
        vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        nn = NearestNeighbors(n_neighbors=min(10, len(docs)), metric="cosine")
        nn.fit(matrix)
        return {"docs": docs, "texts": texts, "matrix": matrix, "nn": nn, "embedder": vectorizer, "mode": "tfidf-fallback"}


def get_rag_index(df: pd.DataFrame) -> dict[str, Any]:
    key = f"{len(df)}:{etl_status()['legal_documents']}:{etl_status()['planning_zones']}"
    if _rag_cache.get("key") != key:
        _rag_cache["key"] = key
        _rag_cache["index"] = build_rag_index(df)
    return _rag_cache["index"]


def candidate_doc_indices(index: dict[str, Any], filters: Filters | None, df: pd.DataFrame) -> list[int]:
    docs = index["docs"]
    if not filters:
        return list(range(len(docs)))

    available_cities = set(df["city"].dropna().astype(str).tolist()) if "city" in df.columns else set()
    selected_city = filters.city if filters.city in available_cities else None
    selected_districts = set(filters.districts or [])

    indices: list[int] = []
    for idx, doc in enumerate(docs):
        doc_city = doc.get("city")
        doc_district = doc.get("district")
        city_match = not selected_city or doc_city is None or str(doc_city) == selected_city
        district_match = not selected_districts or doc_district is None or str(doc_district) in selected_districts
        if city_match and district_match:
            indices.append(idx)

    if indices:
        return indices

    if selected_city:
        city_only = [
            idx for idx, doc in enumerate(docs)
            if doc.get("city") is None or str(doc.get("city")) == selected_city
        ]
        if city_only:
            return city_only

    return list(range(len(docs)))


def retrieve_context(question: str, df: pd.DataFrame, top_k: int = 5, filters: Filters | None = None) -> tuple[list[dict[str, Any]], str]:
    index = get_rag_index(df)
    doc_indices = candidate_doc_indices(index, filters, df)
    if not doc_indices:
        return [], index["mode"]

    if index["mode"] == "sentence-transformers":
        query = index["embedder"].encode([question], normalize_embeddings=True, show_progress_bar=False)
        candidate_matrix = index["matrix"][doc_indices]
        scores = candidate_matrix @ query[0]
        ranked_positions = np.argsort(scores)[::-1][: min(top_k, len(doc_indices))]
        ranked = [(doc_indices[int(pos)], float(scores[int(pos)])) for pos in ranked_positions]
    else:
        query = index["embedder"].transform([question])
        candidate_matrix = index["matrix"][doc_indices]
        similarities = cosine_similarity(query, candidate_matrix)[0]
        ranked_positions = np.argsort(similarities)[::-1][: min(top_k, len(doc_indices))]
        ranked = [(doc_indices[int(pos)], float(similarities[int(pos)])) for pos in ranked_positions]

    sources: list[dict[str, Any]] = []
    for doc_idx, score in ranked:
        doc = dict(index["docs"][int(doc_idx)])
        doc["score"] = score
        sources.append(doc)
    return sources, index["mode"]


def call_ollama(question: str, sources: list[dict[str, Any]], df: pd.DataFrame) -> tuple[str | None, str | None]:
    context = "\n\n".join(
        f"[{idx + 1}] {source['title']} - {source['content']} (Nguồn: {source.get('source_name')})"
        for idx, source in enumerate(sources)
    )
    top = district_score(df).iloc[0]
    prompt = f"""
Bạn là trợ lý phân tích đầu tư bất động sản cho ban điều hành doanh nghiệp.
Hãy trả lời bằng tiếng Việt, giọng điều hành, rõ ý, ngắn gọn, dễ hiểu với CEO.
Ưu tiên ngôn ngữ kinh doanh và đầu tư bất động sản. Tránh thuật ngữ kỹ thuật nếu không thật sự cần.
Nếu dùng nguồn, nhắc theo số [1], [2].

Câu hỏi: {question}

Tóm tắt hiện tại:
- Khu vực ưu tiên: {top['district']}
- Điểm cơ hội: {top['opportunity_score']:.1f}/100
- ROI bình quân khu vực ưu tiên: {top['roi_pct']:.2f}%

Nguồn tham chiếu:
{context}

Yêu cầu trả lời:
1. Kết luận điều hành: nên ưu tiên khu nào hoặc nên hành động thế nào.
2. Cơ sở nhận định: nêu ngắn gọn các dữ kiện chính.
3. Rủi ro cần lưu ý: đặc biệt là pháp lý, quy hoạch, thanh khoản hoặc chu kỳ thị trường.
4. Hành động tiếp theo: nêu bước đi cụ thể cho doanh nghiệp.

Phong cách:
- Không lan man.
- Mỗi ý nên hướng tới quyết định.
- Không dùng giọng giải thích kỹ thuật.
""".strip()
    for model_name in OLLAMA_MODELS:
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": model_name, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
                timeout=35,
            )
            if response.ok:
                payload = response.json()
                answer = payload.get("response", "").strip()
                if answer:
                    return answer, model_name
        except requests.RequestException:
            continue
    return None, None


def future_recommendation_fallback(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
    sources: list[dict[str, Any]],
    retrieval_mode: str,
) -> dict[str, Any]:
    kpis = analytics_payload.get("kpis", {})
    risky_rows = analytics_payload.get("risky", [])
    summary = what_if_payload.get("summary", {})
    scenario_rows = what_if_payload.get("projection", [])
    budget = float(what_if_payload.get("input", {}).get("budget_vnd") or 0)
    loss_row = next((row for row in scenario_rows if float(row.get("pessimistic") or 0) < budget), None)
    weak_district = risky_rows[0]["district"] if risky_rows else None
    best_district = kpis.get("best_district")
    cumulative_roi = float(summary.get("cumulative_roi_pct") or 0)

    if loss_row:
        action = (
            f"Khuyến nghị ưu tiên phòng thủ: tạm dừng mở rộng quá nhanh, xem xét bán bớt hoặc không tăng tỷ trọng "
            f"tại {weak_district or 'nhóm khu vực rủi ro cao'}, và chỉ giải ngân chọn lọc tại {best_district or 'khu vực dẫn đầu'}."
        )
        risks = [
            f"Kịch bản xấu có thể thua lỗ từ năm {2025 + int(loss_row.get('year', 0))}.",
            "Thanh khoản và biên an toàn có thể suy giảm nếu thị trường tiếp tục chậm lại.",
        ]
    elif cumulative_roi < 15:
        action = (
            f"Khuyến nghị giải ngân chọn lọc: ưu tiên tài sản pháp lý rõ ràng tại {best_district or 'khu vực dẫn đầu'}, "
            "giữ tỷ trọng vừa phải và tránh dùng đòn bẩy cao."
        )
        risks = [
            "Biên lợi nhuận chưa đủ rộng, nên dễ bị bào mòn nếu chọn sai thời điểm giải ngân.",
            f"{weak_district or 'Một số khu vực hiệu quả thấp'} cần được kiểm tra kỹ về quy hoạch và khả năng thoát hàng.",
        ]
    else:
        action = (
            f"Khuyến nghị có thể mua thêm có kiểm soát tại {best_district or 'khu vực dẫn đầu'}, "
            "nhưng vẫn cần theo dõi sát kịch bản xấu và đặt ngưỡng dừng lỗ cho nhóm khu vực yếu."
        )
        risks = [
            "Thị trường bất động sản luôn có hai mặt: kỳ vọng lợi nhuận cao nhưng thanh khoản có thể giảm mạnh khi chu kỳ đảo chiều.",
            f"{weak_district or 'Nhóm khu vực điểm thấp'} vẫn là điểm cảnh báo nếu doanh nghiệp muốn mở rộng danh mục.",
        ]

    basis = [
        f"Bộ lọc hiện tại: {filters_summary(filters)}.",
        f"ROI tích lũy ở kịch bản cơ sở: {cumulative_roi:.2f}%.",
        f"Khu vực ưu tiên hiện tại: {best_district or 'chưa xác định'}.",
    ]
    return {
        "answer": action,
        "risks": risks,
        "basis": basis,
        "sources": sources,
        "model": "future-retrieval-fallback",
        "mode": f"{retrieval_mode}-fallback",
        "llm_available": False,
    }


def call_ollama_future_recommendation(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
    sources: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    kpis = analytics_payload.get("kpis", {})
    risky_rows = analytics_payload.get("risky", [])
    summary = what_if_payload.get("summary", {})
    scenarios = what_if_payload.get("scenarios", [])
    projection = what_if_payload.get("projection", [])
    scenario_text = "\n".join(
        f"- {item['name']}: growth {item['growth_pct']:.2f}%, terminal value {item['terminal_value'] / VND_BILLION:.2f} ty"
        for item in scenarios
    )
    sampled_years = "\n".join(
        f"- Nam {2025 + int(row['year'])}: xau {row['pessimistic'] / VND_BILLION:.2f} ty, co so {row['base'] / VND_BILLION:.2f} ty"
        for row in projection[: min(6, len(projection))]
    )
    source_context = "\n\n".join(
        f"[{idx + 1}] {source['title']} - {source['content']} (Nguon: {source.get('source_name')})"
        for idx, source in enumerate(sources)
    )
    risky_text = ", ".join(row["district"] for row in risky_rows[:3]) or "khong co khu vuc rui ro noi bat"
    prompt = f"""
Bạn là trợ lý phân tích đầu tư bất động sản cho ban điều hành doanh nghiệp.
Hãy đưa ra khuyến nghị đầu tư tương lai bằng tiếng Việt, theo giọng điều hành, ngắn gọn, dễ hiểu với CEO.
Bắt buộc cân bằng giữa cơ hội và rủi ro. Không được chỉ nói một chiều theo hướng tăng trưởng.
Phải nêu rõ mặt trái của thị trường nếu doanh nghiệp mở rộng quá nhanh.

Bối cảnh hiện tại: {filters_summary(filters)}

Tài sản đang mô phỏng:
- Mức rủi ro quy hoạch: {what_if_payload['asset_prediction'].get('planning_risk_label', 'unknown')}
- Giá trung vị khu vực: {what_if_payload['asset_prediction'].get('market_median', 0) / VND_BILLION:.2f} tỷ
- Ngân sách: {what_if_payload['input']['budget_vnd'] / VND_BILLION:.2f} tỷ
- Tăng trưởng giả định: {what_if_payload['input']['annual_growth_pct']:.2f}%/năm
- Thời gian nắm giữ: {what_if_payload['input']['years']} năm
- ROI kỳ vọng: {what_if_payload['input']['roi_expected'] * 100:.2f}%

Tóm tắt danh mục:
- Khu vực ưu tiên hiện tại: {kpis.get('best_district', 'N/A')}
- Điểm cơ hội: {kpis.get('best_score', 0):.1f}/100
- ROI bình quân: {kpis.get('avg_roi', 0):.2f}%
- Khu vực cần cảnh báo: {risky_text}

Tóm tắt mô phỏng:
- Giá trị tương lai: {summary.get('future_value', 0) / VND_BILLION:.2f} tỷ
- Lợi nhuận vốn: {summary.get('capital_gain', 0) / VND_BILLION:.2f} tỷ
- ROI tích lũy: {summary.get('cumulative_roi_pct', 0):.2f}%
- Thời gian hoàn vốn: {summary.get('payback_years')}

Các kịch bản:
{scenario_text}

Các mốc năm:
{sampled_years}

Nguồn tham chiếu:
{source_context}

Trả về đúng định dạng sau:
ACTION: ...
WHY: ...
RISKS:
- ...
- ...
SUGGESTION: ...
BASIS:
- ...
- ...

Yêu cầu diễn đạt:
- ACTION: chỉ rõ nên mua thêm, giữ tỷ trọng, bán bớt hay tạm dừng giải ngân.
- WHY: nêu căn cứ kinh doanh ngắn gọn.
- RISKS: nêu các rủi ro chính, bao gồm thanh khoản, pháp lý, quy hoạch, hoặc chu kỳ thị trường.
- SUGGESTION: nêu bước hành động tiếp theo cho doanh nghiệp.
- BASIS: chỉ ghi các dữ kiện cốt lõi dùng để ra quyết định.
""".strip()

    for model_name in OLLAMA_MODELS:
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": model_name, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
                timeout=40,
            )
            if not response.ok:
                continue
            payload = response.json()
            answer = payload.get("response", "").strip()
            if not answer:
                continue

            sections = {"ACTION": "", "WHY": "", "RISKS": "", "SUGGESTION": "", "BASIS": ""}
            current = None
            for raw_line in answer.splitlines():
                line = raw_line.strip()
                matched = next((key for key in sections if line.startswith(f"{key}:")), None)
                if matched:
                    sections[matched] = line.split(":", 1)[1].strip()
                    current = matched
                elif current and line:
                    sections[current] = f"{sections[current]}\n{line}".strip()

            risks = [item.strip("- ").strip() for item in sections["RISKS"].splitlines() if item.strip()]
            basis = [item.strip("- ").strip() for item in sections["BASIS"].splitlines() if item.strip()]
            result = {
                "answer": sections["ACTION"] or answer,
                "why": sections["WHY"],
                "risks": risks,
                "suggestion": sections["SUGGESTION"],
                "basis": basis,
                "sources": sources,
                "model": model_name,
                "mode": "ollama-future-recommendation",
                "llm_available": True,
            }
            return result, model_name
        except requests.RequestException:
            continue
    return None, None


@app.post("/api/assistant")
def assistant(payload: AssistantRequest) -> dict[str, Any]:
    started = time.perf_counter()
    df = apply_filters(load_data(), payload.filters)
    if df.empty:
        return {
            "answer": "Không có dữ liệu phù hợp với bộ lọc hiện tại.",
            "sources": [],
            "model": None,
            "mode": "empty",
            "llm_available": False,
            "retrieved_context": [],
        }

    sources, retrieval_mode = retrieve_context(payload.question, df, payload.top_k, payload.filters)
    answer, model_name = call_ollama(payload.question, sources, df)
    llm_available = bool(answer)
    if not answer:
        top = district_score(df).iloc[0]
        source_lines = " ".join(f"[{idx + 1}] {source['content']}" for idx, source in enumerate(sources[:3]))
        answer = (
            f"Kết luận điều hành hiện tại là ưu tiên {top['district']} với điểm cơ hội "
            f"{top['opportunity_score']:.1f}/100 và ROI bình quân {top['roi_pct']:.2f}%. "
            f"Các căn cứ chính cho nhận định này gồm: {source_lines} "
            "Trợ lý chưa phản hồi từ mô hình ngôn ngữ, nên hệ thống đang trả lời theo chế độ dự phòng dựa trên dữ liệu và nguồn tham chiếu sẵn có."
        )

    return {
        "answer": answer,
        "sources": sources,
        "model": model_name or "retrieval-fallback",
        "mode": "ollama" if llm_available else f"{retrieval_mode}-fallback",
        "llm_available": llm_available,
        "retrieved_context": sources,
        "retrieval_time_ms": round((time.perf_counter() - started) * 1000, 2),
    }


@app.post("/api/rag/reindex")
def rag_reindex() -> dict[str, Any]:
    clear_rag_cache()
    df = load_data()
    index = get_rag_index(df)
    return {
        "status": "rebuilt",
        "mode": index["mode"],
        "documents": len(index["docs"]),
    }

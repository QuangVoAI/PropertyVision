from __future__ import annotations

import asyncio
import hashlib
import math
import os
import json
import re
import sqlite3
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from huggingface_hub import InferenceClient, hf_hub_download, list_repo_files
from dotenv import load_dotenv
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
HF_STREET_DATASET_REPO = "tinixai/vietnam-real-estates"
HF_STREET_DATASET_CARD_URL = "https://huggingface.co/datasets/tinixai/vietnam-real-estates"
VND_BILLION = 1_000_000_000
VND_MILLION = 1_000_000

load_dotenv(ROOT_DIR / ".env")

HF_QWEN_MODEL = os.getenv("PROPERTYVISION_HF_QWEN_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
HF_INFERENCE_PROVIDER = os.getenv("PROPERTYVISION_HF_INFERENCE_PROVIDER", "featherless-ai")
HF_INFERENCE_TIMEOUT_SECONDS = float(os.getenv("PROPERTYVISION_HF_INFERENCE_TIMEOUT_SECONDS", "15"))
HF_FUTURE_RECOMMENDATION_MAX_TOKENS = int(os.getenv("PROPERTYVISION_FUTURE_RECOMMENDATION_MAX_TOKENS", "320"))
HF_FUTURE_EARLY_DONE_SECONDS = float(os.getenv("PROPERTYVISION_FUTURE_EARLY_DONE_SECONDS", "18"))
HF_FUTURE_COMPLETION_DEADLINE_SECONDS = float(os.getenv("PROPERTYVISION_FUTURE_COMPLETION_DEADLINE_SECONDS", "6"))
HF_FUTURE_STREAM_TRANSPORT = os.getenv("PROPERTYVISION_FUTURE_STREAM_TRANSPORT", "completion").lower()
LLM_BACKEND = os.getenv("PROPERTYVISION_LLM_BACKEND", "hf-provider").strip().lower()
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
FEATHERLESS_BASE_URL = os.getenv("PROPERTYVISION_FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1/chat/completions")
FEATHERLESS_APP_URL = os.getenv("PROPERTYVISION_FEATHERLESS_APP_URL", "http://localhost:5173")
FEATHERLESS_APP_TITLE = os.getenv("PROPERTYVISION_FEATHERLESS_APP_TITLE", "PropertyVision")
HOSTED_QWEN_ENABLED = os.getenv("PROPERTYVISION_USE_HOSTED_QWEN", os.getenv("PROPERTYVISION_USE_LOCAL_LLM", "true")).lower() in {"1", "true", "yes", "on"}
DEFAULT_CITY = "TP Hồ Chí Minh"
CITY_LABELS = ["TP Hồ Chí Minh", "Hà Nội"]
LAND_TYPES = {"Đất thổ cư", "Đất dự án, Khu dân cư", "Đất nông nghiệp, kho bãi"}
STREET_REFERENCE_CACHE_PATH = DATASETS_DIR / ".cache" / "street_market_reference.csv"
STREET_REFERENCE_SOURCE_DIR = DATASETS_DIR / ".cache" / "tinixai_vietnam_real_estates"
STREET_REFERENCE_MIN_LISTINGS = int(os.getenv("PROPERTYVISION_STREET_REFERENCE_MIN_LISTINGS", "3"))
STREET_REFERENCE_MAX_DOCS_PER_DISTRICT = int(os.getenv("PROPERTYVISION_STREET_REFERENCE_MAX_DOCS_PER_DISTRICT", "10"))
STREET_REFERENCE_MAX_SHORTLIST_PER_DISTRICT = int(os.getenv("PROPERTYVISION_STREET_REFERENCE_MAX_SHORTLIST_PER_DISTRICT", "5"))
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
    years: int = Field(default=5, ge=1, le=25)


class AssistantRequest(BaseModel):
    question: str
    filters: Filters = Field(default_factory=Filters)
    top_k: int = Field(default=3, ge=1, le=10)
    task: str = "assistant_question"


class SliceDiceRequest(BaseModel):
    filters: Filters = Field(default_factory=Filters)
    row_dimension: str = "district"
    column_dimension: str = "Type of House"
    metric: str = "avg_roi"


class FutureRecommendationRequest(WhatIfRequest):
    filters: Filters = Field(default_factory=Filters)
    top_k: int = Field(default=3, ge=1, le=10)
    task: str = "decision_memo"
    decision_tab: str = "whatif"


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


def normalize_text(value: str) -> str:
    text = str(value).replace("đ", "d").replace("Đ", "D")
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", ascii_text).strip()


def extract_district_mentions(question: str, districts: list[str]) -> list[str]:
    normalized_question = normalize_text(question)
    unique_districts = sorted({district for district in districts if district}, key=len, reverse=True)
    matches: list[str] = []
    for district in unique_districts:
        if normalize_text(district) in normalized_question:
            matches.append(district)
    return matches


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


def strip_ward_label(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^(Phường|Xã|Thị trấn)\s+", "", text, flags=re.IGNORECASE)
    return text.strip()


def district_match_key(city: str, district: str) -> str:
    text = str(district or "").strip()
    if city == DEFAULT_CITY and normalize_text(text) in {"thu duc", "tp thu duc"}:
        return "thu duc"
    text = re.sub(r"^TP\.?\s*Thủ Đức\s*-\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(Quận|Huyện|Thị xã)\s+", "", text, flags=re.IGNORECASE)
    return normalize_text(text)


def ward_match_key(value: str) -> str:
    return normalize_text(strip_ward_label(value))


@lru_cache(maxsize=1)
def district_display_lookup() -> dict[tuple[str, str], str]:
    df = load_data()[["city", "district"]].dropna().drop_duplicates()
    lookup: dict[tuple[str, str], str] = {}
    for row in df.itertuples(index=False):
        city = str(row.city)
        district = str(row.district)
        lookup[(city, district_match_key(city, district))] = district
    lookup[(DEFAULT_CITY, "thu duc")] = "TP Thủ Đức"
    return lookup


@lru_cache(maxsize=1)
def internal_micro_baselines() -> tuple[pd.DataFrame, pd.DataFrame]:
    scoped = load_data().copy()
    scoped["district_key"] = scoped.apply(lambda row: district_match_key(str(row["city"]), str(row["district"])), axis=1)
    scoped["ward_key"] = scoped["ward"].map(ward_match_key)
    district_baseline = (
        scoped.groupby(["city", "district_key"])
        .agg(
            district_roi=("ROI", "mean"),
            district_price_m2=("price_per_m2", "mean"),
            district_listings=("Location", "count"),
        )
        .reset_index()
    )
    thu_duc_rows = scoped[(scoped["city"] == DEFAULT_CITY) & (scoped["district"].astype(str).str.contains("TP. Thủ Đức", na=False))]
    if not thu_duc_rows.empty:
        thu_duc_baseline = pd.DataFrame(
            [
                {
                    "city": DEFAULT_CITY,
                    "district_key": "thu duc",
                    "district_roi": float(thu_duc_rows["ROI"].mean()),
                    "district_price_m2": float(thu_duc_rows["price_per_m2"].mean()),
                    "district_listings": int(len(thu_duc_rows)),
                }
            ]
        )
        district_baseline = pd.concat([district_baseline, thu_duc_baseline], ignore_index=True)
        district_baseline = district_baseline.drop_duplicates(subset=["city", "district_key"], keep="last")

    ward_baseline = (
        scoped.groupby(["city", "district_key", "ward_key"])
        .agg(
            ward_roi=("ROI", "mean"),
            ward_price_m2=("price_per_m2", "mean"),
            ward_listings=("Location", "count"),
        )
        .reset_index()
    )
    return district_baseline, ward_baseline


def normalize_external_city(value: str) -> str:
    text = str(value or "").strip()
    if text == "Hồ Chí Minh":
        return DEFAULT_CITY
    return text


def fallback_external_district_display(city: str, district: str) -> str:
    text = str(district or "").strip()
    if not text:
        return ""
    if city == DEFAULT_CITY:
        if normalize_text(text) in {"thu duc", "tp thu duc"}:
            return "TP Thủ Đức"
        if text.isdigit():
            return f"Quận {text}"
        if text in {"Bình Chánh", "Củ Chi", "Hóc Môn", "Nhà Bè", "Cần Giờ"}:
            return f"Huyện {text}"
        return f"Quận {text}"
    if text in {"Ba Vì", "Chương Mỹ", "Gia Lâm", "Hoài Đức", "Mê Linh", "Mỹ Đức", "Phú Xuyên", "Phúc Thọ", "Quốc Oai", "Sóc Sơn", "Thanh Oai", "Thanh Trì", "Thường Tín", "Thạch Thất", "Đan Phượng", "Đông Anh"}:
        return f"Huyện {text}"
    if text == "Sơn Tây":
        return "Thị xã Sơn Tây"
    return f"Quận {text}"


def build_street_reference_cache() -> pd.DataFrame:
    STREET_REFERENCE_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    parquet_files = sorted(
        filename
        for filename in list_repo_files(repo_id=HF_STREET_DATASET_REPO, repo_type="dataset")
        if filename.endswith(".parquet")
    )
    if not parquet_files:
        raise FileNotFoundError("No parquet shards found in street-level dataset source.")

    frames: list[pd.DataFrame] = []
    for filename in parquet_files:
        local_path = hf_hub_download(
            repo_id=HF_STREET_DATASET_REPO,
            repo_type="dataset",
            filename=filename,
            local_dir=STREET_REFERENCE_SOURCE_DIR,
        )
        shard = pd.read_parquet(
            local_path,
            columns=[
                "province_name",
                "district_name",
                "ward_name",
                "street_name",
                "price",
                "area",
                "property_type_name",
            ],
        )
        shard = shard[shard["province_name"].isin(["Hà Nội", "Hồ Chí Minh"])].copy()
        if shard.empty:
            continue
        frames.append(shard)

    if not frames:
        raise ValueError("Street-level source returned no Hanoi/HCMC rows.")

    raw = pd.concat(frames, ignore_index=True)
    raw["ward_name"] = raw["ward_name"].fillna("").astype(str).str.strip()
    raw["street_name"] = raw["street_name"].fillna("").astype(str).str.strip()
    raw["district_name"] = raw["district_name"].fillna("").astype(str).str.strip()
    raw["price_num"] = pd.to_numeric(raw["price"], errors="coerce")
    raw["area"] = pd.to_numeric(raw["area"], errors="coerce")
    raw = raw[
        raw["street_name"].ne("")
        & raw["district_name"].ne("")
        & raw["price_num"].gt(0)
        & raw["area"].gt(0)
    ].copy()
    raw["price_per_m2"] = raw["price_num"] / raw["area"]

    aggregated = (
        raw.groupby(["province_name", "district_name", "ward_name", "street_name"])
        .agg(
            listings=("street_name", "count"),
            median_price=("price_num", "median"),
            avg_price_m2=("price_per_m2", "mean"),
            avg_area=("area", "mean"),
            dominant_type=("property_type_name", lambda s: s.mode().iloc[0] if not s.mode().empty else "không rõ"),
        )
        .reset_index()
    )
    aggregated["city"] = aggregated["province_name"].map(normalize_external_city)
    aggregated["district_key"] = [
        district_match_key(str(city), str(district))
        for city, district in zip(aggregated["city"], aggregated["district_name"])
    ]
    display_lookup = district_display_lookup()
    aggregated["district_display"] = [
        display_lookup.get(
            (str(city), str(district_key)),
            fallback_external_district_display(str(city), str(district_name)),
        )
        for city, district_key, district_name in zip(
            aggregated["city"],
            aggregated["district_key"],
            aggregated["district_name"],
        )
    ]
    aggregated["ward_key"] = aggregated["ward_name"].map(ward_match_key)
    aggregated = aggregated[aggregated["district_display"].ne("")].copy()

    district_baseline, ward_baseline = internal_micro_baselines()
    aggregated = aggregated.merge(district_baseline, on=["city", "district_key"], how="left")
    aggregated = aggregated.merge(ward_baseline, on=["city", "district_key", "ward_key"], how="left")
    aggregated = aggregated[aggregated["listings"] >= STREET_REFERENCE_MIN_LISTINGS].copy()
    aggregated = aggregated.sort_values(["city", "district_display", "listings", "avg_price_m2"], ascending=[True, True, False, False])
    STREET_REFERENCE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    aggregated.to_csv(STREET_REFERENCE_CACHE_PATH, index=False)
    return aggregated


@lru_cache(maxsize=1)
def load_street_reference() -> pd.DataFrame:
    if STREET_REFERENCE_CACHE_PATH.exists():
        try:
            cached = pd.read_csv(STREET_REFERENCE_CACHE_PATH)
            if not cached.empty:
                return cached
        except Exception:
            pass
    return build_street_reference_cache()


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


@app.get("/api/ai/status")
def ai_status() -> dict[str, Any]:
    return dict(_ai_runtime_state)


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
    asyncio.create_task(warmup_prediction_runtime())
    if HOSTED_QWEN_ENABLED:
        asyncio.create_task(warmup_hosted_qwen())
    else:
        set_ai_runtime_state("ready", "AI ở chế độ retrieval fallback.", "Ready")
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


def build_decision_focus_filters(payload: FutureRecommendationRequest) -> Filters:
    return Filters(
        city=payload.filters.city or DEFAULT_CITY,
        districts=[payload.district] if payload.district else [],
        property_types=[payload.property_type] if payload.property_type else [],
        price_min=payload.filters.price_min,
        price_max=payload.filters.price_max,
        area_min=payload.filters.area_min,
        area_max=payload.filters.area_max,
        roi_min=payload.filters.roi_min,
        roi_max=payload.filters.roi_max,
    )


def decision_focus_dataframe(df: pd.DataFrame, payload: FutureRecommendationRequest) -> tuple[pd.DataFrame, Filters]:
    focus_filters = build_decision_focus_filters(payload)
    scoped = apply_filters(df, focus_filters)
    if payload.legal_documents:
        legal_scoped = scoped[scoped["Legal Documents"].astype(str) == payload.legal_documents]
        if not legal_scoped.empty:
            scoped = legal_scoped
    if not scoped.empty:
        return scoped, focus_filters

    district_filters = Filters(
        city=payload.filters.city or DEFAULT_CITY,
        districts=[payload.district] if payload.district else [],
    )
    district_scoped = apply_filters(df, district_filters)
    if not district_scoped.empty:
        return district_scoped, district_filters

    city_filters = Filters(city=payload.filters.city or DEFAULT_CITY)
    city_scoped = apply_filters(df, city_filters)
    if not city_scoped.empty:
        return city_scoped, city_filters
    return df, city_filters


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
            "RAG: retrieve tài liệu pháp lý/quy hoạch, rồi dùng Qwen2.5-1.5B-Instruct hosted để diễn đạt ngữ nghĩa nếu khả dụng.",
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
    cache_id = cache_key(payload.model_dump())
    cached = _prediction_cache.get(cache_id)
    if cached:
        return dict(cached)

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
    result = {
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
    _prediction_cache[cache_id] = dict(result)
    return result


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
    cache_id = cache_key(payload.model_dump())
    cached = _what_if_cache.get(cache_id)
    if cached:
        return dict(cached)

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

    result = {
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
    _what_if_cache[cache_id] = dict(result)
    return result


@app.post("/api/recommendation/future")
def future_recommendation(payload: FutureRecommendationRequest) -> dict[str, Any]:
    started = time.perf_counter()
    df = load_data()
    filtered_df, focus_filters = decision_focus_dataframe(df, payload)
    analytics_payload = analytics(focus_filters)
    what_if_payload = what_if(payload)
    risk_label = what_if_payload["asset_prediction"].get("planning_risk_label", "medium")
    question = (
        f"Nen mua them, giu hay ban bot tai san dang mo phong tai {payload.district}, loai hinh {payload.property_type}, "
        f"phap ly {payload.legal_documents}, dien tich {payload.area:.1f} m2 trong {payload.years} nam toi "
        f"voi kich ban tang truong {payload.annual_growth_pct:.1f}%/nam, ROI ky vong {payload.roi_expected * 100:.1f}% "
        f"va rui ro quy hoach {risk_label}? Chi danh gia dung tai san nay va thi truong gan nhat cua no."
    )
    cache_id = cache_key(
        {
            "question": question,
            "filters": payload.filters.model_dump(),
            "focus_filters": focus_filters.model_dump(),
            "top_k": payload.top_k,
            "budget_vnd": payload.budget_vnd,
            "annual_growth_pct": payload.annual_growth_pct,
            "years": payload.years,
            "roi_expected": payload.roi_expected,
            "data_rows": len(filtered_df),
            "prompt_version": "future_focus_v10",
        }
    )
    cached = _future_recommendation_cache.get(cache_id)
    if cached:
        cached = dict(cached)
        cached["retrieval_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return cached
    sources, retrieval_mode = retrieve_context(question, filtered_df, payload.top_k, focus_filters)
    recommendation = None
    model_name = None
    if HOSTED_QWEN_ENABLED:
        recommendation, model_name = call_hosted_qwen_future_recommendation(
            what_if_payload,
            analytics_payload,
            focus_filters,
            sources,
            payload.decision_tab,
        )
    if not recommendation:
        raise HTTPException(
            status_code=503,
            detail=hosted_qwen_failure_detail(),
        )
    recommendation = enrich_future_recommendation(recommendation, what_if_payload, analytics_payload, focus_filters, sources)
    if not future_recommendation_is_usable(recommendation):
        raise HTTPException(
            status_code=502,
            detail="AI trả về khuyến nghị chưa hoàn chỉnh. Hãy thử lại để lấy kết quả đầy đủ.",
        )
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
    recommendation["llm_mode"] = active_llm_mode() if recommendation.get("llm_available") else "fast-retrieval"
    _future_recommendation_cache[cache_id] = dict(recommendation)
    return recommendation


@app.post("/api/recommendation/future/stream")
def future_recommendation_stream(payload: FutureRecommendationRequest) -> StreamingResponse:
    started = time.perf_counter()
    question_template = (
        f"Nen mua them, giu hay ban bot tai san dang mo phong tai {payload.district}, loai hinh {payload.property_type}, "
        f"phap ly {payload.legal_documents}, dien tich {payload.area:.1f} m2 trong {payload.years} nam toi "
        f"voi kich ban tang truong {payload.annual_growth_pct:.1f}%/nam, ROI ky vong {payload.roi_expected * 100:.1f}% "
        f"va rui ro quy hoach {{risk_label}}? Chi danh gia dung tai san nay va thi truong gan nhat cua no."
    )

    def generate():
        yield json.dumps(
            {
                "type": "meta",
                "model": HF_QWEN_MODEL,
                "mode": "hf-qwen-future-recommendation",
                "llm_available": llm_credentials_ready(),
                "llm_mode": active_llm_mode(),
                "status": llm_waiting_status() if llm_credentials_ready() else "error",
            },
            ensure_ascii=False,
        ) + "\n"

        if not HOSTED_QWEN_ENABLED or not llm_credentials_ready():
            yield json.dumps(
                {
                    "type": "error",
                    "detail": hosted_qwen_failure_detail(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        yield json.dumps({"type": "stage", "text": "Đang khởi tạo mô phỏng..."}, ensure_ascii=False) + "\n"
        yield json.dumps({"type": "stage", "text": "Đang tính toán mô phỏng tài chính..."}, ensure_ascii=False) + "\n"
        what_if_payload = what_if(payload)
        risk_label = what_if_payload["asset_prediction"].get("planning_risk_label", "medium")
        question = question_template.format(risk_label=risk_label)
        yield json.dumps(
            {
                "type": "what_if",
                "what_if": what_if_payload,
                "prediction": what_if_payload.get("asset_prediction"),
            },
            ensure_ascii=False,
        ) + "\n"
        yield json.dumps({"type": "stage", "text": "Đang nạp dữ liệu thị trường và kiểm tra cache..."}, ensure_ascii=False) + "\n"
        df = load_data()
        filtered_df, focus_filters = decision_focus_dataframe(df, payload)
        cache_id = cache_key(
            {
                "question": question,
                "filters": payload.filters.model_dump(),
                "focus_filters": focus_filters.model_dump(),
                "top_k": payload.top_k,
                "budget_vnd": payload.budget_vnd,
                "annual_growth_pct": payload.annual_growth_pct,
                "years": payload.years,
                "roi_expected": payload.roi_expected,
                "data_rows": len(filtered_df),
                "prompt_version": "future_focus_v10",
            }
        )

        cached = _future_recommendation_cache.get(cache_id)
        if cached:
            cached = dict(cached)
            cached["retrieval_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
            yield json.dumps({"type": "stage", "text": "Đã có kết quả cache, hiển thị ngay..."}, ensure_ascii=False) + "\n"
            yield json.dumps({"type": "done", **cached}, ensure_ascii=False) + "\n"
            return

        analytics_payload = analytics(focus_filters)
        yield json.dumps({"type": "stage", "text": "Đang truy xuất nguồn và chuẩn bị khuyến nghị AI..."}, ensure_ascii=False) + "\n"
        sources, retrieval_mode = retrieve_context(question, filtered_df, payload.top_k, focus_filters)
        prompt = build_decision_recommendation_prompt(what_if_payload, analytics_payload, focus_filters, sources, payload.decision_tab)
        messages = [
            {
                "role": "system",
                "content": "Bạn là trợ lý phân tích đầu tư bất động sản cho ban điều hành doanh nghiệp. Trả lời 100% bằng tiếng Việt trong mọi nội dung người dùng đọc, súc tích, có căn cứ, giọng điều hành.",
            },
            {"role": "user", "content": prompt},
        ]
        answer_lines: list[str] = []
        current_section: str | None = None
        stage_text = "Đang tổng hợp khuyến nghị từ RAG và mô phỏng..." if HF_FUTURE_STREAM_TRANSPORT == "rag-only" else "Qwen đang sinh khuyến nghị và chart spec..."
        yield json.dumps({"type": "stage", "text": stage_text}, ensure_ascii=False) + "\n"
        stream_interrupted = False
        stream_short_circuited = False
        line_iter = None
        if HF_FUTURE_STREAM_TRANSPORT == "rag-only":
            yield json.dumps(
                {
                    "type": "error",
                    "detail": "Luồng khuyến nghị AI đang bị cấu hình `rag-only`, nên không thể sinh khuyến nghị LLM thật. Hãy chuyển transport sang `completion` hoặc `provider-stream`.",
                },
                ensure_ascii=False,
            ) + "\n"
            return
        if HF_FUTURE_STREAM_TRANSPORT != "provider-stream":
            answer, model_name = call_hosted_qwen_with_deadline(
                messages,
                max_tokens=HF_FUTURE_RECOMMENDATION_MAX_TOKENS,
                stop=["\nEND", "END"],
                deadline_seconds=HF_FUTURE_COMPLETION_DEADLINE_SECONDS,
            )
            if not answer:
                yield json.dumps(
                    {
                        "type": "error",
                        "detail": hosted_qwen_failure_detail() or f"{llm_provider_label()} không trả lời kịp để sinh khuyến nghị đầu tư tương lai.",
                    },
                    ensure_ascii=False,
                ) + "\n"
                return
            for line in answer.splitlines():
                answer_lines.append(line)
                stream_event, current_section = future_stream_event(line, current_section)
                if stream_event:
                    yield json.dumps(stream_event, ensure_ascii=False) + "\n"
        else:
            try:
                line_iter = stream_hosted_qwen_lines(
                    messages,
                    max_tokens=HF_FUTURE_RECOMMENDATION_MAX_TOKENS,
                    stop=["\nEND", "END"],
                    soft_wrap_chars=220,
                )
                for line in line_iter or []:
                    answer_lines.append(line)
                    stream_event, current_section = future_stream_event(line, current_section)
                    if stream_event:
                        yield json.dumps(stream_event, ensure_ascii=False) + "\n"
                    if time.perf_counter() - started >= HF_FUTURE_EARLY_DONE_SECONDS:
                        candidate = parse_future_recommendation_answer("\n".join(answer_lines), sources, HF_QWEN_MODEL, True)
                        candidate = enrich_future_recommendation(candidate, what_if_payload, analytics_payload, focus_filters, sources)
                        if future_recommendation_is_usable(candidate):
                            stream_short_circuited = True
                            close = getattr(line_iter, "close", None)
                            if callable(close):
                                close()
                            break
            except Exception:
                stream_interrupted = True

        final_answer = "\n".join(answer_lines).strip()
        if not final_answer:
            yield json.dumps(
                {
                    "type": "error",
                    "detail": hosted_qwen_failure_detail(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        recommendation = parse_future_recommendation_answer(final_answer, sources, HF_QWEN_MODEL, True)
        recommendation = enrich_future_recommendation(recommendation, what_if_payload, analytics_payload, focus_filters, sources)
        if not future_recommendation_is_usable(recommendation):
            yield json.dumps(
                {
                    "type": "error",
                    "detail": "AI trả về khuyến nghị chưa hoàn chỉnh. Hãy thử lại để lấy đầy đủ Kết luận, Lý do, Rủi ro và Hành động.",
                },
                ensure_ascii=False,
            ) + "\n"
            return
        if stream_interrupted and not future_recommendation_is_usable(recommendation):
            yield json.dumps(
                {
                    "type": "error",
                    "detail": "Qwen bị ngắt trước khi hoàn tất khuyến nghị. Hãy thử lại hoặc tăng PROPERTYVISION_HF_INFERENCE_TIMEOUT_SECONDS.",
                },
                ensure_ascii=False,
            ) + "\n"
            return
        recommendation["retrieval_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
        recommendation["question"] = question
        recommendation["what_if"] = what_if_payload
        recommendation["analytics_snapshot"] = {
            "best_district": analytics_payload.get("kpis", {}).get("best_district"),
            "avg_roi": analytics_payload.get("kpis", {}).get("avg_roi"),
            "risky": analytics_payload.get("risky", [])[:3],
        }
        if recommendation.get("llm_available"):
            recommendation["model"] = HF_QWEN_MODEL
            recommendation["llm_mode"] = active_llm_mode()
        else:
            recommendation["llm_mode"] = "fast-retrieval"
        recommendation["stream_interrupted"] = stream_interrupted
        recommendation["stream_short_circuited"] = stream_short_circuited
        _future_recommendation_cache[cache_id] = dict(recommendation)
        yield json.dumps({"type": "done", **recommendation}, ensure_ascii=False) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


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


def ward_market_documents(df: pd.DataFrame) -> list[dict[str, Any]]:
    scoped = df.copy()
    scoped["ward"] = scoped["Location"].astype(str).str.split(",").str[0].str.strip()
    district_baseline = (
        scoped.groupby("district")
        .agg(
            district_price_m2=("price_per_m2", "mean"),
            district_roi=("ROI", "mean"),
            district_listings=("Location", "count"),
        )
        .reset_index()
    )
    grouped = (
        scoped.groupby(["city", "district", "ward"])
        .agg(
            listings=("Location", "count"),
            avg_price_m2=("price_per_m2", "mean"),
            median_price=("price_vnd", "median"),
            avg_roi=("ROI", "mean"),
            avg_area=("area", "mean"),
            dominant_type=("Type of House", lambda s: s.mode().iloc[0] if not s.mode().empty else "không rõ"),
            dominant_legal=("Legal Documents", lambda s: s.mode().iloc[0] if not s.mode().empty else "không rõ"),
        )
        .reset_index()
        .merge(district_baseline, on="district", how="left")
    )
    grouped = grouped[grouped["ward"].astype(str) != ""]
    docs: list[dict[str, Any]] = []
    for row in grouped.itertuples(index=False):
        premium_vs_district = (
            ((float(row.avg_price_m2) / float(row.district_price_m2)) - 1) * 100
            if float(row.district_price_m2 or 0) > 0
            else 0
        )
        roi_gap = float(row.avg_roi or 0) - float(row.district_roi or 0)
        docs.append(
            {
                "title": f"Micro-market - {row.ward} / {row.district}",
                "content": (
                    f"{row.ward}, {row.district} ({row.city}): {int(row.listings)} tin, "
                    f"giá trung vị {float(row.median_price) / VND_BILLION:.2f} tỷ, "
                    f"giá/m2 {float(row.avg_price_m2) / VND_MILLION:.1f} triệu, "
                    f"ROI {float(row.avg_roi) * 100:.2f}%, diện tích TB {float(row.avg_area):.1f} m2. "
                    f"So với mặt bằng {row.district}, khu này {'cao hơn' if premium_vs_district >= 0 else 'thấp hơn'} "
                    f"{abs(premium_vs_district):.1f}% về giá/m2 và {'cao hơn' if roi_gap >= 0 else 'thấp hơn'} "
                    f"{abs(roi_gap) * 100:.2f} điểm % về ROI. "
                    f"Loại hình nổi bật: {row.dominant_type}. Pháp lý phổ biến: {row.dominant_legal}."
                ),
                "source_name": "PropertyVision ward mart",
                "source_url": "datasets/clean_dataset.csv",
                "district": row.district,
                "city": row.city,
            }
        )
    return docs


def city_shortlist_documents(df: pd.DataFrame) -> list[dict[str, Any]]:
    scoped = df.copy()
    scoped["ward"] = scoped["Location"].astype(str).str.split(",").str[0].str.strip()
    grouped = (
        scoped.groupby(["city", "district", "ward"])
        .agg(
            listings=("Location", "count"),
            avg_price_m2=("price_per_m2", "mean"),
            avg_roi=("ROI", "mean"),
            median_price=("price_vnd", "median"),
        )
        .reset_index()
    )
    docs: list[dict[str, Any]] = []
    for city, city_df in grouped.groupby("city"):
        city_df = city_df.copy()
        city_df["roi_rank"] = city_df["avg_roi"].rank(pct=True)
        city_df["liquidity_rank"] = city_df["listings"].rank(pct=True)
        city_df["price_rank"] = city_df["avg_price_m2"].rank(pct=True, ascending=False)
        city_df["micro_score"] = city_df["roi_rank"] * 0.45 + city_df["liquidity_rank"] * 0.35 + city_df["price_rank"] * 0.20
        shortlist = city_df.sort_values(["micro_score", "listings"], ascending=[False, False]).head(6)
        lines = [
            (
                f"- {row.ward}, {row.district}: {int(row.listings)} tin, "
                f"giá/m2 {float(row.avg_price_m2) / VND_MILLION:.1f} triệu, "
                f"ROI {float(row.avg_roi) * 100:.2f}%, giá trung vị {float(row.median_price) / VND_BILLION:.2f} tỷ."
            )
            for row in shortlist.itertuples(index=False)
        ]
        docs.append(
            {
                "title": f"Shortlist mua chi tiết - {city}",
                "content": (
                    f"Shortlist vi mô theo phường/xã cho {city}, ưu tiên cân bằng ROI, thanh khoản và mặt bằng giá:\n"
                    + "\n".join(lines)
                ),
                "source_name": "PropertyVision micro-market shortlist",
                "source_url": "datasets/clean_dataset.csv",
                "city": city,
            }
        )
    return docs


def street_spotlight_documents(df: pd.DataFrame) -> list[dict[str, Any]]:
    scoped = df[df["Location"].astype(str).str.contains("Phố|Đường", case=False, na=False)].copy()
    if scoped.empty:
        return []
    grouped = (
        scoped.groupby(["city", "district", "Location"])
        .agg(
            listings=("Location", "count"),
            avg_price_m2=("price_per_m2", "mean"),
            avg_roi=("ROI", "mean"),
            median_price=("price_vnd", "median"),
        )
        .reset_index()
    )
    docs: list[dict[str, Any]] = []
    for row in grouped.itertuples(index=False):
        docs.append(
            {
                "title": f"Street spotlight - {row.Location}",
                "content": (
                    f"{row.Location} ({row.city}): {int(row.listings)} tin, "
                    f"giá trung vị {float(row.median_price) / VND_BILLION:.2f} tỷ, "
                    f"giá/m2 {float(row.avg_price_m2) / VND_MILLION:.1f} triệu, "
                    f"ROI {float(row.avg_roi) * 100:.2f}%. Đây là location có tên đường/phố hiện diện trực tiếp trong dataset."
                ),
                "source_name": "PropertyVision street spotlight",
                "source_url": "datasets/clean_dataset.csv",
                "district": row.district,
                "city": row.city,
            }
        )
    return docs


def street_reference_documents() -> list[dict[str, Any]]:
    try:
        street_df = load_street_reference().copy()
    except Exception:
        return []
    if street_df.empty:
        return []

    docs: list[dict[str, Any]] = []
    detailed_rows = (
        street_df.sort_values(["city", "district_display", "listings", "avg_price_m2"], ascending=[True, True, False, False])
        .groupby(["city", "district_display"], group_keys=False)
        .head(STREET_REFERENCE_MAX_DOCS_PER_DISTRICT)
    )

    for row in detailed_rows.itertuples(index=False):
        ward_display = row.ward_name if str(row.ward_name).strip() else "không rõ phường/xã"
        local_roi = float(row.ward_roi) if pd.notna(row.ward_roi) else float(row.district_roi) if pd.notna(row.district_roi) else None
        local_price = float(row.ward_price_m2) if pd.notna(row.ward_price_m2) else float(row.district_price_m2) if pd.notna(row.district_price_m2) else None
        premium_vs_local = (
            ((float(row.avg_price_m2) / local_price) - 1) * 100
            if local_price and local_price > 0
            else None
        )
        roi_text = f"ROI nền khu vực {local_roi * 100:.2f}%." if local_roi is not None else "Chưa có ROI nền khu vực từ dataset nội bộ."
        compare_text = (
            f"So với mặt bằng gần nhất, đường này {'cao hơn' if premium_vs_local >= 0 else 'thấp hơn'} {abs(premium_vs_local):.1f}% về giá/m2."
            if premium_vs_local is not None
            else ""
        )
        docs.append(
            {
                "title": f"Street market - {row.street_name}, {ward_display}, {row.district_display}",
                "content": (
                    f"{row.street_name}, {ward_display}, {row.district_display} ({row.city}): {int(row.listings)} tin street-level, "
                    f"giá trung vị {float(row.median_price) / VND_BILLION:.2f} tỷ, "
                    f"giá/m2 {float(row.avg_price_m2) / VND_MILLION:.1f} triệu, "
                    f"diện tích TB {float(row.avg_area):.1f} m2. "
                    f"Loại hình nổi bật: {row.dominant_type}. "
                    f"{roi_text} {compare_text}".strip()
                ),
                "source_name": "Tinix AI street-level market cache",
                "source_url": HF_STREET_DATASET_CARD_URL,
                "district": row.district_display,
                "city": row.city,
            }
        )

    for (city, district_display), district_rows in street_df.groupby(["city", "district_display"]):
        shortlist = district_rows.sort_values(["listings", "avg_price_m2"], ascending=[False, False]).head(STREET_REFERENCE_MAX_SHORTLIST_PER_DISTRICT)
        lines = []
        for row in shortlist.itertuples(index=False):
            ward_display = row.ward_name if str(row.ward_name).strip() else "không rõ phường/xã"
            roi_text = f", ROI nền {float(row.ward_roi) * 100:.2f}%" if pd.notna(row.ward_roi) else f", ROI quận/huyện {float(row.district_roi) * 100:.2f}%" if pd.notna(row.district_roi) else ""
            lines.append(
                f"- {row.street_name} / {ward_display}: {int(row.listings)} tin, giá/m2 {float(row.avg_price_m2) / VND_MILLION:.1f} triệu, "
                f"giá trung vị {float(row.median_price) / VND_BILLION:.2f} tỷ{roi_text}."
            )
        docs.append(
            {
                "title": f"Street shortlist - {district_display}",
                "content": (
                    f"Các tuyến đường có độ phủ listing tốt tại {district_display}, {city}:\n" + "\n".join(lines)
                ),
                "source_name": "Tinix AI street-level shortlist",
                "source_url": HF_STREET_DATASET_CARD_URL,
                "district": district_display,
                "city": city,
            }
        )
    return docs


def load_rag_documents(df: pd.DataFrame) -> list[dict[str, Any]]:
    seed_planning_and_documents()
    docs = analytics_documents(df)
    docs.extend(ward_market_documents(df))
    docs.extend(city_shortlist_documents(df))
    docs.extend(street_spotlight_documents(df))
    docs.extend(street_reference_documents())
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
_assistant_cache: dict[str, dict[str, Any]] = {}
_prediction_cache: dict[str, dict[str, Any]] = {}
_what_if_cache: dict[str, dict[str, Any]] = {}
_future_recommendation_cache: dict[str, dict[str, Any]] = {}
_ai_runtime_state: dict[str, Any] = {
    "status": "idle",
    "label": "Ready",
    "model": HF_QWEN_MODEL,
    "provider": "Featherless" if LLM_BACKEND in {"featherless-direct", "featherless"} and FEATHERLESS_API_KEY else "Hugging Face",
    "message": "AI sẽ được warm up ngầm khi backend khởi động.",
    "tasks": {
        "assistant": {"status": "idle", "label": "Ready", "message": "Chưa warm."},
        "decision": {"status": "idle", "label": "Ready", "message": "Chưa warm."},
    },
    "updated_at": None,
}


def clear_rag_cache() -> None:
    _rag_cache.clear()
    _assistant_cache.clear()
    _prediction_cache.clear()
    _what_if_cache.clear()
    _future_recommendation_cache.clear()


def set_ai_runtime_state(status: str, message: str, label: str | None = None) -> None:
    _ai_runtime_state.update(
        {
            "status": status,
            "label": label or status.replace("_", " ").title(),
            "model": HF_QWEN_MODEL,
            "provider": llm_provider_label(),
            "message": message,
            "updated_at": pd.Timestamp.utcnow().isoformat(),
        }
    )


def set_ai_task_state(task: str, status: str, message: str, label: str | None = None) -> None:
    tasks = dict(_ai_runtime_state.get("tasks") or {})
    tasks[task] = {
        "status": status,
        "label": label or status.replace("_", " ").title(),
        "message": message,
        "updated_at": pd.Timestamp.utcnow().isoformat(),
    }
    _ai_runtime_state["tasks"] = tasks


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

    normalized_question = normalize_text(question)
    question_focus = extract_district_mentions(question, [str(doc.get("district")) for doc in index["docs"] if doc.get("district")])
    focus_set = set(question_focus)
    if focus_set:
        focused_indices = [doc_idx for doc_idx in doc_indices if index["docs"][int(doc_idx)].get("district") in focus_set]
        if focused_indices:
            doc_indices = focused_indices

    wants_street_level = any(token in normalized_question for token in ("duong", "pho", "street", "tuyen"))
    wants_ward_level = any(token in normalized_question for token in ("phuong", "xa", "ward"))
    if wants_street_level:
        street_indices = [
            doc_idx
            for doc_idx in doc_indices
            if str(index["docs"][int(doc_idx)].get("title") or "").startswith(("Street market -", "Street shortlist -"))
        ]
        if street_indices:
            doc_indices = street_indices
    elif wants_ward_level:
        ward_indices = [
            doc_idx
            for doc_idx in doc_indices
            if str(index["docs"][int(doc_idx)].get("title") or "").startswith("Micro-market -")
        ]
        if ward_indices:
            doc_indices = ward_indices

    def relevance_bonus(doc: dict[str, Any]) -> float:
        title = str(doc.get("title") or "")
        bonus = 0.0
        if wants_street_level and (title.startswith("Street market -") or title.startswith("Street shortlist -")):
            bonus += 0.35
        if wants_ward_level and title.startswith("Micro-market -"):
            bonus += 0.20
        return bonus

    if index["mode"] == "sentence-transformers":
        query = index["embedder"].encode([question], normalize_embeddings=True, show_progress_bar=False)
        candidate_matrix = index["matrix"][doc_indices]
        scores = candidate_matrix @ query[0]
        if focus_set:
            for pos, doc_idx in enumerate(doc_indices):
                doc_district = index["docs"][int(doc_idx)].get("district")
                if doc_district in focus_set:
                    scores[pos] += 0.25
        for pos, doc_idx in enumerate(doc_indices):
            scores[pos] += relevance_bonus(index["docs"][int(doc_idx)])
        ranked_positions = np.argsort(scores)[::-1][: min(top_k, len(doc_indices))]
        ranked = [(doc_indices[int(pos)], float(scores[int(pos)])) for pos in ranked_positions]
    else:
        query = index["embedder"].transform([question])
        candidate_matrix = index["matrix"][doc_indices]
        similarities = cosine_similarity(query, candidate_matrix)[0]
        if focus_set:
            similarities = np.array(
                [
                    float(score + 0.25 if index["docs"][int(doc_idx)].get("district") in focus_set else score)
                    for doc_idx, score in zip(doc_indices, similarities)
                ]
            )
        similarities = np.array(
            [
                float(score + relevance_bonus(index["docs"][int(doc_idx)]))
                for doc_idx, score in zip(doc_indices, similarities)
            ]
        )
        ranked_positions = np.argsort(similarities)[::-1][: min(top_k, len(doc_indices))]
        ranked = [(doc_indices[int(pos)], float(similarities[int(pos)])) for pos in ranked_positions]

    sources: list[dict[str, Any]] = []
    for doc_idx, score in ranked:
        doc = dict(index["docs"][int(doc_idx)])
        doc["score"] = score
        sources.append(doc)
    return sources, index["mode"]


def cache_key(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


_last_llm_error_detail: str | None = None


def set_last_llm_error(detail: str | None) -> None:
    global _last_llm_error_detail
    _last_llm_error_detail = str(detail).strip() if detail else None


def active_llm_mode() -> str:
    if not HOSTED_QWEN_ENABLED:
        return "fast-retrieval"
    if LLM_BACKEND in {"featherless-direct", "featherless"} and FEATHERLESS_API_KEY:
        return "featherless-direct"
    if HF_TOKEN:
        return "hf-hosted"
    return "fast-retrieval"


def llm_waiting_status() -> str:
    mode = active_llm_mode()
    if mode == "featherless-direct":
        return "waiting_featherless"
    if mode == "hf-hosted":
        return "waiting_huggingface"
    return "error"


def llm_credentials_ready() -> bool:
    mode = active_llm_mode()
    if mode == "featherless-direct":
        return bool(FEATHERLESS_API_KEY)
    if mode == "hf-hosted":
        return bool(HF_TOKEN)
    return False


def llm_provider_label() -> str:
    mode = active_llm_mode()
    if mode == "featherless-direct":
        return "Featherless"
    if mode == "hf-hosted":
        return "Hugging Face"
    return "AI provider"


def parse_remote_llm_error(response: requests.Response) -> str:
    detail = ""
    issues_text = ""
    try:
        response.encoding = "utf-8"
        payload = response.json()
        if isinstance(payload, dict):
            error_payload = payload.get("error")
            if isinstance(error_payload, dict):
                detail = str(
                    error_payload.get("message")
                    or error_payload.get("detail")
                    or error_payload.get("error")
                    or ""
                ).strip()
                issues = error_payload.get("issues")
                if issues:
                    issues_text = json.dumps(issues, ensure_ascii=False)
            elif error_payload:
                detail = str(error_payload).strip()
            if not detail:
                detail = str(payload.get("detail") or payload.get("message") or "").strip()
    except Exception:
        detail = ""
    if not detail:
        detail = response.text.strip()

    normalized = detail.lower()
    provider = llm_provider_label()
    if response.status_code in {401, 403} and any(token in normalized for token in ("credit", "credits", "quota", "billing", "balance", "payment", "insufficient")):
        return f"{provider} API credit has been exhausted."
    if response.status_code == 429:
        return f"{provider} API rate limit exceeded. Please retry shortly."
    if response.status_code in {401, 403}:
        return f"{provider} API key was rejected."
    if issues_text:
        return f"{detail or 'Validation error'}: {issues_text}"
    return detail or f"{provider} request failed with HTTP {response.status_code}."


def featherless_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {FEATHERLESS_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": FEATHERLESS_APP_URL,
        "X-Title": FEATHERLESS_APP_TITLE,
    }


def featherless_request_payload(
    messages: list[dict[str, str]],
    max_tokens: int,
    stop: list[str] | None = None,
    stream: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": HF_QWEN_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "top_p": 0.9,
    }
    if stop:
        payload["stop"] = stop
    if stream:
        payload["stream"] = True
    return payload


@lru_cache(maxsize=1)
def hosted_qwen_client() -> InferenceClient | None:
    if not HOSTED_QWEN_ENABLED or active_llm_mode() != "hf-hosted":
        return None
    try:
        return InferenceClient(
            model=HF_QWEN_MODEL,
            provider=HF_INFERENCE_PROVIDER,
            token=HF_TOKEN,
            timeout=HF_INFERENCE_TIMEOUT_SECONDS,
        )
    except Exception:
        return None


def call_featherless_qwen(messages: list[dict[str, str]], max_tokens: int = 450, stop: list[str] | None = None) -> tuple[str | None, str | None]:
    if active_llm_mode() != "featherless-direct" or not FEATHERLESS_API_KEY:
        return None, None
    try:
        response = requests.post(
            FEATHERLESS_BASE_URL,
            headers=featherless_headers(),
            json=featherless_request_payload(messages, max_tokens, stop=stop, stream=False),
            timeout=HF_INFERENCE_TIMEOUT_SECONDS,
        )
        response.encoding = "utf-8"
        if not response.ok:
            detail = parse_remote_llm_error(response)
            set_last_llm_error(detail)
            return None, None
        payload = response.json()
        content = payload.get("choices", [{}])[0].get("message", {}).get("content")
        answer = content.strip() if isinstance(content, str) else None
        if answer:
            set_last_llm_error(None)
            return answer, str(payload.get("model") or HF_QWEN_MODEL)
    except Exception as exc:
        set_last_llm_error(str(exc))
        return None, None
    return None, None


def stream_featherless_qwen(messages: list[dict[str, str]], max_tokens: int = 450, stop: list[str] | None = None):
    if active_llm_mode() != "featherless-direct" or not FEATHERLESS_API_KEY:
        return
    response = None
    try:
        response = requests.post(
            FEATHERLESS_BASE_URL,
            headers=featherless_headers(),
            json=featherless_request_payload(messages, max_tokens, stop=stop, stream=True),
            timeout=HF_INFERENCE_TIMEOUT_SECONDS,
            stream=True,
        )
        if not response.ok:
            detail = parse_remote_llm_error(response)
            set_last_llm_error(detail)
            raise RuntimeError(detail)
        set_last_llm_error(None)
        response.encoding = "utf-8"
        for raw_line in response.iter_lines(decode_unicode=False):
            if not raw_line:
                continue
            if isinstance(raw_line, bytes):
                line = raw_line.decode("utf-8", errors="replace").strip()
            else:
                line = str(raw_line).strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data or data == "[DONE]":
                break
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = payload.get("choices") or []
            if not choices:
                continue
            first_choice = choices[0] or {}
            delta = first_choice.get("delta") or {}
            content = delta.get("content")
            if isinstance(content, str) and content:
                yield content
            if first_choice.get("finish_reason"):
                break
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        detail = _last_llm_error_detail or str(exc) or hosted_qwen_failure_detail()
        set_last_llm_error(detail)
        raise RuntimeError(detail) from exc
    finally:
        if response is not None:
            response.close()


def hosted_qwen_failure_detail() -> str:
    if not HOSTED_QWEN_ENABLED:
        return "Hosted Qwen đang tắt. Hãy bật PROPERTYVISION_USE_HOSTED_QWEN=true và cung cấp API key phù hợp."
    if active_llm_mode() == "featherless-direct" and not FEATHERLESS_API_KEY:
        return "Thiếu FEATHERLESS_API_KEY. Hãy thêm key Featherless vào file .env trước khi chạy backend."
    if active_llm_mode() == "hf-hosted" and not HF_TOKEN:
        return "Thiếu HF_TOKEN. Hãy thêm token vào file .env hoặc biến môi trường trước khi chạy backend."
    return _last_llm_error_detail or f"{llm_provider_label()} is unavailable or timed out. Please retry after the model becomes available."


async def warmup_hosted_qwen() -> None:
    if not HOSTED_QWEN_ENABLED:
        set_ai_runtime_state("ready", "Hosted Qwen đang tắt, hệ thống sẽ dùng retrieval mode.", "Ready")
        set_ai_task_state("assistant", "ready", "Hosted Qwen đang tắt.", "Ready")
        set_ai_task_state("decision", "ready", "Hosted Qwen đang tắt.", "Ready")
        return
    if not llm_credentials_ready():
        detail = hosted_qwen_failure_detail()
        set_ai_runtime_state("error", detail, "Error")
        set_ai_task_state("assistant", "error", detail, "Error")
        set_ai_task_state("decision", "error", detail, "Error")
        return

    set_ai_runtime_state("loading", f"Đang gọi {llm_provider_label()} ngầm để làm nóng model...", "Model loading")
    try:
        assistant_messages = [
            {"role": "system", "content": "Bạn chỉ cần trả lời đúng một câu ngắn: warm."},
            {"role": "user", "content": "warm"},
        ]
        decision_payload = FutureRecommendationRequest(
            district="Quận 1",
            property_type="Nhà mặt tiền",
            legal_documents="Sổ đỏ",
            area=80,
            bedrooms=3,
            toilets=2,
            floors=3,
            roi_expected=0.14,
            budget_vnd=10 * VND_BILLION,
            annual_growth_pct=8.0,
            years=5,
            filters=Filters(city=DEFAULT_CITY),
            top_k=3,
            task="decision_memo",
            decision_tab="whatif",
        )
        decision_what_if = what_if(decision_payload)
        decision_analytics = analytics(decision_payload.filters)
        decision_prompt = build_decision_recommendation_prompt(
            decision_what_if,
            decision_analytics,
            decision_payload.filters,
            [],
            decision_payload.decision_tab,
        )
        decision_messages = [
            {
                "role": "system",
                "content": "Bạn là trợ lý phân tích đầu tư bất động sản cho ban điều hành doanh nghiệp. Trả lời 100% bằng tiếng Việt trong mọi nội dung người dùng đọc, súc tích, có căn cứ, giọng điều hành.",
            },
            {"role": "user", "content": decision_prompt},
        ]

        assistant_task = asyncio.wait_for(asyncio.to_thread(call_hosted_qwen, assistant_messages, 16), timeout=12)
        decision_task = asyncio.wait_for(asyncio.to_thread(call_hosted_qwen, decision_messages, 64), timeout=12)
        assistant_result, decision_result = await asyncio.gather(assistant_task, decision_task, return_exceptions=True)
        if isinstance(assistant_result, Exception):
            assistant_result = (None, None)
        if isinstance(decision_result, Exception):
            decision_result = (None, None)
        assistant_answer, _ = assistant_result
        decision_answer, _ = decision_result
        if assistant_answer:
            set_ai_task_state("assistant", "ready", "Assistant prompt đã được warm.", "Ready")
        else:
            set_ai_task_state("assistant", "error", hosted_qwen_failure_detail(), "Error")
        if decision_answer:
            set_ai_task_state("decision", "ready", "Decision prompt đã được warm.", "Ready")
        else:
            set_ai_task_state("decision", "error", hosted_qwen_failure_detail(), "Error")
        if assistant_answer and decision_answer:
            set_ai_runtime_state("ready", f"{llm_provider_label()} đã sẵn sàng phục vụ cả assistant và decision.", "Ready")
        else:
            set_ai_runtime_state("error", hosted_qwen_failure_detail(), "Error")
    except Exception as exc:
        set_ai_runtime_state("error", f"Warm up thất bại: {exc}", "Error")
        set_ai_task_state("assistant", "error", f"Warm up thất bại: {exc}", "Error")
        set_ai_task_state("decision", "error", f"Warm up thất bại: {exc}", "Error")


async def warmup_prediction_runtime() -> None:
    try:
        await asyncio.to_thread(load_data)
        await asyncio.to_thread(train_model)
    except Exception:
        pass


def call_hosted_qwen(messages: list[dict[str, str]], max_tokens: int = 450, stop: list[str] | None = None) -> tuple[str | None, str | None]:
    if active_llm_mode() == "featherless-direct":
        return call_featherless_qwen(messages, max_tokens=max_tokens, stop=stop)
    client = hosted_qwen_client()
    if client is None:
        return None, None
    try:
        response = client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            stop=stop,
            temperature=0.2,
            top_p=0.9,
        )
        content = getattr(response.choices[0].message, "content", None)
        answer = content.strip() if isinstance(content, str) else None
        if answer:
            set_last_llm_error(None)
            return answer, getattr(response, "model", HF_QWEN_MODEL)
    except Exception as exc:
        set_last_llm_error(str(exc))
        return None, None
    return None, None


def call_hosted_qwen_with_deadline(
    messages: list[dict[str, str]],
    max_tokens: int = 450,
    stop: list[str] | None = None,
    deadline_seconds: float = 12,
) -> tuple[str | None, str | None]:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(call_hosted_qwen, messages, max_tokens, stop)
    try:
        return future.result(timeout=deadline_seconds)
    except FutureTimeoutError:
        future.cancel()
        return None, None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def stream_hosted_qwen(messages: list[dict[str, str]], max_tokens: int = 450, stop: list[str] | None = None):
    if active_llm_mode() == "featherless-direct":
        yield from stream_featherless_qwen(messages, max_tokens=max_tokens, stop=stop)
        return
    client = hosted_qwen_client()
    if client is None:
        return
    stream = None
    try:
        stream = client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            stop=stop,
            stream=True,
            temperature=0.2,
            top_p=0.9,
        )
        for chunk in stream:
            content = getattr(chunk.choices[0].delta, "content", None)
            if content:
                yield content
    except Exception as exc:
        raise RuntimeError(hosted_qwen_failure_detail()) from exc
    finally:
        close = getattr(stream, "close", None)
        if callable(close):
            close()


def stream_hosted_qwen_lines(messages: list[dict[str, str]], max_tokens: int = 450, stop: list[str] | None = None, soft_wrap_chars: int = 120):
    buffer = ""
    stream = stream_hosted_qwen(messages, max_tokens=max_tokens, stop=stop)
    if stream is None:
        return

    for chunk in stream:
        buffer += chunk
        while True:
            if "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    yield line
                continue

            if len(buffer) >= soft_wrap_chars:
                split_at = buffer.rfind(" ", 0, soft_wrap_chars)
                if split_at > 40:
                    line = buffer[:split_at].strip()
                    buffer = buffer[split_at + 1 :]
                    if line:
                        yield line
                    continue
            break

    tail = buffer.strip()
    if tail:
        yield tail


def build_assistant_prompt(
    question: str,
    sources: list[dict[str, Any]],
    focus_districts: list[str],
    filters: Filters,
    task: str = "assistant_question",
) -> str:
    context = "\n\n".join(
        f"[{idx + 1}] {source['title']} - {source['content']} (Nguồn: {source.get('source_name')})"
        for idx, source in enumerate(sources)
    )
    focus_text = ", ".join(focus_districts) if focus_districts else "không nêu đích danh khu vực"
    base_context = f"""
Câu hỏi: {question}

Trọng tâm câu hỏi: {focus_text}

Bối cảnh bộ lọc:
{filters_summary(filters)}

Nguồn tham chiếu:
{context}
""".strip()

    if task == "executive_brief":
        return f"""
Bạn là chuyên viên phân tích đầu tư bất động sản, viết ghi chú điều hành ngắn gọn cho ban lãnh đạo.
Mục tiêu là tóm tắt nhanh, rõ ràng, có thể đưa thẳng vào báo cáo định kỳ.
Nội dung phải bám vào khu vực/city được hỏi, không lan sang khu vực khác nếu không có trong câu hỏi.
Nêu ngắn gọn 3 phần: phát hiện chính, lợi thế/rủi ro, hành động ưu tiên.
Nếu trích nguồn, dùng ký hiệu [1], [2].
Trình bày bằng markdown gọn gàng:
- Dùng tiêu đề rõ ràng cho từng phần.
- Mỗi gạch đầu dòng phải nằm trên một dòng hoàn chỉnh.
- Không viết riêng một dòng chỉ có số thứ tự như `1.` rồi xuống dòng mới giải thích.

{base_context}

Định dạng trả lời:
## Phát hiện chính
- ...

## Lợi thế
- ...

## Rủi ro
- ...

## Hành động
- ...
""".strip()

    if task == "planning_watch":
        return f"""
Bạn là trợ lý giám sát quy hoạch và rủi ro pháp lý.
Chỉ tập trung vào các tín hiệu quy hoạch, pháp lý, thanh khoản và hạn chế triển khai.
Nếu có nhắc đến quận/huyện cụ thể thì chỉ trả lời đúng các khu đó.
Không biến câu trả lời thành khuyến nghị đầu tư chung.
Nếu trích nguồn, dùng ký hiệu [1], [2].
Trình bày bằng markdown gọn gàng, mỗi ý một dòng rõ ràng, không tách số thứ tự sang dòng riêng.

{base_context}

Định dạng trả lời:
## Rủi ro quy hoạch
- ...

## Rủi ro pháp lý
- ...

## Ảnh hưởng thanh khoản
- ...

## Gợi ý kiểm tra tiếp theo
- ...
""".strip()

    return f"""
Bạn là trợ lý phân tích đầu tư bất động sản cho ban điều hành doanh nghiệp.
Hãy trả lời bằng tiếng Việt, giọng điều hành, rõ ý, ngắn gọn, dễ hiểu với CEO.
Ưu tiên ngôn ngữ kinh doanh và đầu tư bất động sản. Tránh thuật ngữ kỹ thuật nếu không thật sự cần.
Phải bám chặt câu hỏi. Nếu câu hỏi có nhắc đến quận/huyện cụ thể thì chỉ trả lời đúng các khu vực đó, không tự chuyển sang khu vực ưu tiên chung.
 Nếu câu hỏi chỉ nêu một khu vực, tuyệt đối không liệt kê thêm khu vực khác ngoài khu vực đó trừ khi người dùng yêu cầu so sánh.
 Nếu nguồn hiện tại có tài liệu vi mô theo phường/xã hoặc location chi tiết hơn trong cùng khu vực, hãy ưu tiên nêu phường/xã/location đó thay vì chỉ dừng ở cấp quận/huyện.
 Nếu người dùng hỏi sâu tới mức tên đường cụ thể mà nguồn hiện tại không có đủ dữ liệu street-level đáng tin cậy, phải nói rõ đang có dữ liệu tốt nhất ở cấp phường/xã hoặc location trong dataset, không được tự bịa tên đường.
 Mọi nhận định quan trọng phải có dẫn chứng số liệu hoặc chỉ dấu định lượng từ nguồn tham chiếu.
 Mỗi gạch đầu dòng phải gắn ít nhất một nguồn theo dạng [1], [2].
 Không được trả lời kiểu chung chung như "nhiều khu vực có tiềm năng" nếu câu hỏi đang hỏi một khu cụ thể.
 Nếu nguồn không đủ để khẳng định, hãy nói rõ "chưa đủ dữ liệu trong nguồn hiện tại" thay vì suy diễn rộng.
Trình bày bằng markdown sạch:
- Không mở đầu bằng "Chào CEO".
- Không dùng danh sách đánh số 1. 2. 3.
- Dùng đúng 4 tiêu đề sau:
## Kết luận điều hành
## Cơ sở nhận định
## Rủi ro cần lưu ý
## Hành động tiếp theo
- Mỗi tiêu đề nên đi kèm 2 đến 4 gạch đầu dòng chi tiết, ngắn vừa phải.
- Với `Cơ sở nhận định`, mỗi gạch đầu dòng phải có ít nhất một số liệu cụ thể như ROI, giá/m2, điểm cơ hội, số lượng tin, mức rủi ro hoặc trạng thái pháp lý nếu nguồn có.
- Với `Rủi ro cần lưu ý`, nêu rõ rủi ro nào đến từ quy hoạch, rủi ro nào đến từ thanh khoản, rủi ro nào đến từ pháp lý; nếu có số liệu thì gắn vào.
- Với `Hành động tiếp theo`, hành động phải bám đúng câu hỏi người dùng vừa hỏi, không nói chung chung.
- Không dùng tiếng Anh nếu không thật sự cần.
- Không viết thêm đoạn kết luận ngoài 4 tiêu đề trên.
- Không dùng `---`, không thêm mục “Tổng quan”, và không đổi tên các tiêu đề.

{base_context}
Định dạng trả lời:
## Kết luận điều hành
- ... [1]

## Cơ sở nhận định
- ... [1]

## Rủi ro cần lưu ý
- ... [1]

## Hành động tiếp theo
- ... [1]
""".strip()


def build_decision_recommendation_prompt(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
    sources: list[dict[str, Any]],
    decision_tab: str,
) -> str:
    kpis = analytics_payload.get("kpis", {})
    risky_rows = analytics_payload.get("risky", [])
    summary = what_if_payload.get("summary", {})
    scenarios = what_if_payload.get("scenarios", [])
    projection = what_if_payload.get("projection", [])
    scenario_text = "; ".join(
        f"{item['name']} {item['terminal_value'] / VND_BILLION:.2f} tỷ"
        for item in scenarios[:3]
    )
    source_context = "; ".join(
        f"{idx + 1}. {source.get('title') or source.get('source_name')}"
        for idx, source in enumerate(sources[:2])
    )
    focus_district = (filters.districts or [what_if_payload.get("input", {}).get("district")])[0]
    risky_text = ", ".join(row["district"] for row in risky_rows[:3]) or str(focus_district or "không có cảnh báo nổi bật")
    if decision_tab == "scenario":
        tab_instruction = "Tập trung giải thích ý nghĩa biểu đồ kịch bản và mốc rủi ro theo năm, không biến thành lời khuyên mua bán quá dài. Chart title nên nhấn mạnh dải kịch bản theo thời gian và khác rõ với tab còn lại."
        chart_title_hint = "Triển vọng giá trị theo kịch bản"
    elif decision_tab == "asset":
        tab_instruction = "Tập trung vào đặc tính tài sản, mức giá, pháp lý và độ phù hợp với danh mục. Chart title nên nhấn mạnh mức hấp dẫn tài sản so với danh mục và khác rõ với tab còn lại."
        chart_title_hint = "Mức hấp dẫn tài sản so với danh mục"
    else:
        tab_instruction = "Tập trung vào quyết định mua thêm, giữ tỷ trọng, bán bớt hoặc tạm dừng giải ngân. Chart title nên nhấn mạnh mô phỏng tài chính và tác động của vốn/tăng trưởng."
        chart_title_hint = "Mô phỏng tài chính theo vốn và tăng trưởng"

    asset_summary = (
        f"Tài sản mô phỏng: {what_if_payload['input'].get('district')} | "
        f"{what_if_payload['input'].get('property_type')} | "
        f"pháp lý {what_if_payload['input'].get('legal_documents')} | "
        f"diện tích {what_if_payload['input'].get('area')} m2."
    )
    assumption_summary = (
        f"Giả định đầu tư: ngân sách {what_if_payload['input']['budget_vnd'] / VND_BILLION:.2f} tỷ | "
        f"tăng trưởng {what_if_payload['input']['annual_growth_pct']:.1f}%/năm | "
        f"nắm giữ {what_if_payload['input']['years']} năm | "
        f"ROI kỳ vọng {what_if_payload['input']['roi_expected'] * 100:.1f}%."
    )
    result_summary = (
        f"Kết quả mô phỏng: giá trị tương lai {summary.get('future_value', 0) / VND_BILLION:.2f} tỷ | "
        f"lợi nhuận vốn {summary.get('capital_gain', 0) / VND_BILLION:.2f} tỷ | "
        f"ROI tích lũy {summary.get('cumulative_roi_pct', 0):.2f}% | "
        f"rủi ro quy hoạch {what_if_payload['asset_prediction'].get('planning_risk_label', 'unknown')}."
    )

    return f"""
Viết khuyến nghị đầu tư BĐS bằng tiếng Việt, tối đa 150 từ, đúng format, không markdown đậm.
Chỉ được bám vào đúng Thông tin tài sản và Giả định đầu tư đang có trên cùng màn hình mô phỏng. Không mở rộng sang tài sản khác, khu vực khác, hay giả định khác nếu người dùng không chọn ở trang này.
Không được trả lời kiểu chung chung như "hợp lý", "có tiềm năng", "nên cân nhắc" nếu chưa nêu rõ tài sản nào, giả định nào và kết quả nào.
Nếu thiếu một trong các thông tin bắt buộc bên dưới thì phải nói rõ chưa đủ dữ liệu thay vì suy diễn.
BẮT BUỘC PHẢI NHẮC LẠI:
{asset_summary}
{assumption_summary}
{result_summary}
Ngữ cảnh bổ sung: bộ lọc {filters_summary(filters)}; khu vực tham chiếu {focus_district or 'N/A'}; cảnh báo {risky_text}; kịch bản {scenario_text or 'không có'}; nguồn {source_context or 'BI mart'}.
{tab_instruction}
Yêu cầu trọng tâm: phần khuyến nghị phải tập trung đúng tài sản đang mô phỏng ở trên, không được nói như một nhận định thị trường chung.

KET_LUAN: 1 câu.
Kết luận phải nêu rõ ít nhất 2 trong 4 yếu tố: khu vực, loại hình, pháp lý, diện tích; và phải chạm một trong các số: ROI kỳ vọng, giá trị tương lai, ROI tích lũy, tăng trưởng, nắm giữ.
LY_DO:
- 2 ý ngắn.
Mỗi ý phải nhắc ít nhất một số liệu hoặc chi tiết từ tài sản/giả định.
RUI_RO:
- Xấu: ...
- Cơ sở: ...
- Lạc quan: ...
Mỗi dòng rủi ro phải gắn với tài sản hoặc kịch bản đang mô phỏng, không dùng câu cảnh báo chung chung.
GOI_Y:
- 2 hành động ngắn.
Hành động phải nói rõ nên mua thêm, giữ, bán bớt hay tạm dừng giải ngân trong bối cảnh tài sản này.
CO_SO:
- 2 căn cứ ngắn.
Mỗi căn cứ phải chứa một số liệu cụ thể từ mô phỏng hoặc bộ lọc.
END
""".strip()


def parse_spec_block(body: str) -> dict[str, Any]:
    spec: dict[str, Any] = {}
    for raw_line in body.splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        spec[key] = value
    if "series" in spec:
        spec["series"] = [item.strip() for item in str(spec["series"]).split(",") if item.strip()]
    return spec


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
    chart_spec = {
        "chart_type": "line",
        "title": "Triển vọng giá trị theo kịch bản",
        "caption": "Biểu đồ line giúp so sánh rủi ro theo thời gian và nhìn nhanh mốc nào bắt đầu tách pha.",
        "insight": "Đường cơ sở là trọng tâm, hai đường xấu và tích cực cho thấy biên an toàn của chiến lược.",
        "x_key": "calendar_year",
        "series": ["pessimistic", "base", "optimistic"],
        "reference_line": "budget_vnd",
    }
    return {
        "answer": action,
        "why": (
            f"Bộ lọc {filters_summary(filters)} cho thấy khu vực ưu tiên là {best_district or 'chưa xác định'}, "
            f"với ROI tích lũy kịch bản cơ sở khoảng {cumulative_roi:.2f}%."
        ),
        "risks": risks,
        "suggestion": action,
        "basis": basis,
        "chart_spec": chart_spec,
        "chart_caption": chart_spec["caption"],
        "sources": sources,
        "model": "future-retrieval-fallback",
        "mode": f"{retrieval_mode}-fallback",
        "llm_available": False,
    }


FUTURE_SECTION_ALIASES = {
    "ACTION": "KET_LUAN",
    "KET_LUAN": "KET_LUAN",
    "KET LUAN": "KET_LUAN",
    "KẾT LUẬN": "KET_LUAN",
    "KẾT_LUẬN": "KET_LUAN",
    "KẾT LUẬN ĐẦU TƯ": "KET_LUAN",
    "WHY": "LY_DO",
    "LY_DO": "LY_DO",
    "LY DO": "LY_DO",
    "LÝ DO": "LY_DO",
    "LÝ_DO": "LY_DO",
    "RISKS": "RUI_RO",
    "RUI_RO": "RUI_RO",
    "RUI RO": "RUI_RO",
    "RỦI RO": "RUI_RO",
    "RỦI_RO": "RUI_RO",
    "SUGGESTION": "GOI_Y",
    "GOI_Y": "GOI_Y",
    "GOI Y": "GOI_Y",
    "GỢI Ý": "GOI_Y",
    "GỢI_Ý": "GOI_Y",
    "HÀNH ĐỘNG": "GOI_Y",
    "BASIS": "CO_SO",
    "CO_SO": "CO_SO",
    "CO SO": "CO_SO",
    "CƠ SỞ": "CO_SO",
    "CƠ_SỞ": "CO_SO",
    "CHART_SPEC": "CHART_SPEC",
    "CHART SPEC": "CHART_SPEC",
    "CHARTSPEC": "CHART_SPEC",
}

FUTURE_CHART_SPEC_KEYS = {
    "CHART_SPEC",
    "CHART SPEC",
    "CHARTSPEC",
    "chart_type",
    "title",
    "caption",
    "insight",
    "x_key",
    "series",
    "reference_line",
}

FUTURE_USER_SECTION_KEYS = {
    "KET_LUAN",
    "LY_DO",
    "RUI_RO",
    "GOI_Y",
    "CO_SO",
}


def canonical_future_section(label: str) -> str | None:
    normalized = re.sub(r"\s+", " ", str(label).strip().upper().replace("_", " "))
    compact = normalized.replace(" ", "_")
    return FUTURE_SECTION_ALIASES.get(str(label).strip().upper()) or FUTURE_SECTION_ALIASES.get(normalized) or FUTURE_SECTION_ALIASES.get(compact)


def future_section_from_label(label: str, rest: str = "", current_section: str | None = None) -> str | None:
    raw = str(label or "").strip()
    upper = raw.upper()
    compact = re.sub(r"\s+", "_", upper.replace("_", " "))
    section = canonical_future_section(raw)
    if not section:
        return None

    code_labels = {
        "ACTION",
        "WHY",
        "RISKS",
        "SUGGESTION",
        "BASIS",
        "KET_LUAN",
        "LY_DO",
        "RUI_RO",
        "GOI_Y",
        "CO_SO",
        "CHART_SPEC",
        "CHART SPEC",
        "CHARTSPEC",
    }
    heading_labels = {
        "KẾT LUẬN",
        "KẾT LUẬN ĐẦU TƯ",
        "LÝ DO",
        "RỦI RO",
        "RỦI RO CẦN NÊU",
        "GỢI Ý",
        "HÀNH ĐỘNG",
        "CƠ SỞ ĐƯA RA KHUYẾN NGHỊ",
    }
    if upper in code_labels or compact in code_labels:
        return section
    if not str(rest or "").strip() or upper in heading_labels:
        return section
    if current_section:
        return None
    return section


def is_future_chart_spec_line(value: str) -> bool:
    line = str(value or "").strip().lstrip("- ").strip()
    line = re.sub(r"^\*+|\*+$", "", line).strip()
    if not line:
        return False
    key_match = re.match(r"^([A-Za-z_ ]+)\s*:", line)
    if key_match:
        key = key_match.group(1).strip()
        return key in FUTURE_CHART_SPEC_KEYS or key.upper() in FUTURE_CHART_SPEC_KEYS
    return line.upper() in {"CHART_SPEC", "CHART SPEC", "CHARTSPEC"}


def append_future_section_text(current_text: str, next_line: str) -> str:
    cleaned = clean_future_user_text(next_line)
    if not cleaned:
        return current_text.strip()
    return f"{current_text}\n{cleaned}".strip()


def clean_future_user_text(value: str) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    replacements = [
        (r"\bACTION\b", "Kết luận"),
        (r"\bWHY\b", "Lý do"),
        (r"\bRISKS\b", "Rủi ro"),
        (r"\bSUGGESTION\b", "Gợi ý"),
        (r"\bBASIS\b", "Cơ sở"),
        (r"\bbuy more\b", "mua thêm"),
        (r"\bbuy\b", "mua"),
        (r"\bhold\b", "giữ"),
        (r"\bsell\b", "bán"),
        (r"\bgrowth\b", "tăng trưởng"),
        (r"\bterminal value\b", "giá trị cuối kỳ"),
        (r"\bpayback period\b", "thời gian hoàn vốn"),
        (r"\bcash yield\b", "dòng tiền sinh lời"),
    ]
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^\s*#{1,6}\s*", "", line).strip()
        if not line or re.fullmatch(r"[-*_ ]+", line):
            continue
        if "*" in line and re.fullmatch(r"\*+\s*[A-Za-zÀ-ỹ_ ]{1,4}\s*", line):
            continue
        if is_future_chart_spec_line(line):
            continue

        labeled = re.match(r"^(?:\*\*)?([A-Za-zÀ-ỹ_ ]+)(?:\*\*)?\s*:\s*(.*)$", line)
        if labeled:
            label = labeled.group(1).strip()
            normalized_label = re.sub(r"\s+", " ", label.upper().replace("_", " ")).strip()
            compact_label = normalized_label.replace(" ", "_")
            strip_inline_label = normalized_label in {
                "ACTION",
                "WHY",
                "RISKS",
                "SUGGESTION",
                "BASIS",
                "KET LUAN",
                "LY DO",
                "RUI RO",
                "GOI Y",
                "CO SO",
                "KẾT LUẬN",
                "LÝ DO",
                "RỦI RO CẦN NÊU",
                "HÀNH ĐỘNG",
                "CƠ SỞ ĐƯA RA KHUYẾN NGHỊ",
            } or compact_label in {"KET_LUAN", "LY_DO", "RUI_RO", "GOI_Y", "CO_SO"}
            section = future_section_from_label(label, labeled.group(2)) if strip_inline_label else None
            if section == "CHART_SPEC":
                continue
            if section in FUTURE_USER_SECTION_KEYS and strip_inline_label:
                line = labeled.group(2).strip()
                if not line:
                    continue

        line = line.replace("**", "").strip()
        for pattern, replacement in replacements:
            line = re.sub(pattern, replacement, line, flags=re.I)
        line = re.sub(r"\s{2,}", " ", line).strip()
        if line:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def future_stream_event(line: str, current_section: str | None) -> tuple[dict[str, Any] | None, str | None]:
    cleaned = str(line or "").strip()
    if not cleaned:
        return None, current_section
    if cleaned.upper() == "END":
        return None, current_section

    if is_future_chart_spec_line(cleaned):
        if re.match(r"^(?:\*\*)?\s*(CHART_SPEC|CHART SPEC|CHARTSPEC)(?:\*\*)?\s*:?\s*", cleaned.lstrip("- ").strip(), flags=re.I):
            return None, "CHART_SPEC"
        return None, current_section

    match = re.match(r"^(?:\*\*)?([A-Za-zÀ-ỹ_ ]+)(?:\*\*)?\s*:\s*(.*)$", cleaned)
    if match:
        rest = clean_future_user_text(match.group(2).strip())
        section = future_section_from_label(match.group(1), rest, current_section)
        if section == "CHART_SPEC":
            return None, "CHART_SPEC"
        if section:
            if not rest:
                return None, section
            target = {
                "KET_LUAN": "answer",
                "LY_DO": "why",
                "RUI_RO": "risks",
                "GOI_Y": "suggestion",
                "CO_SO": "basis",
            }.get(section, "answer")
            return {"type": "line", "section": target, "text": rest}, section

    if current_section == "CHART_SPEC":
        return None, current_section

    text = clean_future_user_text(cleaned)
    if not text:
        return None, current_section
    target = {
        "KET_LUAN": "answer",
        "LY_DO": "why",
        "RUI_RO": "risks",
        "GOI_Y": "suggestion",
        "CO_SO": "basis",
    }.get(current_section or "KET_LUAN", "answer")
    return {"type": "line", "section": target, "text": text}, current_section


def parse_future_recommendation_answer(
    answer: str,
    sources: list[dict[str, Any]],
    model_name: str | None,
    llm_available: bool,
    mode: str = "hf-qwen-future-recommendation",
) -> dict[str, Any]:
    sections = {"KET_LUAN": "", "LY_DO": "", "RUI_RO": "", "GOI_Y": "", "CO_SO": "", "CHART_SPEC": ""}
    current = None
    for raw_line in answer.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.upper() == "END":
            break
        if is_future_chart_spec_line(line):
            if re.match(r"^(?:\*\*)?\s*(CHART_SPEC|CHART SPEC|CHARTSPEC)(?:\*\*)?\s*:?\s*", line.lstrip("- ").strip(), flags=re.I):
                current = "CHART_SPEC"
            elif current == "CHART_SPEC":
                sections["CHART_SPEC"] = f"{sections['CHART_SPEC']}\n{line}".strip()
            continue
        matched = re.match(r"^(?:\*\*)?([A-Za-zÀ-ỹ_ ]+)(?:\*\*)?\s*:\s*(.*)$", line)
        canonical = future_section_from_label(matched.group(1), matched.group(2), current) if matched else None
        if canonical:
            current = canonical
            rest = matched.group(2).strip() if canonical == "CHART_SPEC" else clean_future_user_text(matched.group(2).strip())
            if rest:
                sections[canonical] = f"{sections[canonical]}\n{rest}".strip()
        elif current:
            if current == "CHART_SPEC":
                sections[current] = f"{sections[current]}\n{line}".strip()
            else:
                sections[current] = append_future_section_text(sections[current], line)

    risks = [clean_future_user_text(item.strip("- ").strip()) for item in sections["RUI_RO"].splitlines() if item.strip()]
    basis = [clean_future_user_text(item.strip("- ").strip()) for item in sections["CO_SO"].splitlines() if item.strip()]
    chart_spec = parse_spec_block(sections["CHART_SPEC"])
    if not chart_spec:
        chart_spec = {
            "chart_type": "line",
            "title": "Triển vọng giá trị theo kịch bản",
            "caption": "So sánh ba kịch bản xấu, cơ sở và tích cực theo từng năm.",
            "insight": "Biểu đồ cho thấy chênh lệch rủi ro tăng dần theo thời gian nắm giữ.",
            "x_key": "calendar_year",
            "series": ["pessimistic", "base", "optimistic"],
            "reference_line": "budget_vnd",
        }
    parsed_any_section = any(sections[key].strip() for key in ("KET_LUAN", "LY_DO", "RUI_RO", "GOI_Y", "CO_SO"))
    answer_text = sections["KET_LUAN"] if sections["KET_LUAN"].strip() else ("" if parsed_any_section else answer)

    return {
        "answer": clean_future_user_text(answer_text),
        "why": clean_future_user_text(sections["LY_DO"]),
        "risks": risks,
        "suggestion": clean_future_user_text(sections["GOI_Y"]),
        "basis": basis,
        "chart_spec": chart_spec,
        "chart_caption": chart_spec.get("caption") or chart_spec.get("insight") or "",
        "sources": sources,
        "model": model_name or HF_QWEN_MODEL,
        "mode": mode,
        "llm_available": llm_available,
    }


def future_recommendation_is_usable(recommendation: dict[str, Any]) -> bool:
    return bool(
        str(recommendation.get("answer") or "").strip()
        and (
            str(recommendation.get("why") or "").strip()
            or str(recommendation.get("suggestion") or "").strip()
            or len(recommendation.get("risks") or []) >= 1
        )
    )


def future_recommendation_basis_from_data(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
    sources: list[dict[str, Any]],
) -> list[str]:
    summary = what_if_payload.get("summary", {})
    focus_district = (filters.districts or [None])[0]
    asset = what_if_payload.get("input", {})
    source_titles = ", ".join(str(source.get("title") or source.get("source_name") or "nguồn RAG") for source in sources[:2])
    basis = [
        f"Tài sản {asset.get('district') or focus_district or 'khu vực đang mô phỏng'} - {asset.get('property_type') or 'chưa rõ loại hình'} - pháp lý {asset.get('legal_documents') or 'chưa rõ'} - {float(asset.get('area') or 0):.1f} m2.",
        f"Mô phỏng {what_if_payload.get('input', {}).get('years', 0)} năm cho ROI tích lũy khoảng {float(summary.get('cumulative_roi_pct') or 0):.2f}% với ROI kỳ vọng {float(asset.get('roi_expected') or 0) * 100:.1f}%.",
        f"Giá trị tương lai ước tính {float(summary.get('future_value') or 0) / VND_BILLION:.2f} tỷ, ngân sách {float(asset.get('budget_vnd') or 0) / VND_BILLION:.2f} tỷ.",
        f"Bộ lọc và nguồn tham chiếu RAG: {filters_summary(filters)}; {source_titles or 'dữ liệu thị trường nội bộ'}."
    ]
    return basis


def future_recommendation_risks_from_data(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
) -> list[str]:
    scenarios = what_if_payload.get("scenarios", [])
    risky_rows = analytics_payload.get("risky", [])[:2]
    risks: list[str] = []
    for item in scenarios[:3]:
        name = str(item.get("name") or "Kịch bản")
        terminal_value = float(item.get("terminal_value") or 0)
        capital_gain = float(item.get("capital_gain") or 0)
        risks.append(
            f"{name}: giá trị cuối kỳ khoảng {terminal_value / VND_BILLION:.2f} tỷ, lợi nhuận vốn {capital_gain / VND_BILLION:.2f} tỷ nên cần kiểm soát biến động dòng tiền."
        )
    for row in risky_rows:
        district = row.get("district") or "khu vực rủi ro"
        avg_roi = float(row.get("avg_roi") or 0)
        risks.append(
            f"{district}: ROI bình quân {avg_roi:.2f}% và đang nằm trong nhóm cần theo dõi thêm về thanh khoản hoặc quy hoạch."
        )
    return risks[:4]


def future_recommendation_why_from_data(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
) -> str:
    summary = what_if_payload.get("summary", {})
    focus_district = (filters.districts or [None])[0]
    asset = what_if_payload.get("input", {})
    return " ".join(
        [
            f"Tài sản tại {asset.get('district') or focus_district or 'khu vực đang mô phỏng'} ({asset.get('property_type') or 'chưa rõ loại hình'}, pháp lý {asset.get('legal_documents') or 'chưa rõ'}, {float(asset.get('area') or 0):.1f} m2) được mô phỏng trong {what_if_payload.get('input', {}).get('years', 0)} năm.",
            f"Giá trị tương lai khoảng {float(summary.get('future_value') or 0) / VND_BILLION:.2f} tỷ và ROI tích lũy ước tính {float(summary.get('cumulative_roi_pct') or 0):.2f}% với ROI kỳ vọng {float(asset.get('roi_expected') or 0) * 100:.1f}%.",
            f"Khuyến nghị này chỉ đọc theo thị trường gần nhất của {focus_district or 'tài sản đang mô phỏng'} và bối cảnh {filters_summary(filters)}.",
        ]
    ).strip()


def future_recommendation_suggestion_from_data(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
) -> str:
    asset = what_if_payload.get("input", {})
    risk_label = str(what_if_payload.get("asset_prediction", {}).get("planning_risk_label") or "medium")
    focus_district = (filters.districts or [None])[0] or "khu vực đang mô phỏng"
    action = "giữ tỷ trọng và giải ngân chọn lọc" if risk_label == "medium" else "có thể mở rộng giải ngân có kiểm soát" if risk_label == "low" else "tạm ưu tiên thẩm định trước khi tăng tỷ trọng"
    return (
        f"Ưu tiên {action} với tài sản tại {asset.get('district') or focus_district}. "
        f"Trước khi ra quyết định cuối cùng, cần kiểm tra thêm pháp lý {asset.get('legal_documents') or 'chưa rõ'}, quy hoạch và tốc độ hấp thụ của tài sản mục tiêu."
    )


def future_recommendation_answer_from_data(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
) -> str:
    summary = what_if_payload.get("summary", {})
    asset = what_if_payload.get("input", {})
    district = asset.get("district") or (filters.districts or [None])[0] or "tài sản đang mô phỏng"
    property_type = asset.get("property_type") or "tài sản"
    legal_documents = asset.get("legal_documents") or "chưa rõ pháp lý"
    area = float(asset.get("area") or 0)
    roi_expected = float(asset.get("roi_expected") or 0) * 100
    future_value = float(summary.get("future_value") or 0) / VND_BILLION
    cumulative_roi = float(summary.get("cumulative_roi_pct") or 0)
    years = int(what_if_payload.get("input", {}).get("years", 0) or 0)
    risk_label = str(what_if_payload.get("asset_prediction", {}).get("planning_risk_label") or "medium")

    if cumulative_roi < 15 or risk_label == "high":
        return (
            f"Tài sản tại {district} ({property_type}, pháp lý {legal_documents}, {area:.1f} m2) chưa đủ an toàn để tăng tỷ trọng mạnh; "
            f"nên thẩm định thêm vì ROI kỳ vọng {roi_expected:.1f}% trong {years} năm chỉ chuyển hóa thành ROI tích lũy {cumulative_roi:.2f}% với giá trị tương lai {future_value:.2f} tỷ."
        )
    if risk_label == "low":
        return (
            f"Tài sản tại {district} ({property_type}, pháp lý {legal_documents}, {area:.1f} m2) có thể mua thêm có kiểm soát vì ROI kỳ vọng {roi_expected:.1f}% trong {years} năm "
            f"đi cùng giá trị tương lai {future_value:.2f} tỷ và ROI tích lũy {cumulative_roi:.2f}%."
        )
    return (
        f"Tài sản tại {district} ({property_type}, pháp lý {legal_documents}, {area:.1f} m2) phù hợp để giữ hoặc giải ngân chọn lọc vì ROI kỳ vọng {roi_expected:.1f}% trong {years} năm "
        f"đem lại giá trị tương lai {future_value:.2f} tỷ và ROI tích lũy {cumulative_roi:.2f}%."
    )


def future_recommendation_is_specific(
    text: str,
    what_if_payload: dict[str, Any],
    filters: Filters,
) -> bool:
    normalized = clean_future_user_text(text).lower()
    if not normalized:
        return False
    asset = what_if_payload.get("input", {})
    signals = 0
    for value in (
        str(asset.get("district") or (filters.districts or [None])[0] or "").lower(),
        str(asset.get("property_type") or "").lower(),
        str(asset.get("legal_documents") or "").lower(),
    ):
        if value and value in normalized:
            signals += 1

    numeric_signals = 0
    for value in (
        f"{float(asset.get('roi_expected') or 0) * 100:.1f}",
        f"{float(asset.get('area') or 0):.1f}",
        f"{float(what_if_payload.get('summary', {}).get('future_value') or 0) / VND_BILLION:.2f}",
        f"{float(what_if_payload.get('summary', {}).get('cumulative_roi_pct') or 0):.2f}",
        str(int(what_if_payload.get("input", {}).get("years", 0) or 0)),
    ):
        if value and value in normalized:
            numeric_signals += 1

    return signals >= 2 and numeric_signals >= 2


def payload_or_filters_city(filters: Filters) -> str:
    return filters.city or DEFAULT_CITY


def enrich_future_recommendation(
    recommendation: dict[str, Any],
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    result = dict(recommendation)
    answer = str(result.get("answer") or "").strip()
    why = str(result.get("why") or "").strip()
    suggestion = str(result.get("suggestion") or "").strip()
    risks = [item for item in (result.get("risks") or []) if str(item).strip()]
    basis = [item for item in (result.get("basis") or []) if str(item).strip()]

    if not answer and suggestion:
        answer = suggestion
    if not answer and why:
        answer = why.split(". ")[0].strip()
    if not future_recommendation_is_specific(answer, what_if_payload, filters):
        answer = future_recommendation_answer_from_data(what_if_payload, analytics_payload, filters)
    if not why:
        why = future_recommendation_why_from_data(what_if_payload, analytics_payload, filters)
    if not suggestion:
        suggestion = future_recommendation_suggestion_from_data(what_if_payload, analytics_payload, filters)
    if len(risks) < 2:
        risks = (risks + future_recommendation_risks_from_data(what_if_payload, analytics_payload))[:4]
    if not basis:
        basis = future_recommendation_basis_from_data(what_if_payload, analytics_payload, filters, sources)

    result["answer"] = clean_future_user_text(answer)
    result["why"] = clean_future_user_text(why)
    result["suggestion"] = clean_future_user_text(suggestion)
    result["risks"] = [clean_future_user_text(item) for item in risks if clean_future_user_text(item)]
    result["basis"] = [clean_future_user_text(item) for item in basis if clean_future_user_text(item)]
    return result


def call_hosted_qwen_future_recommendation(
    what_if_payload: dict[str, Any],
    analytics_payload: dict[str, Any],
    filters: Filters,
    sources: list[dict[str, Any]],
    decision_tab: str = "whatif",
) -> tuple[dict[str, Any] | None, str | None]:
    prompt = build_decision_recommendation_prompt(what_if_payload, analytics_payload, filters, sources, decision_tab)

    messages = [
        {
            "role": "system",
            "content": "Bạn là trợ lý phân tích đầu tư bất động sản cho ban điều hành doanh nghiệp. Trả lời 100% bằng tiếng Việt trong mọi nội dung người dùng đọc, súc tích, có căn cứ, giọng điều hành.",
        },
        {"role": "user", "content": prompt},
    ]

    answer, model_name = call_hosted_qwen(messages, max_tokens=HF_FUTURE_RECOMMENDATION_MAX_TOKENS, stop=["\nEND", "END"])
    if not answer:
        return None, None

    result = parse_future_recommendation_answer(answer, sources, model_name or HF_QWEN_MODEL, True)
    result = enrich_future_recommendation(result, what_if_payload, analytics_payload, filters, sources)
    return result, model_name or HF_QWEN_MODEL


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

    cache_id = cache_key(
        {
            "question": payload.question,
            "filters": payload.filters.model_dump(),
            "top_k": payload.top_k,
            "data_rows": len(df),
            "prompt_version": "assistant_vi_v2",
        }
    )
    cached = _assistant_cache.get(cache_id)
    if cached:
        cached = dict(cached)
        cached["retrieval_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return cached

    sources, retrieval_mode = retrieve_context(payload.question, df, payload.top_k, payload.filters)
    answer = None
    model_name = None
    if HOSTED_QWEN_ENABLED:
        focus_districts = extract_district_mentions(payload.question, [str(d) for d in df["district"].dropna().astype(str).unique().tolist()])
        prompt = build_assistant_prompt(payload.question, sources, focus_districts, payload.filters, payload.task)
        answer, model_name = call_hosted_qwen(
            [
            {
                "role": "system",
                "content": "Bạn là trợ lý phân tích đầu tư bất động sản cho ban điều hành doanh nghiệp. Trả lời 100% bằng tiếng Việt trong mọi nội dung người dùng đọc, súc tích, có căn cứ, giọng điều hành.",
            },
                {"role": "user", "content": prompt},
            ],
            max_tokens=520,
        )
    if not answer:
        raise HTTPException(
            status_code=503,
            detail=hosted_qwen_failure_detail(),
        )

    result = {
        "answer": answer,
        "sources": sources,
        "model": model_name or "retrieval-fallback",
        "mode": "hf-qwen",
        "llm_available": True,
        "retrieved_context": sources,
        "retrieval_time_ms": round((time.perf_counter() - started) * 1000, 2),
        "llm_mode": active_llm_mode() if HOSTED_QWEN_ENABLED else "fast-retrieval",
    }
    _assistant_cache[cache_id] = dict(result)
    return result


@app.post("/api/assistant/stream")
def assistant_stream(payload: AssistantRequest) -> StreamingResponse:
    df = apply_filters(load_data(), payload.filters)
    if df.empty:
        raise HTTPException(status_code=404, detail="Không có dữ liệu phù hợp với bộ lọc hiện tại.")

    sources, _ = retrieve_context(payload.question, df, payload.top_k, payload.filters)
    focus_districts = extract_district_mentions(payload.question, [str(d) for d in df["district"].dropna().astype(str).unique().tolist()])
    prompt = build_assistant_prompt(payload.question, sources, focus_districts, payload.filters, payload.task)
    messages = [
        {
            "role": "system",
            "content": "Bạn là trợ lý phân tích đầu tư bất động sản cho ban điều hành doanh nghiệp. Trả lời súc tích, có căn cứ, giọng điều hành.",
        },
        {"role": "user", "content": prompt},
    ]

    def generate():
        yield json.dumps(
            {
                "type": "meta",
                "model": HF_QWEN_MODEL,
                "mode": "hf-qwen",
                "llm_available": llm_credentials_ready(),
                "llm_mode": active_llm_mode(),
                "status": llm_waiting_status() if llm_credentials_ready() else "error",
                "sources": sources,
            },
            ensure_ascii=False,
        ) + "\n"

        if not HOSTED_QWEN_ENABLED or not llm_credentials_ready():
            yield json.dumps(
                {
                    "type": "error",
                    "detail": hosted_qwen_failure_detail(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        answer_lines: list[str] = []
        try:
            for line in stream_hosted_qwen_lines(messages, max_tokens=520) or []:
                answer_lines.append(line)
                yield json.dumps({"type": "line", "text": line}, ensure_ascii=False) + "\n"
        except Exception:
            yield json.dumps(
                {
                    "type": "error",
                    "detail": hosted_qwen_failure_detail(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        final_answer = "\n".join(answer_lines).strip()
        if not final_answer:
            yield json.dumps(
                {
                    "type": "error",
                    "detail": hosted_qwen_failure_detail(),
                },
                ensure_ascii=False,
            ) + "\n"
            return

        yield json.dumps(
            {
                "type": "done",
                "answer": final_answer,
                "model": HF_QWEN_MODEL,
                "mode": "hf-qwen",
                "llm_available": True,
                "llm_mode": active_llm_mode(),
            },
            ensure_ascii=False,
        ) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


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

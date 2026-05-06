from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "clean_data.csv"
VND_BILLION = 1_000_000_000
VND_MILLION = 1_000_000

app = FastAPI(title="PropertyVision BI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Filters(BaseModel):
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


class AssistantRequest(BaseModel):
    question: str
    filters: Filters = Field(default_factory=Filters)


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


def records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [{key: clean_value(value) for key, value in row.items()} for row in df.to_dict(orient="records")]


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["bedrooms_num"] = df["Bedrooms"].map(parse_number)
    df["toilets_num"] = df["Toilets"].map(parse_number)
    df["floor_num"] = pd.to_numeric(df["Total Floors"], errors="coerce")
    df["price_billion"] = df["price_vnd"] / VND_BILLION
    df["price_per_m2_million"] = df["price_per_m2"] / VND_MILLION
    df["roi_pct"] = df["ROI"] * 100
    df["ward"] = df["Location"].str.split(",").str[0].str.strip()
    return df


def apply_filters(df: pd.DataFrame, filters: Filters) -> pd.DataFrame:
    result = df.copy()
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
        result = result[result["roi_pct"] >= filters.roi_min]
    if filters.roi_max is not None:
        result = result[result["roi_pct"] <= filters.roi_max]
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
    grouped = (
        df.groupby("district")
        .agg(
            listings=("Location", "count"),
            avg_price=("price_vnd", "mean"),
            median_price=("price_vnd", "median"),
            avg_price_m2=("price_per_m2", "mean"),
            avg_roi=("ROI", "mean"),
            volatility=("ROI", "std"),
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
    return (
        df.groupby("Type of House")
        .agg(
            listings=("Location", "count"),
            avg_price=("price_vnd", "mean"),
            median_price=("price_vnd", "median"),
            avg_roi=("ROI", "mean"),
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
    ]
    model_df = df[features + ["price_vnd"]].dropna(subset=["price_vnd", "area", "price_per_m2", "ROI"])
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
    }
    return pipeline, metrics


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/metadata")
def metadata() -> dict[str, Any]:
    df = load_data()
    return {
        "rows": len(df),
        "districts": sorted(df["district"].dropna().unique().tolist()),
        "property_types": sorted(df["Type of House"].dropna().unique().tolist()),
        "legal_documents": sorted(df["Legal Documents"].dropna().unique().tolist()),
        "price_range": [float(df["price_billion"].quantile(0.01)), float(df["price_billion"].quantile(0.99))],
        "area_range": [float(df["area"].quantile(0.01)), float(df["area"].quantile(0.99))],
        "roi_range": [float(df["roi_pct"].min()), float(df["roi_pct"].max())],
    }


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
        .agg(price_billion=("price_billion", "mean"), roi_pct=("roi_pct", "mean"), listings=("Location", "count"))
        .dropna()
        .reset_index()
    )
    best = district_df.iloc[0]
    risky = district_df.sort_values(["roi_pct", "volatility"], ascending=[True, False]).head(5)
    samples = df.sort_values("ROI", ascending=False).head(80)

    return {
        "empty": False,
        "kpis": {
            "listings": int(len(df)),
            "total_value": float(df["price_vnd"].sum()),
            "median_price": float(df["price_vnd"].median()),
            "avg_price_m2": float(df["price_per_m2"].mean()),
            "avg_roi": float(df["roi_pct"].mean()),
            "best_district": str(best["district"]),
            "best_score": float(best["opportunity_score"]),
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


@app.post("/api/predict")
def predict(payload: PredictionRequest) -> dict[str, Any]:
    df = load_data()
    model, metrics = train_model()
    local = df[(df["district"] == payload.district) & (df["Type of House"] == payload.property_type)]
    if local.empty:
        local = df[df["district"] == payload.district]
    if local.empty:
        local = df
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
        "model": metrics,
    }


def rag_documents(df: pd.DataFrame) -> list[dict[str, str]]:
    districts = district_score(df).head(12)
    types = type_score(df)
    docs: list[dict[str, str]] = []
    for row in districts.itertuples(index=False):
        docs.append(
            {
                "title": f"Khu vực {row.district}",
                "content": (
                    f"{row.district}: {row.listings} tin, ROI {row.roi_pct:.2f}%, "
                    f"giá trung vị {row.median_price / VND_BILLION:.2f} tỷ, "
                    f"giá/m2 {row.price_m2_million:.1f} triệu, điểm cơ hội {row.opportunity_score:.1f}."
                ),
            }
        )
    for row in types.itertuples(index=False):
        docs.append(
            {
                "title": f"Phân khúc {getattr(row, '_0')}",
                "content": (
                    f"{getattr(row, '_0')}: {row.listings} tin, ROI {row.roi_pct:.2f}%, "
                    f"giá/m2 {row.price_m2_million:.1f} triệu."
                ),
            }
        )
    return docs


@app.post("/api/assistant")
def assistant(payload: AssistantRequest) -> dict[str, Any]:
    df = apply_filters(load_data(), payload.filters)
    if df.empty:
        return {"answer": "Không có dữ liệu phù hợp với bộ lọc hiện tại.", "sources": []}

    docs = rag_documents(df)
    tokens = set(re.findall(r"\w+", payload.question.lower()))
    ranked = sorted(
        docs,
        key=lambda doc: sum(token in (doc["title"] + " " + doc["content"]).lower() for token in tokens),
        reverse=True,
    )
    selected = ranked[:5]
    top = district_score(df).iloc[0]
    answer = (
        f"Khuyến nghị hiện tại là ưu tiên {top['district']} với điểm cơ hội "
        f"{top['opportunity_score']:.1f}/100 và ROI trung bình {top['roi_pct']:.2f}%. "
        "Nên dùng kết quả này như lớp sàng lọc ban đầu, sau đó kiểm tra pháp lý, quy hoạch, "
        "dòng tiền cho thuê và khả năng thoát hàng trước khi giải ngân."
    )
    return {"answer": answer, "sources": selected}

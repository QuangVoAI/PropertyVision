from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agentic_rag import run_agentic_rag
from src.analytics import (
    SCENARIO_PRESETS,
    compute_undervalued_scores,
    district_scorecard,
    forecast_district_prices,
    simulate_price,
    summarize_market,
)
from src.data_access import clear_data_cache, filter_listings, filter_monthly, load_listings, load_monthly
from src.pipeline import raw_files_status, seed_kaggle_data, seed_synthetic_data
from src.rag import build_vector_store, package_status, rag_runtime_mode, reset_vector_store


app = FastAPI(title="PropertyVision API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3)
    city: str
    districts: list[str] = Field(default_factory=list)
    property_types: list[str] = Field(default_factory=list)
    tone: str = "advisor"


class ScenarioRequest(BaseModel):
    city: str
    district: str
    interest_rate: float
    growth_rate: float
    supply_shock: float
    years: int


def _load_filtered_context(
    city: str,
    districts: list[str] | None = None,
    property_types: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    listings = load_listings()
    if listings.empty:
        raise HTTPException(status_code=400, detail="Database is empty. Load sample or Kaggle data first.")
    monthly = load_monthly()
    filtered_listings = filter_listings(listings, city, districts, property_types)
    filtered_monthly = filter_monthly(monthly, city, districts)
    if filtered_listings.empty:
        raise HTTPException(status_code=404, detail="No records match the selected filters.")
    scorecard = district_scorecard(filtered_listings, filtered_monthly)
    return filtered_listings, filtered_monthly, scorecard


def _overview_payload(
    filtered_listings: pd.DataFrame,
    filtered_monthly: pd.DataFrame,
    scorecard: pd.DataFrame,
) -> dict[str, Any]:
    summary = summarize_market(filtered_listings, filtered_monthly)
    district_heat = (
        filtered_listings.groupby("district_name", as_index=False)
        .agg(
            avg_price_per_sqm=("price_per_sqm", "mean"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
            listing_count=("listing_id", "count"),
            median_area=("area_sqm", "median"),
        )
        .sort_values("avg_price_per_sqm", ascending=False)
    )
    trend = (
        filtered_monthly.groupby("month", as_index=False)
        .agg(avg_price_per_sqm=("avg_price_per_sqm", "mean"), listing_count=("listing_count", "sum"))
        .sort_values("month")
    )
    top_segments = (
        filtered_listings.groupby("property_type_name", as_index=False)
        .agg(avg_price_per_sqm=("price_per_sqm", "mean"), listing_count=("listing_id", "count"))
        .sort_values("avg_price_per_sqm", ascending=False)
    )
    return {
        "summary": summary,
        "district_heat": district_heat.to_dict("records"),
        "trend": trend.to_dict("records"),
        "top_segments": top_segments.to_dict("records"),
        "scorecard_preview": scorecard.head(10).to_dict("records"),
    }


def _evidence_payload(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence = []
    for doc in docs[:3]:
        evidence.append(
            {
                "source": doc.get("source"),
                "excerpt": str(doc.get("content", "")).strip().replace("\n", " ")[:260],
                "score": round(float(doc.get("focus_score", doc.get("final_score", doc.get("rerank_score", doc.get("score", 0.0))))), 3),
            }
        )
    return evidence


def _chat_visual_payload(
    filtered_listings: pd.DataFrame,
    filtered_monthly: pd.DataFrame,
    scorecard: pd.DataFrame,
    district: str | None,
    intent: str,
) -> list[dict[str, Any]]:
    visuals: list[dict[str, Any]] = []

    district_compare = (
        filtered_listings.groupby("district_name", as_index=False)
        .agg(avg_price_per_sqm=("price_per_sqm", "mean"), listing_count=("listing_id", "count"))
        .sort_values("avg_price_per_sqm", ascending=False)
        .head(8)
    )
    visuals.append(
        {
            "kind": "district_compare",
            "title": "Mặt bằng giá theo quận",
            "subtitle": "So sánh giá trung bình/m² trong bộ lọc hiện tại.",
            "data": district_compare.to_dict("records"),
        }
    )

    if intent in {"valuation", "overview"} and not scorecard.empty:
        zscore_data = scorecard[["district_name", "z_score", "signal", "avg_price_per_sqm"]].copy()
        visuals.append(
            {
                "kind": "zscore_compare",
                "title": "Định giá tương đối",
                "subtitle": "Z-score thấp hơn cho thấy quận rẻ tương đối hơn trong cùng bộ lọc.",
                "data": zscore_data.to_dict("records"),
            }
        )

    focus_district = district or (filtered_monthly["district_name"].iloc[0] if not filtered_monthly.empty else None)
    if focus_district:
        district_monthly = filtered_monthly[filtered_monthly["district_name"] == focus_district]
        if not district_monthly.empty:
            forecast_df, residual_std = forecast_district_prices(district_monthly)
            visuals.append(
                {
                    "kind": "forecast",
                    "title": f"Dự báo giá cho {focus_district}",
                    "subtitle": "Lịch sử giá/m² kết hợp đường dự báo và dải bất định.",
                    "data": forecast_df.to_dict("records"),
                    "meta": {"district": focus_district, "residual_std": residual_std},
                }
            )
            defaults = SCENARIO_PRESETS["Ổn định"]
            base_price = float(district_monthly["avg_price_per_sqm"].iloc[-1])
            scenario_df = simulate_price(
                base_price=base_price,
                interest_rate=float(defaults["interest_rate"]),
                growth_rate=float(defaults["growth_rate"]),
                supply_shock=float(defaults["supply_shock"]),
                years=5,
            )
            visuals.append(
                {
                    "kind": "scenario_projection",
                    "title": f"Kịch bản 5 năm cho {focus_district}",
                    "subtitle": "Baseline dựa trên preset Ổn định để minh họa triển vọng tương lai.",
                    "data": scenario_df.to_dict("records"),
                    "meta": {"district": focus_district, "preset": "Ổn định"},
                }
            )

    return visuals


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "rag_mode": rag_runtime_mode(), "packages": package_status()}


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    listings = load_listings()
    cities = sorted(listings["city_name"].unique()) if not listings.empty else []
    districts_by_city = {
        city: sorted(listings.loc[listings["city_name"] == city, "district_name"].unique())
        for city in cities
    }
    property_types = sorted(listings["property_type_name"].unique()) if not listings.empty else []
    return {
        "cities": cities,
        "districts_by_city": districts_by_city,
        "property_types": property_types,
        "scenario_presets": SCENARIO_PRESETS,
        "raw_files": raw_files_status(),
    }


@app.post("/api/data/load-sample")
def load_sample_data() -> dict[str, str]:
    message = seed_synthetic_data()
    clear_data_cache()
    return {"message": message}


@app.post("/api/data/load-kaggle")
def load_kaggle_data() -> dict[str, str]:
    message = seed_kaggle_data()
    clear_data_cache()
    return {"message": message}


@app.post("/api/rag/reindex")
def reindex_rag() -> dict[str, Any]:
    return build_vector_store(force_rebuild=True)


@app.delete("/api/rag/index")
def clear_rag_index() -> dict[str, str]:
    reset_vector_store()
    return {"message": "Vector index removed."}


@app.get("/api/dashboard")
def dashboard(
    city: str,
    districts: list[str] = Query(default=[]),
    property_types: list[str] = Query(default=[]),
) -> dict[str, Any]:
    filtered_listings, filtered_monthly, scorecard = _load_filtered_context(city, districts, property_types)
    forecast_district = districts[0] if districts else sorted(filtered_listings["district_name"].unique())[0]
    forecast_input = filtered_monthly[filtered_monthly["district_name"] == forecast_district]
    forecast_df, residual_std = forecast_district_prices(forecast_input)
    snapshot = (
        filtered_monthly.sort_values("month")
        .groupby("district_name", as_index=False)
        .tail(1)[["district_name", "avg_price_per_sqm"]]
    )
    undervalued = compute_undervalued_scores(snapshot)
    return {
        "overview": _overview_payload(filtered_listings, filtered_monthly, scorecard),
        "forecast": {
            "district": forecast_district,
            "series": forecast_df.to_dict("records"),
            "residual_std": residual_std,
        },
        "undervalued": undervalued.to_dict("records"),
        "scorecard": scorecard.to_dict("records"),
    }


@app.post("/api/forecast/scenario")
def forecast_scenario(payload: ScenarioRequest) -> dict[str, Any]:
    filtered_listings, filtered_monthly, _ = _load_filtered_context(payload.city, [payload.district], None)
    if filtered_monthly.empty:
        raise HTTPException(status_code=404, detail="District monthly data not found.")
    base_price = float(filtered_monthly["avg_price_per_sqm"].iloc[-1])
    sim_df = simulate_price(
        base_price=base_price,
        interest_rate=payload.interest_rate,
        years=payload.years,
        growth_rate=payload.growth_rate,
        supply_shock=payload.supply_shock,
    )
    return {
        "district": payload.district,
        "base_price": base_price,
        "series": sim_df.to_dict("records"),
        "listing_count": int(len(filtered_listings)),
    }


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    filtered_listings, filtered_monthly, scorecard = _load_filtered_context(
        payload.city,
        payload.districts,
        payload.property_types,
    )
    result = run_agentic_rag(payload.question, filtered_listings, scorecard, tone=payload.tone)
    evidence = _evidence_payload(result.graded_docs if result.graded_docs else result.retrieved_docs)
    visuals = _chat_visual_payload(
        filtered_listings=filtered_listings,
        filtered_monthly=filtered_monthly,
        scorecard=scorecard,
        district=result.district,
        intent=result.intent,
    )
    return {
        "answer": result.answer,
        "citations": result.citations,
        "evidence": evidence,
        "visualizations": visuals,
        "trace": {
            "intent": result.intent,
            "city": result.city,
            "district": result.district,
            "mentioned_district": result.mentioned_district,
            "tone": result.tone,
            "rewritten_query": result.rewritten_query,
            "sql_summary": result.sql_summary,
            "retrieved_docs": [doc["source"] for doc in result.retrieved_docs],
            "graded_docs": [doc["source"] for doc in result.graded_docs],
        },
    }

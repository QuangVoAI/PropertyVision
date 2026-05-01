from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


SCENARIO_PRESETS = {
    "Đóng băng": {"interest_rate": 12.0, "growth_rate": -2.0, "supply_shock": 1.06},
    "Ổn định": {"interest_rate": 8.0, "growth_rate": 7.0, "supply_shock": 1.00},
    "Sốt đất hạ tầng": {"interest_rate": 6.5, "growth_rate": 15.0, "supply_shock": 0.92},
}


def forecast_district_prices(monthly_df: pd.DataFrame, horizon: int = 3) -> tuple[pd.DataFrame, float]:
    if monthly_df.empty:
        return pd.DataFrame(), 0.0

    work = monthly_df.sort_values("month").reset_index(drop=True).copy()
    work["t"] = np.arange(len(work))

    model = LinearRegression()
    X = work[["t"]]
    y = work["avg_price_per_sqm"]
    sample_weight = work["listing_count"].clip(lower=1)
    model.fit(X, y, sample_weight=sample_weight)

    work["prediction"] = model.predict(X)
    residual_std = float((y - work["prediction"]).std(ddof=1)) if len(work) > 1 else 0.0

    future_index = np.arange(len(work), len(work) + horizon)
    future_months = pd.period_range(work["month"].iloc[-1], periods=horizon + 1, freq="M")[1:]
    future_pred = model.predict(pd.DataFrame({"t": future_index}))

    forecast_df = pd.DataFrame(
        {
            "month": future_months.astype(str),
            "avg_price_per_sqm": np.nan,
            "prediction": future_pred,
            "y_lower": future_pred - residual_std,
            "y_upper": future_pred + residual_std,
            "series_type": "forecast",
        }
    )

    history_df = work[["month", "avg_price_per_sqm", "prediction"]].copy()
    history_df["y_lower"] = history_df["prediction"] - residual_std
    history_df["y_upper"] = history_df["prediction"] + residual_std
    history_df["series_type"] = "history"
    return pd.concat([history_df, forecast_df], ignore_index=True), residual_std


def simulate_price(
    base_price: float,
    interest_rate: float,
    years: int,
    growth_rate: float,
    supply_shock: float = 1.0,
) -> pd.DataFrame:
    records = []
    current = base_price
    for year in range(years + 1):
        shock = 1 - (interest_rate - 8.0) * 0.025
        supply_adjustment = 1 / supply_shock
        adjusted_growth = (growth_rate / 100.0) * shock * supply_adjustment
        if year > 0:
            current *= 1 + adjusted_growth
        records.append(
            {
                "year": year,
                "simulated_price": current,
                "interest_rate": interest_rate,
                "growth_rate": growth_rate,
                "supply_shock": supply_shock,
            }
        )
    return pd.DataFrame(records)


def compute_undervalued_scores(district_snapshot: pd.DataFrame) -> pd.DataFrame:
    work = district_snapshot.copy()
    mean_value = work["avg_price_per_sqm"].mean()
    std_value = work["avg_price_per_sqm"].std(ddof=0) or 1.0
    work["z_score"] = (work["avg_price_per_sqm"] - mean_value) / std_value
    work["signal"] = np.where(work["z_score"] < -0.5, "Undervalued", "Neutral/Expensive")
    return work.sort_values("z_score")


def summarize_market(listings_df: pd.DataFrame, monthly_df: pd.DataFrame) -> dict[str, float | str]:
    if listings_df.empty:
        return {
            "listing_count": 0,
            "district_count": 0,
            "avg_price_per_sqm": 0.0,
            "median_area": 0.0,
            "latest_month": "N/A",
            "market_delta_pct": 0.0,
        }

    latest_month = monthly_df["month"].max() if not monthly_df.empty else "N/A"
    earliest_month = monthly_df["month"].min() if not monthly_df.empty else "N/A"
    latest_avg = (
        monthly_df.loc[monthly_df["month"] == latest_month, "avg_price_per_sqm"].mean()
        if latest_month != "N/A"
        else 0.0
    )
    earliest_avg = (
        monthly_df.loc[monthly_df["month"] == earliest_month, "avg_price_per_sqm"].mean()
        if earliest_month != "N/A"
        else 0.0
    )
    market_delta_pct = ((latest_avg - earliest_avg) / earliest_avg) * 100 if earliest_avg else 0.0
    return {
        "listing_count": int(len(listings_df)),
        "district_count": int(listings_df["district_name"].nunique()),
        "avg_price_per_sqm": float(listings_df["price_per_sqm"].mean()),
        "median_area": float(listings_df["area_sqm"].median()),
        "latest_month": latest_month,
        "market_delta_pct": float(market_delta_pct),
    }


def district_scorecard(filtered_df: pd.DataFrame, monthly_df: pd.DataFrame) -> pd.DataFrame:
    if filtered_df.empty:
        return pd.DataFrame()

    latest_per_district = (
        monthly_df.sort_values("month")
        .groupby("district_name", as_index=False)
        .tail(1)[["district_name", "avg_price_per_sqm", "listing_count"]]
    )
    scorecard = (
        filtered_df.groupby("district_name", as_index=False)
        .agg(
            avg_price_per_sqm=("price_per_sqm", "mean"),
            median_area=("area_sqm", "median"),
            avg_bedrooms=("bedrooms", "mean"),
            listing_count=("listing_id", "count"),
        )
        .merge(
            latest_per_district.rename(
                columns={
                    "avg_price_per_sqm": "latest_month_price_per_sqm",
                    "listing_count": "latest_month_listing_count",
                }
            ),
            on="district_name",
            how="left",
        )
    )
    scored = compute_undervalued_scores(
        scorecard[["district_name", "avg_price_per_sqm"]].copy()
    )
    scorecard = scorecard.merge(scored[["district_name", "z_score", "signal"]], on="district_name", how="left")
    scorecard["liquidity_score"] = (
        scorecard["listing_count"].rank(pct=True) * 0.5
        + scorecard["latest_month_listing_count"].fillna(0).rank(pct=True) * 0.5
    ).round(2)
    scorecard["signal_rank"] = scorecard["signal"].map({"Undervalued": 0, "Neutral/Expensive": 1}).fillna(2)
    scorecard = scorecard.sort_values(["signal_rank", "z_score", "liquidity_score"], ascending=[True, True, False])
    return scorecard.drop(columns=["signal_rank"])

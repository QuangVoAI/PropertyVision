from __future__ import annotations

from functools import lru_cache

import pandas as pd

from src.db import get_connection


LISTINGS_QUERY = """
SELECT
    f.listing_id,
    c.city_name,
    d.district_name,
    p.property_type_name,
    f.owner_name,
    f.address,
    f.area_sqm,
    f.bedrooms,
    f.legal_status,
    f.posted_date,
    f.price_text,
    f.price_vnd,
    f.price_per_sqm,
    f.latitude,
    f.longitude,
    f.description
FROM fact_listings f
JOIN dim_city c ON c.city_id = f.city_id
JOIN dim_district d ON d.district_id = f.district_id
JOIN dim_property_type p ON p.property_type_id = f.property_type_id
"""

MONTHLY_QUERY = """
SELECT
    c.city_name,
    d.district_name,
    m.month,
    m.avg_price_per_sqm,
    m.listing_count
FROM mart_district_monthly m
JOIN dim_district d ON d.district_id = m.district_id
JOIN dim_city c ON c.city_id = d.city_id
"""


@lru_cache(maxsize=1)
def load_listings() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(LISTINGS_QUERY, conn)
    conn.close()
    return df


@lru_cache(maxsize=1)
def load_monthly() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(MONTHLY_QUERY, conn)
    conn.close()
    return df


def clear_data_cache() -> None:
    load_listings.cache_clear()
    load_monthly.cache_clear()


def filter_listings(
    listings: pd.DataFrame,
    city: str,
    districts: list[str] | None = None,
    property_types: list[str] | None = None,
) -> pd.DataFrame:
    filtered = listings[listings["city_name"] == city]
    if districts:
        filtered = filtered[filtered["district_name"].isin(districts)]
    if property_types:
        filtered = filtered[filtered["property_type_name"].isin(property_types)]
    return filtered.copy()


def filter_monthly(
    monthly: pd.DataFrame,
    city: str,
    districts: list[str] | None = None,
) -> pd.DataFrame:
    filtered = monthly[monthly["city_name"] == city]
    if districts:
        filtered = filtered[filtered["district_name"].isin(districts)]
    return filtered.copy()

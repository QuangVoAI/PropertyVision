from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "propertyvision.db"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS dim_city (
            city_id INTEGER PRIMARY KEY,
            city_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS dim_district (
            district_id INTEGER PRIMARY KEY,
            city_id INTEGER NOT NULL,
            district_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            UNIQUE(city_id, district_name),
            FOREIGN KEY(city_id) REFERENCES dim_city(city_id)
        );

        CREATE TABLE IF NOT EXISTS dim_property_type (
            property_type_id INTEGER PRIMARY KEY,
            property_type_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS fact_listings (
            listing_id INTEGER PRIMARY KEY,
            city_id INTEGER NOT NULL,
            district_id INTEGER NOT NULL,
            property_type_id INTEGER NOT NULL,
            owner_name TEXT NOT NULL,
            address TEXT NOT NULL,
            area_sqm REAL NOT NULL,
            bedrooms INTEGER NOT NULL,
            legal_status TEXT NOT NULL,
            posted_date TEXT NOT NULL,
            price_text TEXT NOT NULL,
            price_vnd REAL NOT NULL,
            price_per_sqm REAL NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            description TEXT,
            FOREIGN KEY(city_id) REFERENCES dim_city(city_id),
            FOREIGN KEY(district_id) REFERENCES dim_district(district_id),
            FOREIGN KEY(property_type_id) REFERENCES dim_property_type(property_type_id)
        );

        CREATE TABLE IF NOT EXISTS mart_district_monthly (
            district_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            avg_price_per_sqm REAL NOT NULL,
            listing_count INTEGER NOT NULL,
            PRIMARY KEY(district_id, month),
            FOREIGN KEY(district_id) REFERENCES dim_district(district_id)
        );
        """
    )
    conn.commit()

from __future__ import annotations

from pathlib import Path

from src.generate_sample import generate_listing_rows, load_to_sqlite
from src.ingest_kaggle import import_kaggle_datasets


RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
HCMC_CSV = RAW_DIR / "vietnam_housing_hcm.csv"
HANOI_CSV = RAW_DIR / "VN_housing_dataset.csv"


def raw_files_status() -> dict[str, bool]:
    return {
        "hcmc_csv": HCMC_CSV.exists(),
        "hanoi_csv": HANOI_CSV.exists(),
    }


def seed_synthetic_data() -> str:
    df = generate_listing_rows()
    load_to_sqlite(df)
    return f"Loaded {len(df)} synthetic listings."


def seed_kaggle_data() -> str:
    df = import_kaggle_datasets(HCMC_CSV, HANOI_CSV)
    load_to_sqlite(df)
    return f"Imported {len(df)} Kaggle listings."

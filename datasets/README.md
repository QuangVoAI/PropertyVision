---
language:
- vi
license: other
task_categories:
- tabular-classification
- tabular-regression
tags:
- real-estate
- vietnam
- hanoi
- ho-chi-minh-city
- business-intelligence
- property-analytics
- tabular
- pandas
pretty_name: Hanoi & Ho Chi Minh City Real Estate Dataset
size_categories:
- 100K<n<1M
---

# Hanoi & Ho Chi Minh City Real Estate Dataset

## Dataset Summary

This dataset is a cleaned, consolidated, and analysis-ready real estate dataset covering two major Vietnamese urban markets:

- **Hanoi**
- **Ho Chi Minh City**

It was prepared for **PropertyVision BI**, a business intelligence and decision-support project focused on property analytics, price prediction, ROI analysis, planning-risk exploration, and dashboard-based market monitoring.

The dataset is designed for:

- exploratory data analysis
- dashboarding and BI use cases
- tabular machine learning
- market segmentation
- investment scenario analysis

## Why This Dataset Matters

This dataset was built to demonstrate more than simple data collection. It reflects a practical end-to-end analytics workflow that is highly relevant for portfolio and CV use cases:

- multi-source tabular data consolidation
- schema harmonization across two major cities
- feature standardization for business intelligence and machine learning
- rule-based enrichment for incomplete records
- validation-oriented preprocessing for downstream product stability

For recruiters or reviewers, this dataset highlights work across **data cleaning, dataset design, feature engineering, data validation, and analytics product thinking** rather than only model training.

## Quick Stats

| Metric | Value |
|---|---:|
| Total rows | 106,205 |
| Cities covered | 2 |
| Ho Chi Minh City rows | 23,722 |
| Hanoi rows | 82,483 |
| Main data file | `clean_dataset.csv` |
| Format | CSV |
| Primary use | BI, analytics, ML experimentation |

## Preview

### BI Overview Dashboard

![PropertyVision BI overview](./preview-overview.png)

### GIS and Planning View

![PropertyVision GIS and planning map](./preview-gis-map.png)

## Dataset Structure

The main file in this repository is:

- `clean_dataset.csv`

Each row represents a processed property listing or synthesized listing record prepared for downstream analytics.

### Core Columns

- `Location`: normalized location label
- `Price`: human-readable property price
- `Type of House`: property category
- `Land Area`: human-readable area label
- `Bedrooms`: bedroom count label
- `Toilets`: toilet count label
- `Total Floors`: number of floors
- `Main Door Direction`: main door orientation
- `Balcony Direction`: balcony orientation
- `Legal Documents`: legal status label
- `price_vnd`: numeric property price in VND
- `area`: numeric land/building area
- `price_per_m2`: numeric price per square meter
- `district`: district label
- `purchase_price`: estimated purchase price proxy
- `current_price`: current price proxy
- `ROI`: return-on-investment proxy
- `date`: normalized date field
- `city`: city label
- `source_dataset`: original source file identifier

## Data Sources

This dataset is a curated derivative dataset built from cleaned source data used in the PropertyVision project.

The underlying information was assembled from public and educational data sources referenced in the project, including public planning/GIS references and real estate market proxy data.

This repository publishes the **processed analytical dataset**, not a claim of ownership over all raw source records.

Because this is a derivative analytical release, users should review upstream source terms before using the dataset for redistribution or commercial applications.

## Preprocessing and Curation

The published dataset was prepared through several curation steps:

1. schema standardization across city-level datasets
2. column normalization for price, area, ROI, district, and date fields
3. consolidation of Hanoi and Ho Chi Minh City records into one tabular dataset
4. generation of business-ready derived fields such as `purchase_price`, `current_price`, and `price_per_m2`
5. consistency validation for property-type-specific rules

## Important Note on Synthetic Enrichment

Some Hanoi records originally had fewer attributes than the Ho Chi Minh City dataset.

To create a unified schema for analytics and demo applications, selected fields for Hanoi were enriched using **deterministic rule-based preprocessing**, including:

- property type inference
- bedroom and toilet count estimation
- floor count estimation
- legal document label approximation
- directional field completion
- normalized location labeling

These enriched values were created to support **schema consistency, dashboard stability, and machine learning experimentation**.

They should be treated as **synthetic analytical enrichments**, not guaranteed ground-truth metadata.

## Intended Use

Recommended use cases:

- BI dashboards
- market comparison between Hanoi and Ho Chi Minh City
- regression experiments for property price estimation
- ROI analysis
- feature engineering practice
- educational data projects
- portfolio projects in analytics, data science, and data engineering

## Skills Demonstrated

This dataset release demonstrates the following practical skills:

- data cleaning and tabular preprocessing
- schema design and dataset consolidation
- feature engineering for property analytics
- rule-based synthetic enrichment for incomplete records
- validation rule design for data consistency
- business intelligence thinking for dashboard-ready data products
- preparation of shareable ML and analytics assets for public repositories

## Author

Curated and released by **Xuan Quang Vo** as part of the **PropertyVision BI** project.

## Limitations

- This dataset is intended primarily for **analytics and educational use**.
- Some fields are cleaned proxies rather than directly verified transaction records.
- Some Hanoi attributes are **synthetically enriched** for consistency.
- The dataset should not be used as the sole basis for legal, financial, or investment decisions.

## Citation

If you use this dataset, please cite it as:

```bibtex
@dataset{springwang08_hanoi_hcmc_real_estate,
  author = {Xuan Quang Vo},
  title = {Hanoi \& Ho Chi Minh City Real Estate Dataset},
  year = {2026},
  publisher = {Hugging Face},
  url = {https://huggingface.co/datasets/SpringWang08/hanoi-hcmc-real-estate}
}
```

## Acknowledgement

This dataset card and processed release were prepared as part of the **PropertyVision BI** project for academic, portfolio, and demonstration purposes.

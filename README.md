# PropertyVision BI

PropertyVision is a full-stack Business Intelligence and Decision Support web system for enterprise real estate investment. The system combines market analytics, transaction-proxy data, GIS planning context, price prediction, realtime ETL, and Legal/Planning RAG with a local LLM.

## Run Backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Backend: `http://localhost:8000`

## Run Local LLM

PropertyVision uses Ollama when available.

```bash
ollama serve
ollama run qwen2.5:14b
```

Fallback models configured in backend: `llama3.1:latest`, `llama3:latest`.

If Ollama is offline, RAG still returns retrieved BI/legal/planning context with citations.

## Run Frontend

```bash
cd frontend
npm run dev
```

Frontend: `http://localhost:5173`

## Main Modules

- Multi-page React frontend adapted from the `web/` design handoff.
- Executive Dashboard: KPI, ROI, market value, top opportunity district.
- Market Intelligence: district and property-type analysis.
- Slice & Dice Analysis: enterprise multidimensional analysis by district, property type, legal status, price band, area band, and ROI band.
- Investment Strategy: opportunity scoring and action recommendation.
- GIS Map: district-level planning/risk map using public GIS-style coordinates.
- Data Pipeline: manual refresh, scheduled refresh, incremental transaction-proxy ingest, ETL logs.
- Price Prediction: Random Forest model with legal/planning risk feature.
- What-If Simulation: budget, growth, and horizon sliders calculate future value, ROI, annualized ROI, investable units, and payback period.
- Multi-scenario Projection: pessimistic/base/optimistic 5-10 year projection with confidence band.
- Legal/Planning RAG: retrieval over BI summaries, legal notes, planning zones, and public-source citations.
- MIS/DSS/EIS: explanation of how the project maps to enterprise information systems.

## Public Data Hub

The demo uses public and cached sources:

- HCMGIS Portal: https://portal.hcmgis.vn/
- HCMGIS/GeoNode registry: https://dateno.io/registry/catalog/cdi00001949/
- HCMC land data platform reference: https://vietnam.opendevelopmentmekong.net/news/hcmc-launches-online-land-data-platform/
- HCMC planning lookup portal: https://thongtinquyhoach.hochiminhcity.gov.vn
- Kaggle HCMC Real Estate Data 2025: https://www.kaggle.com/datasets/cnglmph/ho-chi-minh-city-real-estate-data-2025
- Kaggle House Pricing HCM: https://www.kaggle.com/datasets/trnduythanhkhttt/housepricinghcm/data

## Key API Endpoints

- `GET /api/health`
- `GET /api/metadata`
- `POST /api/analytics`
- `POST /api/slice-dice`
- `POST /api/predict`
- `POST /api/what-if`
- `POST /api/assistant`
- `GET /api/methodology`
- `GET /api/model-info`
- `POST /api/etl/run`
- `GET /api/etl/status`
- `GET /api/map/districts`
- `GET /api/planning/zones`
- `POST /api/rag/reindex`

## Rubric Coverage

- Mô tả đề tài/bài toán: tab MIS/DSS/EIS and this README.
- Mô tả công cụ/thuật toán/phương pháp: FastAPI, React, Recharts, Leaflet, SQLite, Random Forest, ETL, RAG, Ollama.
- Demo ứng dụng: frontend at `localhost:5173`.
- Trực quan hóa kết quả/giải thích/phân tích: dashboards, charts, GIS map, strategy table, citations.
- Baseline document: `BASELINE.md` includes data dictionary, KPI formulas, model metrics, what-if formulas, and RAG architecture notes.
- Kết luận: Executive Conclusion section in the MIS/DSS/EIS tab.
- Thuyết trình/demo: use `DEMO_SCRIPT.md`.
- Trình bày: `PRESENTATION_OUTLINE.md`.

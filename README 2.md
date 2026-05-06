# PropertyVision BI

Full-stack BI web app for real estate price prediction, ROI analysis, investment strategy, and future RAG/LLM integration.

## Structure

- `backend/main.py`: FastAPI analytics, prediction, and assistant API.
- `frontend/src/main.jsx`: React dashboard.
- `frontend/src/styles.css`: Application UI styling.
- `clean_data.csv`: Cleaned property dataset.

## Run Backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Backend runs at `http://localhost:8000`.

## Run Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at `http://localhost:5173` and proxies `/api` requests to FastAPI.

## Features

- KPI dashboard for total value, median price, average price per m2, ROI, and best opportunity district.
- Market charts by district and property type.
- Investment strategy table with opportunity scoring.
- Price prediction endpoint using a Random Forest model trained from `clean_data.csv`.
- RAG/LLM assistant endpoint returning retrieved context from BI summaries.

## LLM Integration Point

Replace the logic in `backend/main.py` endpoint `/api/assistant` with your preferred RAG stack:

1. Generate district, property, legal, planning, and market documents.
2. Store embeddings in a vector database.
3. Retrieve top-k evidence for each question.
4. Send question and evidence to an LLM.
5. Return answer, sources, assumptions, and risk level to the frontend.

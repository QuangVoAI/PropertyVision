# PropertyVision BI

PropertyVision BI is a full-stack real estate intelligence application for **Ho Chi Minh City** and **Hanoi**, built for business intelligence, price prediction, ROI analysis, planning-risk exploration, and executive-style decision support.

The project combines:

- a **FastAPI backend** for analytics, prediction, planning, and assistant endpoints
- a **React + Vite frontend** for dashboards and interactive exploration
- a **Hugging Face-hosted processed dataset** that can be pulled automatically on first backend run

## Highlights

- Unified analytics across **Ho Chi Minh City** and **Hanoi**
- Market KPIs, district comparison, and property-type breakdowns
- Price prediction with machine learning
- What-if simulation and future recommendation flows
- GIS and planning-oriented views
- Retrieval-based assistant with optional Ollama integration

## Project Structure

```text
PropertyVision/
├── backend/                    FastAPI application
├── frontend/                   React + Vite frontend
├── datasets/                   Local dataset workspace
│   ├── README.md               Dataset card / dataset notes
│   └── raw/                    Optional raw reference files
├── data/                       SQLite files generated at runtime
├── docs/                       Project documentation
├── notebooks/                  Data exploration notebooks
├── app.py                      Quick run note
├── README.md
└── requirements.txt
```

## Dataset Behavior

The application is configured so that **cloning the repository is enough to get started**.

When the backend starts:

1. it tries to download `clean_dataset.csv` from Hugging Face
2. it stores the file locally at:

```text
datasets/clean_dataset.csv
```

3. if the download is unavailable but `datasets/clean_dataset.csv` already exists, it uses that local file
4. if neither is available, it falls back to the raw reference CSV files in `datasets/raw/`

Hugging Face dataset:

- https://huggingface.co/datasets/SpringWang08/hanoi-hcmc-real-estate

This means a fresh clone can run without manually copying the processed dataset into the repo.

## Data Quality Note

The processed CSV is not a raw export. Before the backend serves it, the app applies a rule-based normalization pass so the dataset stays internally consistent and demo-ready:

- `Bedrooms`, `Toilets`, and `Total Floors` are normalized by property type, area, and floor count
- land-type records are forced to `0` bedrooms, `0` toilets, and `0` floors
- Hanoi locations are aligned to real wards, communes, and townships within the correct districts
- dates are constrained to a realistic analysis window so trend charts remain meaningful

These rules are designed for BI exploration and portfolio demos, not as a claim of ground-truth property labels.

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/QuangVoAI/PropertyVision.git
cd PropertyVision
```

### 2. Start the backend

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Backend:

```text
http://localhost:8000
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## First-Run Experience

On the first backend run, the app may spend a short moment downloading the processed dataset from Hugging Face into `datasets/clean_dataset.csv`.

After that:

- the file remains available locally
- subsequent backend runs reuse the downloaded file
- the repository stays clean because the downloaded dataset file is ignored by Git

## Key Files

- `backend/main.py`: primary backend entrypoint
- `frontend/src/main.jsx`: main frontend app
- `datasets/README.md`: local dataset card and dataset notes
- `docs/BASELINE.md`: technical baseline
- `docs/DEMO_SCRIPT.md`: guided demo flow
- `docs/PRESENTATION_OUTLINE.md`: presentation structure
- `docs/UI_DESIGN_SPEC.md`: UI design reference

## Documentation

- [Technical Baseline](docs/BASELINE.md)
- [Demo Script](docs/DEMO_SCRIPT.md)
- [Presentation Outline](docs/PRESENTATION_OUTLINE.md)
- [UI Design Spec](docs/UI_DESIGN_SPEC.md)

## Notes

- `data/` is runtime-generated and not required to be present before startup.
- `datasets/clean_dataset.csv` is downloaded automatically and is not committed.
- `datasets/raw/` is kept only as an optional fallback/reference layer.
- Ollama is optional. If no local model is available, the assistant still returns retrieval-based fallback responses.

# PropertyVision BI

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.x-blue)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 📋 Project Overview

PropertyVision is an enterprise-grade **Business Intelligence and Decision Support System** for real estate investment in Ho Chi Minh City. The platform integrates market analytics, geospatial planning, predictive modeling, and AI-powered insights to enable data-driven investment decisions.

### Key Features

- 📊 **Executive Dashboard**: Real-time KPIs, ROI metrics, and market value analysis
- 🗺️ **GIS Map Integration**: District-level planning and risk visualization
- 🤖 **AI Assistant**: Legal/Planning RAG with local LLM support (Ollama)
- 🔮 **Price Prediction**: Random Forest model with risk factors
- 📈 **What-If Simulation**: Multi-scenario projection with confidence intervals
- 🔍 **Market Intelligence**: Multi-dimensional analysis by district, property type, and price bands
- 🔄 **Real-time ETL**: Automatic data pipeline and incremental data ingestion
- 📱 **Responsive UI**: React + Vite frontend with interactive visualizations

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI, Python 3.10+ |
| Frontend | React 18, Vite, Axios |
| Database | SQLite |
| Visualization | Recharts, Leaflet |
| ML/AI | Scikit-learn (Random Forest), Ollama (Local LLM) |
| Data Processing | Pandas, NumPy |

---

## 📦 Prerequisites

- Python 3.10+
- Node.js 16+ & npm
- Git
- (Optional) Ollama for local LLM support

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/QuangVoAI/PropertyVision.git
cd PropertyVision

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Start Services

**Terminal 1 - Backend:**
```bash
uvicorn backend.main:app --reload
# Backend available at: http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Frontend available at: http://localhost:5173
```

**Terminal 3 - Local LLM (Optional):**
```bash
ollama serve
ollama run qwen2.5:14b
```

> **Note**: If Ollama is unavailable, RAG will still work with fallback models (`llama3.1`, `llama3`). Without any LLM, the system returns retrieved context with citations.

---

## 📁 Project Structure

```
PropertyVision/
├── backend/
│   ├── __init__.py
│   └── main.py              # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── main.jsx         # React entry point
│   │   └── styles.css       # Global styles
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── data/
│   └── propertyvision.db    # SQLite database
├── Web/                     # UI design handoff
│   ├── b_n_quy_ho_ch_gis/
│   ├── ph_n_t_ch_th_tr_ng/
│   └── ... (analysis pages)
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── BASELINE.md             # Technical specifications
├── DEMO_SCRIPT.md          # Demo walkthrough
└── PRESENTATION_OUTLINE.md # Presentation guide
```

---

## 🎯 Core Modules

### Dashboard & Analytics
- **Executive Dashboard**: Key metrics, ROI analysis, market value, top opportunity districts
- **Market Intelligence**: District and property-type comparative analysis
- **Slice & Dice Analysis**: Multi-dimensional OLAP analysis

### Advanced Features
- **Investment Strategy**: Opportunity scoring and recommendation engine
- **GIS Map**: Interactive planning and risk visualization
- **Price Prediction**: ML-powered price estimation with risk assessment
- **What-If Simulation**: Scenario planning with budget and growth parameters
- **Multi-scenario Projection**: 5-10 year forecasts (pessimistic/base/optimistic)
- **Legal/Planning RAG**: Conversational AI with document retrieval

### Data Management
- **Data Pipeline**: Manual/scheduled refresh with ETL logging
- **Incremental Ingestion**: Transaction-proxy data synchronization
- **MIS/DSS/EIS Mapping**: Enterprise information systems framework

---

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/metadata` | System metadata |
| `POST` | `/api/analytics` | Analytics queries |
| `POST` | `/api/slice-dice` | Multi-dimensional analysis |
| `POST` | `/api/predict` | Price prediction |
| `POST` | `/api/what-if` | Simulation engine |
| `POST` | `/api/assistant` | RAG-based Q&A |
| `GET` | `/api/map/districts` | GIS district data |
| `GET` | `/api/planning/zones` | Planning zone data |
| `POST` | `/api/etl/run` | Trigger data pipeline |
| `GET` | `/api/etl/status` | ETL job status |

See `BASELINE.md` for detailed API documentation.

---

## 📊 Data Sources

The system integrates public and open-source data:

- **HCMGIS Portal**: https://portal.hcmgis.vn/
- **HCMC Planning Portal**: https://thongtinquyhoach.hochiminhcity.gov.vn
- **Kaggle Datasets**:
  - [HCMC Real Estate 2025](https://www.kaggle.com/datasets/cnglmph/ho-chi-minh-city-real-estate-data-2025)
  - [House Pricing HCM](https://www.kaggle.com/datasets/trnduythanhkhttt/housepricinghcm/data)

---

## 📚 Documentation

- **`BASELINE.md`**: Data dictionary, KPI formulas, model specs, architecture notes
- **`DEMO_SCRIPT.md`**: Step-by-step demo walkthrough
- **`PRESENTATION_OUTLINE.md`**: Presentation structure and key talking points
- **`UI_DESIGN_SPEC.md`**: UI/UX specifications

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   React Frontend (Vite)             │
│   - Dashboard, Charts, Map          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   FastAPI Backend                   │
│   - Analytics Engine                │
│   - ML Pipeline                     │
│   - RAG Service                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Data Layer                        │
│   - SQLite Database                 │
│   - ETL Pipeline                    │
└─────────────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
   ┌────▼──┐    ┌────▼──────┐
   │ Ollama │    │ Data APIs │
   │ (LLM)  │    │ (GIS, etc)│
   └────────┘    └───────────┘
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 Development Notes

- **Backend Logs**: Check Uvicorn output for API errors
- **Frontend Logs**: Open browser DevTools (F12)
- **Database**: SQLite file located at `data/propertyvision.db`
- **LLM Fallback**: System gracefully degrades if Ollama is unavailable

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 👥 Authors

- **Project Lead**: Quang Vo AI Team
- **Repository**: https://github.com/QuangVoAI/PropertyVision

---

## 🙋 Support

For issues, questions, or suggestions:
- Open an [Issue](https://github.com/QuangVoAI/PropertyVision/issues)
- Check existing [Documentation](./BASELINE.md)

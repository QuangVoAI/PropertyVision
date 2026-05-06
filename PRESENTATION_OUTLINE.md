# PropertyVision Presentation Outline

## Slide 1: Title

PropertyVision BI - Real Estate Decision Intelligence

## Slide 2: Problem

- Doanh nghiệp cần chọn khu vực đầu tư, định giá tài sản, kiểm soát ROI và rủi ro.
- Listing rời rạc không đủ để ra quyết định chiến lược.
- Cần MIS/DSS/EIS tích hợp BI, GIS, ETL và AI.

## Slide 3: Data

- `clean_data.csv`: listing đã xử lý.
- SQLite warehouse: dimension, fact listing, mart district monthly.
- Transaction proxy: public listing/time-series datasets.
- Planning/legal docs: HCMGIS, cổng quy hoạch, legal/planning cache.

## Slide 4: Architecture

- Frontend: React + Recharts + Leaflet.
- Backend: FastAPI.
- Storage: SQLite.
- ML: Random Forest.
- RAG: sentence-transformers + NearestNeighbors.
- LLM: Ollama local model.

## Slide 5: Method

- KPI analytics.
- Slice-and-dice multidimensional analysis.
- Opportunity scoring.
- Legal/planning risk screening.
- Price prediction.
- What-if simulation and payback analysis.
- 5-10 year multi-scenario projection.
- Retrieval + LLM answer with citations.
- ETL manual/scheduled/incremental.

## Slide 6: Demo Flow

1. Executive Dashboard.
2. Market Intelligence.
3. Slice & Dice Analysis.
4. Investment Strategy.
5. GIS Map.
6. Data Pipeline.
7. Price Prediction.
8. Legal/Planning RAG.

## Slide 7: Results

- Top opportunity districts.
- ROI and price/m² comparison.
- Prediction result with MAE/R².
- What-if future value, ROI, payback period, scenario projection.
- RAG response with sources.

## Slide 8: Information Systems Mapping

- MIS: reporting dashboards.
- DSS: prediction and recommendation.
- EIS: executive overview.
- TPS: transaction-proxy fact table.
- KWS: RAG/LLM knowledge assistant.
- OAS: reports, citations, demo documents.

## Slide 9: Conclusion

- PropertyVision supports data-driven investment decisions.
- The system integrates market, map, ETL, planning/legal context and AI.
- It is ready to replace public/cached sources with enterprise official data.

## Slide 10: Rubric Checklist

- Problem description.
- Method/tool/algorithm description.
- Application demo.
- Visualization and explanation.
- Conclusion.
- Presentation/demo quality.
- Clear delivery.

# PropertyVision UI/UX Design Specification

Tài liệu này mô tả toàn bộ project PropertyVision ở góc nhìn sản phẩm, giao diện và luồng dữ liệu. Mục tiêu là để team thiết kế UI/UX hiểu hệ thống có những thành phần nào, mỗi màn hình cần hiển thị gì, người dùng thao tác ra sao, dữ liệu đến từ đâu và nên ưu tiên thiết kế trải nghiệm thế nào.

## 1. Tổng Quan Sản Phẩm

PropertyVision là hệ thống web BI/DSS cho doanh nghiệp bất động sản. Hệ thống giúp lãnh đạo và bộ phận phân tích đầu tư:

- Theo dõi thị trường bất động sản theo khu vực, phân khúc, giá/m², ROI.
- Dự đoán giá bất động sản dựa trên dữ liệu đã xử lý.
- Mô phỏng What-If để đánh giá tác động của ngân sách, tăng trưởng và số năm nắm giữ.
- Dự phóng đa kịch bản 5-10 năm với confidence band.
- Xếp hạng khu vực nên đầu tư bằng điểm cơ hội.
- Kiểm tra rủi ro pháp lý/quy hoạch ở mức screening.
- Xem bản đồ phân tích khu vực.
- Chạy và theo dõi pipeline dữ liệu gần real-time.
- Hỏi trợ lý RAG/LLM về chiến lược, pháp lý, quy hoạch, ROI, rủi ro.
- Giải thích project theo các loại hệ thống thông tin doanh nghiệp: MIS, DSS, EIS, TPS, OAS, KWS.

Thông điệp sản phẩm:

> PropertyVision không chỉ là dashboard listing. Đây là hệ thống ra quyết định đầu tư bất động sản tích hợp Market Intelligence, GIS Planning, Realtime ETL, Price Prediction và Legal/Planning RAG.

## 2. Người Dùng Mục Tiêu

### 2.1. Executive / CEO / Ban lãnh đạo

Nhu cầu:

- Xem nhanh thị trường đang ở đâu.
- Biết khu nào nên ưu tiên đầu tư.
- Biết ROI trung bình, quy mô thị trường, rủi ro chính.
- Không muốn xem bảng dữ liệu quá chi tiết.

Giao diện nên ưu tiên:

- KPI rõ ràng.
- Ngôn ngữ kinh doanh.
- Ít thuật ngữ kỹ thuật.
- Kết luận và khuyến nghị nổi bật.

### 2.2. Business Analyst / BI Analyst

Nhu cầu:

- Lọc dữ liệu theo khu vực, loại tài sản, ROI, giá.
- So sánh quận/huyện và phân khúc.
- Xem bảng dữ liệu chi tiết.
- Kiểm tra nguồn dữ liệu, ETL log, confidence score.

Giao diện nên ưu tiên:

- Bộ lọc mạnh.
- Chart dễ đọc.
- Table có hierarchy rõ.
- Source/citation minh bạch.

### 2.3. Investment Manager

Nhu cầu:

- Xác định khu vực có cơ hội đầu tư tốt.
- Dự đoán giá hợp lý cho một tài sản.
- Kiểm tra rủi ro pháp lý/quy hoạch.
- Nhận đề xuất hành động: mở rộng danh mục, gom chọn lọc, kiểm soát rủi ro.

Giao diện nên ưu tiên:

- Strategy table.
- Prediction form.
- GIS Map.
- Risk badge.
- Recommendation badge.

### 2.4. Giảng viên / Hội đồng chấm demo

Nhu cầu:

- Hiểu bài toán.
- Thấy được công cụ, thuật toán, phương pháp.
- Xem demo ứng dụng chạy thật.
- Thấy trực quan hóa, phân tích, giải thích, kết luận.
- Thấy project có frontend/backend/API rõ ràng.

Giao diện nên ưu tiên:

- Có tab giải thích methodology.
- Có story demo rõ.
- Các module có tên dễ liên hệ với rubric.

## 3. Kiến Trúc Hệ Thống

### 3.1. Frontend

Tech stack:

- React
- Vite
- Recharts
- React Leaflet
- CSS custom

Frontend chạy tại:

```text
http://localhost:5173
```

Nếu port 5173 bị chiếm, Vite có thể chạy ở:

```text
http://localhost:5174
```

Frontend gọi backend thông qua API prefix:

```text
/api/...
```

Vite proxy chuyển request tới:

```text
http://localhost:8000
```

### 3.2. Backend

Tech stack:

- FastAPI
- Pandas
- SQLite
- scikit-learn
- sentence-transformers
- NearestNeighbors
- Ollama local LLM

Backend chạy tại:

```text
http://localhost:8000
```

### 3.3. Data Layer

Nguồn dữ liệu chính:

- `clean_data.csv`: dữ liệu bất động sản đã xử lý.
- `data/propertyvision.db`: SQLite warehouse.

Bảng trong SQLite hiện có:

- `dim_city`
- `dim_district`
- `dim_property_type`
- `fact_listings`
- `mart_district_monthly`
- `fact_transactions`
- `dim_planning_zone`
- `legal_documents`
- `etl_runs`

### 3.4. AI/ML Layer

Các lớp AI/ML:

- Random Forest price prediction.
- Legal/planning risk score feature.
- RAG document retrieval.
- Local LLM qua Ollama.

Model local:

- Primary: `qwen2.5:14b`
- Fallback: `llama3.1:latest`
- Fallback: `llama3:latest`

Nếu Ollama offline, hệ thống vẫn trả lời bằng retrieval fallback.

## 4. Navigation Tổng Thể

Phiên bản hiện tại đang triển khai theo dạng một dashboard với nhiều tab. Tuy nhiên định hướng thiết kế mong muốn là **multi-page enterprise web app** để sản phẩm trông đầy đủ, đa dạng và đúng đối tượng doanh nghiệp hơn.

Designer nên xem các tab hiện tại như các **module chức năng** và có thể tách thành nhiều trang riêng trong bản UI mới.

Ứng dụng có layout chính gồm:

- Sidebar bên trái.
- Header/topbar.
- Tab navigation.
- Main content area.

Các tab hiện tại:

1. `Tổng quan`
2. `Thị trường`
3. `Slice & Dice`
4. `Chiến lược`
5. `GIS Map`
6. `Data Pipeline`
7. `Dự đoán giá`
8. `RAG/LLM`
9. `MIS/DSS/EIS`
10. `Dữ liệu`

Thiết kế cần đảm bảo các tab này là first-class modules, không giống các section phụ. Mỗi tab nên có một mục đích rõ ràng, headline rõ ràng, và có thể demo độc lập.

## 4A. Multi-Page Information Architecture

### 4A.1. Mục tiêu chuyển sang nhiều trang

Web nên có nhiều trang để:

- Trông giống sản phẩm BI doanh nghiệp thật hơn.
- Giảm cảm giác “một dashboard nhồi nhiều tab”.
- Cho từng nhóm người dùng có khu vực làm việc riêng.
- Tăng độ đa dạng giao diện: dashboard, map, form, assistant, table, report, pipeline monitor, executive memo.
- Dễ demo theo story: từ tổng quan lãnh đạo đến phân tích chi tiết, mô phỏng quyết định và báo cáo kết luận.

### 4A.2. Sitemap đề xuất

```text
PropertyVision
├── 1. Executive Overview
├── 2. Market Intelligence
│   ├── Market Dashboard
│   ├── Slice & Dice
│   └── Segment Comparison
├── 3. Decision Lab
│   ├── Investment Strategy
│   ├── Price Prediction
│   ├── What-If Simulation
│   └── Scenario Projection
├── 4. GIS & Planning
│   ├── GIS Map
│   ├── Planning Zones
│   └── Legal/Planning Risk
├── 5. AI Analyst
│   ├── RAG/LLM Chat
│   ├── Retrieved Sources
│   └── Suggested Questions
├── 6. Data Operations
│   ├── ETL Pipeline
│   ├── Public Data Hub
│   └── Data Quality
├── 7. Data Explorer
│   ├── Listings Table
│   ├── Transaction Proxy
│   └── Export/Download
├── 8. Methodology & Baseline
│   ├── Problem & Method
│   ├── Data Dictionary
│   ├── Model Baseline
│   └── MIS/DSS/EIS Mapping
└── 9. Executive Report
    ├── Key Findings
    ├── Recommendations
    └── Presentation Mode
```

### 4A.3. Primary Navigation

Thiết kế navigation nên có 2 cấp:

1. Primary sidebar navigation cho page chính.
2. Secondary tabs hoặc segmented control bên trong từng page nếu page có nhiều submodule.

Primary nav đề xuất:

- Overview
- Market
- Decision Lab
- GIS Planning
- AI Analyst
- Data Ops
- Explorer
- Methodology
- Report

Không nên để quá nhiều tab ngang ở topbar vì sẽ dài và kém enterprise khi mở rộng.

### 4A.4. Page 1 - Executive Overview

Mục tiêu:

- Trang đầu tiên cho lãnh đạo.
- Trả lời: “Thị trường hiện tại thế nào, khu nào nên ưu tiên, rủi ro chính là gì?”

Nội dung:

- KPI cards:
  - Total Value.
  - Median Price.
  - Avg Price/m².
  - Avg ROI.
  - Best District.
  - Transaction Proxy.
- Trend chart giá và ROI.
- Donut/bar phân bổ vốn theo phân khúc.
- Executive recommendation callout.
- Top 3 opportunity districts.
- Top 3 risk watchlist.

Layout đề xuất:

- Header + status.
- KPI grid.
- 2-column chart row.
- Recommendation panel bên dưới.

### 4A.5. Page 2 - Market Intelligence

Mục tiêu:

- Trang cho analyst/business team phân tích thị trường.

Submodules:

- ROI theo khu vực.
- Giá/m² và thanh khoản proxy.
- Segment comparison.
- Top/bottom district table.

Nội dung:

- Bar chart ROI.
- Scatter chart price/m² vs listings.
- Table phân khúc.
- Filter context.
- Benchmark market vs filtered.

Layout đề xuất:

- Toolbar filter context.
- Chart grid.
- Table section.

### 4A.6. Page 3 - Slice & Dice

Mục tiêu:

- Trang BI enterprise đúng nghĩa.
- Cho phép cắt dữ liệu đa chiều.

Controls:

- Row dimension.
- Column dimension.
- Metric.
- Global filters.

Visuals:

- Benchmark cards.
- Bar chart top row segments.
- Pivot matrix.
- Top cross-segments table.

Design note:

- Đây là trang nên thiết kế giống BI workstation.
- Cần table/pivot dày dữ liệu nhưng vẫn dễ scan.
- Nên có “Save view” hoặc “Current view” trong bản design nếu muốn trông chuyên nghiệp hơn.

### 4A.7. Page 4 - Decision Lab

Mục tiêu:

- Trang DSS chính.
- Cho investment manager mô phỏng quyết định.

Submodules:

- Investment Strategy.
- Price Prediction.
- What-If Simulation.
- Scenario Projection.

Nội dung:

- Strategy matrix.
- Prediction form.
- What-if sliders:
  - Budget.
  - Growth %.
  - Years.
- Simulation KPI:
  - Future Value.
  - Capital Gain.
  - Cumulative ROI.
  - Annualized ROI.
  - Payback Period.
  - Investable Units.
- Scenario projection line chart:
  - Xấu.
  - Cơ sở.
  - Lạc quan.
  - Confidence band.

Layout đề xuất:

- Left panel: input form + sliders.
- Right panel: prediction result + decision metrics.
- Full-width chart phía dưới.

### 4A.8. Page 5 - GIS & Planning

Mục tiêu:

- Trang bản đồ và rủi ro quy hoạch/pháp lý.

Nội dung:

- Full map panel.
- Marker theo opportunity score.
- Color theo risk level.
- Side panel khi chọn district.
- Planning/risk cards.
- Source/citation list.

Design note:

- Map nên là thành phần trung tâm, không bị nhốt trong card nhỏ.
- Có legend rõ.
- Có risk filter.
- Popup nên ngắn; detail nên nằm trong side panel.

### 4A.9. Page 6 - AI Analyst

Mục tiêu:

- Trang chatbot RAG/LLM.
- Cho người dùng hỏi bằng tiếng Việt về chiến lược, ROI, quy hoạch, pháp lý.

Nội dung:

- Chat/question area.
- Suggested prompt chips.
- Answer panel.
- Citation/source cards.
- LLM status:
  - Ollama online.
  - Retrieval fallback.
- Retrieved context inspector.

Design note:

- Không nên giống chatbot casual.
- Nên giống “AI research analyst workspace”.
- Citation phải rõ để tăng độ tin cậy.

### 4A.10. Page 7 - Data Operations

Mục tiêu:

- Trang vận hành dữ liệu.
- Cho thấy hệ thống có ETL gần real-time và data governance.

Nội dung:

- ETL status.
- Refresh ETL CTA.
- Transaction proxy count.
- Planning zones count.
- Legal docs count.
- ETL run log.
- Public Data Hub source cards.
- Data quality indicators:
  - Records seen.
  - Records inserted.
  - Last updated.
  - Confidence score.

Design note:

- Trang này nên giống control room/operations monitor.
- Có status colors nhưng không quá rực.

### 4A.11. Page 8 - Data Explorer

Mục tiêu:

- Cho analyst xem dữ liệu chi tiết.

Nội dung:

- Listings table.
- Transaction proxy table.
- Search.
- Filters.
- Sort.
- Export CSV.
- Row detail drawer.

Design note:

- Table cần là trọng tâm.
- Không cần nhiều chart.
- Cần xử lý text dài trong địa chỉ.

### 4A.12. Page 9 - Methodology & Baseline

Mục tiêu:

- Trang giải thích bài toán, phương pháp, dữ liệu, model và hệ thống thông tin.
- Dùng để chấm rubric và trả lời câu hỏi kỹ thuật.

Nội dung:

- Problem statement.
- Architecture diagram.
- Data dictionary.
- KPI formulas.
- Opportunity score formula.
- Model baseline:
  - MAE.
  - R².
  - Features.
- RAG architecture:
  - sentence-transformers.
  - NearestNeighbors cosine similarity prototype.
  - Production migration: ChromaDB/FAISS/pgvector.
- MIS/DSS/EIS/TPS/OAS/KWS mapping.

Design note:

- Trang này có thể giống documentation inside product.
- Nên có cards/accordion cho từng nhóm nội dung.

### 4A.13. Page 10 - Executive Report

Mục tiêu:

- Trang tổng hợp để thuyết trình hoặc export report.

Nội dung:

- Key findings.
- Top opportunities.
- Risk watchlist.
- Recommended actions.
- What-if result summary.
- RAG generated memo.
- Data sources/citations.

Design note:

- Nên giống report/memo cho lãnh đạo.
- Có thể có “Presentation mode”.
- Có thể có “Export PDF” trong design tương lai, chưa nhất thiết implement ngay.

### 4A.14. Route Naming Đề Xuất

Nếu chuyển từ tab sang route, dùng:

```text
/overview
/market
/slice-dice
/decision-lab
/gis-planning
/ai-analyst
/data-ops
/explorer
/methodology
/executive-report
```

### 4A.15. Multi-Page Demo Flow

Flow demo mới:

1. `/overview`: mở đầu bằng KPI và executive recommendation.
2. `/market`: phân tích thị trường.
3. `/slice-dice`: chứng minh BI enterprise.
4. `/decision-lab`: What-If và projection, chứng minh DSS.
5. `/gis-planning`: bản đồ và rủi ro quy hoạch.
6. `/ai-analyst`: hỏi RAG/LLM.
7. `/data-ops`: chứng minh ETL và data governance.
8. `/methodology`: giải thích thuật toán, baseline, MIS/DSS/EIS.
9. `/executive-report`: kết luận.

### 4A.16. Ưu Tiên Thiết Kế Multi-Page

Nếu team thiết kế không đủ thời gian làm tất cả page, ưu tiên theo thứ tự:

1. Executive Overview.
2. Decision Lab.
3. Slice & Dice.
4. GIS & Planning.
5. AI Analyst.
6. Data Operations.
7. Methodology & Baseline.
8. Data Explorer.
9. Executive Report.

Lý do:

- Executive Overview giúp mở demo mạnh.
- Decision Lab là phần DSS ăn điểm nhất.
- Slice & Dice chứng minh BI doanh nghiệp.
- GIS/RAG/ETL làm project khác biệt.

## 5. Global Layout

### 5.1. Sidebar

Mục đích:

- Branding.
- Bộ lọc toàn cục.
- Thay đổi dữ liệu toàn bộ dashboard.

Nội dung sidebar:

- Logo/text `PV`.
- Tên app: `PropertyVision`.
- Subtitle: `BI bất động sản doanh nghiệp`.
- Multi-select khu vực.
- Multi-select loại tài sản.
- Range filter giá tối đa.
- Range filter ROI tối thiểu.

Component cần thiết kế:

- Brand block.
- Filter group.
- Chip multi-select.
- Range slider.
- Active state cho selected chips.
- Empty/all state.

Ghi chú UX:

- `selected = []` nghĩa là chọn tất cả.
- Nên có text nhỏ giải thích “Tất cả” khi không chọn cụ thể.
- Sidebar cần scroll riêng vì danh sách quận/huyện dài.

### 5.2. Topbar

Nội dung:

- Eyebrow: `Real Estate Decision Intelligence`.
- Main headline: `Dashboard chiến lược dự đoán giá và tối ưu danh mục`.
- Status pill: số tin sau lọc hoặc trạng thái loading.

Component:

- Product heading.
- Status badge.
- Loading state.

### 5.3. Tab Navigation

Tab list:

- Tổng quan
- Thị trường
- Chiến lược
- GIS Map
- Data Pipeline
- Dự đoán giá
- RAG/LLM
- MIS/DSS/EIS
- Dữ liệu

Yêu cầu thiết kế:

- Tab active phải nổi bật.
- Tab phải wrap tốt trên màn hình nhỏ.
- Không dùng style quá giống button CTA; đây là navigation chính.

## 6. Tab 1 - Tổng Quan

Tên tab:

```text
Tổng quan
```

Mục tiêu:

Cho lãnh đạo xem nhanh thị trường và tình hình đầu tư.

### 6.1. KPI Cards

KPI hiện có:

1. Tổng giá trị
2. Giá trung vị
3. Giá/m² TB
4. ROI trung bình
5. Khu ưu tiên
6. Transaction proxy

Dữ liệu từ:

```text
POST /api/analytics
```

Trường dữ liệu:

- `kpis.total_value`
- `kpis.median_price`
- `kpis.avg_price_m2`
- `kpis.avg_roi`
- `kpis.best_district`
- `kpis.best_score`
- `kpis.transaction_count`
- `kpis.avg_confidence`

Thiết kế card:

- Label nhỏ.
- Value lớn.
- Delta/secondary info nhỏ.
- Icon có thể thêm nếu muốn:
  - Tổng giá trị: money/building.
  - Giá trung vị: tag.
  - Giá/m²: ruler.
  - ROI: trending up.
  - Khu ưu tiên: map pin/star.
  - Transaction proxy: database.

### 6.2. Chart - Xu hướng giá và ROI

Loại chart hiện tại:

- Composed chart.
- Area cho giá trung bình theo tháng.
- Line cho ROI theo tháng.

Dữ liệu:

- `analytics.timeline`
- `date`
- `price_billion`
- `roi_pct`
- `listings`

Thiết kế:

- Cần dual-axis rõ ràng.
- Legend dễ đọc.
- Tooltip có format:
  - Giá: tỷ VND.
  - ROI: %.

### 6.3. Chart - Cơ cấu vốn theo phân khúc

Loại chart:

- Pie chart.

Dữ liệu:

- `analytics.types`
- Tính tỷ trọng theo `avg_price * listings`.

Thiết kế:

- Màu phân khúc phải phân biệt rõ.
- Label % không được chồng nhau.
- Có thể thay Pie thành Donut chart nếu đẹp hơn.

## 7. Tab 2 - Thị Trường

Tên tab:

```text
Thị trường
```

Mục tiêu:

Phân tích Market Intelligence theo khu vực và phân khúc.

### 7.1. Chart - ROI theo khu vực

Loại chart:

- Bar chart.

Dữ liệu:

- `analytics.districts`
- Sort theo `roi_pct` giảm dần.
- Hiển thị top 12.

Trường:

- `district`
- `roi_pct`

Thiết kế:

- Label quận/huyện cần đọc được.
- Có thể dùng horizontal bar nếu tên dài.
- Top ROI nên có màu nổi bật.

### 7.2. Chart - Giá/m² và thanh khoản proxy

Loại chart:

- Scatter chart.

Dữ liệu:

- `analytics.districts`

Trường:

- `price_m2_million`
- `listings`
- `district`

Ý nghĩa:

- Trục X: giá/m².
- Trục Y: số tin/listing count, dùng như proxy thanh khoản.

Thiết kế:

- Tooltip cần hiển thị tên khu vực.
- Nên có chú thích “listing count = liquidity proxy”.

## 8. Tab 3 - Slice & Dice

Tên tab:

```text
Slice & Dice
```

Mục tiêu:

Đây là module BI doanh nghiệp quan trọng. Người dùng có thể cắt dữ liệu theo nhiều chiều để trả lời câu hỏi quản trị như: ROI thay đổi thế nào theo khu vực và loại tài sản, phân khúc giá nào hiệu quả nhất, nhóm pháp lý nào có giá/m² tốt hơn.

API:

```text
POST /api/slice-dice
```

Chiều phân tích:

- Khu vực.
- Loại tài sản.
- Pháp lý.
- Nhóm giá.
- Nhóm diện tích.
- Nhóm ROI.

Metric:

- Số tin.
- Giá TB.
- Giá trung vị.
- Giá/m² TB.
- ROI TB.
- Tổng giá trị.
- Điểm cơ hội.

Component:

- Row dimension select.
- Column dimension select.
- Metric select.
- Filter context bar.
- Benchmark cards: filtered vs market.
- Bar chart theo dimension chính.
- Pivot matrix.
- Top cross-segments table.

Thiết kế:

- Đây nên là tab có cảm giác “enterprise BI” nhất.
- Pivot matrix phải đọc được, không trang trí quá nhiều.
- Benchmark filtered vs market cần nổi bật để giúp ra quyết định.
- Khi sample nhỏ, warning phải rõ nhưng không gây panic.

## 9. Tab 4 - Chiến Lược

Tên tab:

```text
Chiến lược
```

Mục tiêu:

Biến dữ liệu thành quyết định đầu tư.

### 8.1. Bảng Ma Trận Ưu Tiên Đầu Tư

Dữ liệu:

- `analytics.districts`
- Hiển thị top 15.

Cột:

- Khu vực
- Hành động
- Số tin
- Giá trung vị
- ROI
- Triệu/m²
- Điểm

Logic hành động:

- `opportunity_score >= 65`: Mở rộng danh mục.
- `roi_pct < 10`: Hạn chế giải ngân.
- Còn lại: Gom chọn lọc.

Thiết kế:

- Cột `Hành động` nên dùng badge.
- Cột `Điểm` nên có progress bar.
- Cần highlight top 3.
- Risk/action color:
  - Mở rộng danh mục: xanh.
  - Gom chọn lọc: xanh dương/cam.
  - Hạn chế giải ngân: đỏ/cam đậm.

## 10. Tab 5 - GIS Map

Tên tab:

```text
GIS Map
```

Mục tiêu:

Hiển thị bản đồ phân tích khu vực, kết hợp ROI, điểm cơ hội và rủi ro quy hoạch.

API:

```text
GET /api/map/districts
```

Response chính:

- `districts`
- `sources`

Mỗi district có:

- `district`
- `latitude`
- `longitude`
- `listings`
- `roi_pct`
- `price_m2_million`
- `opportunity_score`
- `risk_level`
- `planning_note`
- `recommendation`

### 9.1. Map Panel

Hiện tại dùng:

- Leaflet map.
- OpenStreetMap tile.
- CircleMarker.

Visual encoding:

- Marker size = `opportunity_score`.
- Marker color = `risk_level`.
  - low: xanh.
  - medium: cam.
  - high: đỏ.

Popup hiển thị:

- District.
- Opportunity score.
- ROI.
- Giá/m².
- Rủi ro quy hoạch.
- Planning note.
- Recommendation.

Thiết kế:

- Map cần chiếm diện tích lớn.
- Nên có legend:
  - Marker size = điểm cơ hội.
  - Màu = rủi ro quy hoạch.
- Popup cần gọn, dễ đọc, không quá dài.

### 9.2. Planning/Risk List

Mục tiêu:

Liệt kê top khu vực kèm ghi chú quy hoạch.

Card hiển thị:

- District.
- Recommendation.
- Planning note.
- ROI.
- Listing count.
- Risk level.

Thiết kế:

- Card list có scroll nếu dài.
- Risk level nên là badge.
- Recommendation nên là badge hoặc pill.

## 11. Tab 6 - Data Pipeline

Tên tab:

```text
Data Pipeline
```

Mục tiêu:

Chứng minh hệ thống có realtime ETL trong phạm vi demo.

API:

```text
GET /api/etl/status
POST /api/etl/run
POST /api/rag/reindex
```

### 10.1. Pipeline KPI Cards

KPI:

- Transaction proxy.
- Planning zones.
- Legal docs.

Dữ liệu:

- `etl.transaction_records`
- `etl.planning_zones`
- `etl.legal_documents`

### 10.2. Refresh ETL Button

CTA:

```text
Refresh ETL
```

Khi bấm:

1. Gọi `/api/etl/run`.
2. Gọi `/api/map/districts`.
3. Gọi `/api/rag/reindex`.
4. Gọi lại `/api/analytics`.

Trạng thái:

- Normal.
- Loading: `Đang refresh`.
- Success: cập nhật KPI/log.
- Error: hiển thị message.

Thiết kế:

- CTA nên nổi bật nhưng không quá marketing.
- Có thể thêm icon refresh/database.

### 10.3. ETL Log Table

Cột:

- Run
- Mode
- Status
- Seen
- Inserted
- Message

Dữ liệu:

- `etl.runs`

Ý nghĩa:

- `mode`: startup/manual/scheduled.
- `status`: success/error.
- `records_seen`: số bản ghi đọc được.
- `records_inserted`: số bản ghi mới sau incremental check.

Thiết kế:

- Table cần compact.
- `status=success` dùng badge xanh.
- `records_inserted=0` không phải lỗi, nghĩa là không có dữ liệu mới.

### 10.4. Public Data Hub

Dữ liệu:

- `etl.sources`

Mỗi source có:

- `name`
- `type`
- `url`
- `status`

Sources hiện tại:

- HCMGIS Portal.
- HCMGIS GeoNode registry.
- HCMC online land data platform.
- Cổng tra cứu quy hoạch TP.HCM.
- Kaggle HCMC Real Estate Data 2025.
- Kaggle House Pricing HCM.

Thiết kế:

- Source card/citation list.
- Có external link indicator.
- Status badge:
  - public-source.
  - cached-local-proxy.

## 12. Tab 7 - Dự Đoán Giá

Tên tab:

```text
Dự đoán giá
```

Mục tiêu:

Cho người dùng nhập thông số tài sản và nhận giá dự đoán.

API:

```text
POST /api/predict
```

### 11.1. Prediction Form

Input:

- Khu vực.
- Loại bất động sản.
- Pháp lý.
- Diện tích m².
- Phòng ngủ.
- WC.
- Số tầng.
- ROI kỳ vọng.

Payload:

```json
{
  "district": "Quận Tân Bình",
  "property_type": "Nhà hẻm, ngõ",
  "legal_documents": "Sổ hồng",
  "area": 70,
  "bedrooms": 3,
  "toilets": 3,
  "floors": 3,
  "roi_expected": 0.14
}
```

Thiết kế:

- Form nên chia nhóm:
  - Vị trí & loại tài sản.
  - Thông số vật lý.
  - Tài chính/rủi ro.
- CTA: `Dự đoán`.
- Có thể thêm default example.

### 11.2. Prediction Result

Response:

- `predicted_price`
- `lower_bound`
- `upper_bound`
- `price_per_m2`
- `market_median`
- `gap_pct`
- `planning_risk_score`
- `planning_risk_label`
- `model.mae`
- `model.r2`

Hiển thị:

- Giá dự đoán lớn nhất.
- Khoảng tham chiếu.
- Giá/m² suy ra.
- Chênh lệch với trung vị khu vực.
- Legal/planning risk.
- MAE/R².

Thiết kế:

- Result card nên có hierarchy rất rõ.
- Giá dự đoán là hero metric.
- Risk label có badge màu.
- MAE/R² nhỏ hơn, là thông tin kỹ thuật.

### 11.3. What-If Simulation

Mục tiêu:

Biến phần dự đoán thành Decision Support System thật sự. Người dùng không chỉ xem giá dự đoán tại một thời điểm mà còn mô phỏng hiệu quả đầu tư nếu thay đổi giả định kinh doanh.

API:

```text
POST /api/what-if
```

Input sliders:

- Ngân sách đầu tư, đơn vị tỷ VND.
- Tăng trưởng giá hằng năm, đơn vị %.
- Số năm nắm giữ, từ 1 đến 10 năm.

Output KPI:

- Future Value.
- Capital Gain.
- Cumulative ROI.
- Annualized ROI.
- Payback Period.
- Investable Units.

Thiết kế:

- Đây nên là phần nổi bật nhất của tab Dự đoán giá.
- Slider cần dễ chỉnh khi demo.
- KPI nên cập nhật ngay sau khi bấm `Chạy What-If DSS`.
- Payback period nên có badge hoặc highlight vì là chỉ số ra quyết định.

### 11.4. Dự Phóng Đa Kịch Bản

Mục tiêu:

Hiển thị forward projection 5-10 năm, thay vì chỉ point-in-time prediction.

Chart:

- Line chart 3 đường:
  - Xấu.
  - Cơ sở.
  - Lạc quan.
- Confidence band quanh kịch bản cơ sở.

Ý nghĩa:

- Xấu = tăng trưởng thấp hơn giả định 4%.
- Cơ sở = tăng trưởng người dùng chọn.
- Lạc quan = tăng trưởng cao hơn giả định 4%.

Thiết kế:

- 3 đường phải phân biệt màu rõ:
  - Xấu: đỏ/cam.
  - Cơ sở: xanh dương.
  - Lạc quan: xanh lá.
- Confidence band nên nhẹ, không che line chính.
- Tooltip format tiền VND/tỷ.

## 13. Tab 8 - RAG/LLM

Tên tab:

```text
RAG/LLM
```

Mục tiêu:

Cho người dùng hỏi trợ lý AI về thị trường, pháp lý, quy hoạch, ROI và chiến lược.

API:

```text
POST /api/assistant
```

### 12.1. Question Box

Default question:

```text
Nên ưu tiên khu vực nào để đầu tư với ROI tốt và rủi ro vừa phải?
```

Câu hỏi demo khác:

- `Quận Tân Bình có rủi ro quy hoạch gì?`
- `Nên ưu tiên khu vực nào nếu muốn ROI tốt và pháp lý an toàn?`
- `So sánh Bình Chánh và Thủ Đức về giá/m2, ROI và thanh khoản.`

Thiết kế:

- Textarea rộng.
- CTA `Phân tích`.
- Có thể thêm suggestion chips cho câu hỏi mẫu.

### 12.2. Answer Panel

Response:

- `answer`
- `sources`
- `model`
- `mode`
- `llm_available`
- `retrieved_context`
- `retrieval_time_ms`

Metadata hiển thị:

- Mode.
- Model.
- LLM online/fallback.
- Retrieval time.

Answer:

- Text tiếng Việt.
- Nên có format đoạn hoặc bullet nếu design xử lý được.

Sources:

- Title.
- Score.
- Content.
- Source name.
- Source URL.

Thiết kế:

- Source/citation phải nhìn rõ.
- Nên có collapsible source cards nếu dài.
- Nếu LLM offline, hiển thị badge `retrieval fallback`, không coi là lỗi.

## 14. Tab 9 - MIS/DSS/EIS

Tên tab:

```text
MIS/DSS/EIS
```

Mục tiêu:

Giải thích hệ thống theo rubric và theo môn học hệ thống thông tin quản lý.

API:

```text
GET /api/methodology
```

### 13.1. Business BI / DSS / EIS Section

Nội dung:

- Bài toán.
- Phương pháp.
- Data Coverage & Governance.

`methodology.problem`:

```text
Doanh nghiệp cần hệ thống MIS/DSS/EIS để dự đoán giá bất động sản, so sánh ROI, kiểm soát rủi ro pháp lý/quy hoạch và chọn chiến lược đầu tư.
```

Methods:

- BI dashboard.
- DSS scoring.
- Prediction.
- RAG.
- Realtime ETL.

### 13.2. Mapping Hệ Thống Thông Tin

Các card:

- MIS: báo cáo KPI, thị trường, phân khúc và pipeline dữ liệu.
- DSS: dự đoán giá, opportunity score, khuyến nghị đầu tư.
- EIS: executive dashboard cho lãnh đạo.
- KWS: RAG/LLM giúp khai thác tri thức pháp lý/quy hoạch.
- TPS: fact_transactions là lớp ghi nhận giao dịch/proxy giao dịch.
- OAS: demo script, citation và báo cáo hỗ trợ truyền thông nội bộ.

Thiết kế:

- Mỗi loại hệ thống nên là card riêng.
- Acronym lớn, giải thích ngắn.
- Có thể dùng màu/icon riêng nhưng không quá rực.

### 13.3. Executive Conclusion

Nội dung:

- PropertyVision tích hợp Market Intelligence, GIS Planning, Realtime ETL và Legal/Planning RAG.
- Hệ thống không chỉ xem dữ liệu listing mà còn có transaction proxy, source citation, data governance.
- Demo tập trung vào quyết định: chọn khu ưu tiên, kiểm tra rủi ro, dự đoán giá, đề xuất hành động.

Thiết kế:

- Nên là section kết luận nổi bật.
- Có thể dùng callout hoặc executive memo style.

## 15. Tab 10 - Dữ Liệu

Tên tab:

```text
Dữ liệu
```

Mục tiêu:

Cho analyst xem top tài sản ROI cao trong bộ lọc hiện tại.

Dữ liệu:

- `analytics.samples`

Cột:

- Địa chỉ.
- Khu vực.
- Loại.
- Giá.
- Diện tích.
- ROI.

Thiết kế:

- Table rõ ràng.
- Cột địa chỉ có thể dài, cần xử lý overflow.
- Có thể thêm search/export trong version sau.

## 16. API Inventory Cho Designer

Designer không cần code API, nhưng cần hiểu mỗi màn hình lấy dữ liệu từ đâu.

### 16.1. `GET /api/health`

Mục đích:

- Kiểm tra backend sống.

Response:

```json
{
  "status": "ok"
}
```

### 16.2. `GET /api/metadata`

Mục đích:

- Lấy danh sách filter option.

Response chính:

- `rows`
- `districts`
- `property_types`
- `legal_documents`
- `price_range`
- `area_range`
- `roi_range`

### 16.3. `POST /api/analytics`

Mục đích:

- Lấy toàn bộ dữ liệu dashboard sau filter.

Request:

```json
{
  "districts": [],
  "property_types": [],
  "price_min": null,
  "price_max": null,
  "area_min": null,
  "area_max": null,
  "roi_min": null,
  "roi_max": null
}
```

Response chính:

- `kpis`
- `timeline`
- `districts`
- `types`
- `risky`
- `samples`

### 16.4. `POST /api/slice-dice`

Mục đích:

- Phân tích slice-and-dice đa chiều cho doanh nghiệp.

Request:

```json
{
  "filters": {
    "districts": [],
    "property_types": [],
    "price_min": null,
    "price_max": null,
    "area_min": null,
    "area_max": null,
    "roi_min": null,
    "roi_max": null
  },
  "row_dimension": "district",
  "column_dimension": "Type of House",
  "metric": "avg_roi"
}
```

Response chính:

- `dimensions`
- `metrics`
- `rows`
- `matrix`
- `columns`
- `top_segments`
- `filter_context`
- `benchmark`

### 16.5. `POST /api/predict`

Mục đích:

- Dự đoán giá tài sản.

Response chính:

- `predicted_price`
- `lower_bound`
- `upper_bound`
- `price_per_m2`
- `gap_pct`
- `planning_risk_label`
- `model`

### 16.6. `POST /api/assistant`

Mục đích:

- RAG/LLM assistant.

Response chính:

- `answer`
- `sources`
- `model`
- `mode`
- `llm_available`
- `retrieval_time_ms`

### 16.7. `GET /api/etl/status`

Mục đích:

- Trạng thái pipeline.

Response chính:

- `transaction_records`
- `planning_zones`
- `legal_documents`
- `sources`
- `runs`

### 16.8. `POST /api/etl/run`

Mục đích:

- Chạy refresh ETL thủ công.

Response chính:

- `result`
- `status`

### 16.9. `GET /api/map/districts`

Mục đích:

- Dữ liệu bản đồ.

Response chính:

- `districts`
- `sources`

### 16.10. `GET /api/planning/zones`

Mục đích:

- Danh sách vùng quy hoạch/rủi ro pháp lý.

Response chính:

- `zones`
- `sources`

### 16.11. `GET /api/methodology`

Mục đích:

- Nội dung giải thích project.

Response chính:

- `problem`
- `data`
- `methods`
- `information_systems`
- `etl`

### 16.12. `GET /api/model-info`

Mục đích:

- Thông tin model dự đoán.

Response chính:

- `mae`
- `r2`
- `trained_rows`
- `features`
- `algorithm`

### 16.13. `POST /api/rag/reindex`

Mục đích:

- Rebuild index RAG.

Response chính:

- `status`
- `mode`
- `documents`

## 17. Data Model Tóm Tắt

### 17.1. `clean_data.csv`

Cột quan trọng:

- `Location`
- `Price`
- `Type of House`
- `Land Area`
- `Bedrooms`
- `Toilets`
- `Total Floors`
- `Main Door Direction`
- `Balcony Direction`
- `Legal Documents`
- `price_vnd`
- `area`
- `price_per_m2`
- `district`
- `purchase_price`
- `current_price`
- `ROI`
- `date`

### 17.2. `fact_transactions`

Mục đích:

- Lưu giao dịch/proxy giao dịch từ nguồn công khai/cache.

Trường:

- `transaction_id`
- `source_id`
- `transaction_date`
- `district`
- `property_type`
- `price_vnd`
- `area_sqm`
- `price_per_sqm`
- `legal_status`
- `roi`
- `source_name`
- `source_url`
- `confidence_score`
- `updated_at`

### 17.3. `dim_planning_zone`

Mục đích:

- Lưu lớp screening quy hoạch/rủi ro pháp lý theo khu vực.

Trường:

- `zone_id`
- `district`
- `latitude`
- `longitude`
- `zone_type`
- `risk_level`
- `description`
- `source_name`
- `source_url`
- `updated_at`

### 17.4. `legal_documents`

Mục đích:

- Nguồn tài liệu RAG.

Trường:

- `document_id`
- `title`
- `document_type`
- `district`
- `content`
- `source_name`
- `source_url`
- `updated_at`

### 17.5. `etl_runs`

Mục đích:

- Log pipeline.

Trường:

- `run_id`
- `source_name`
- `mode`
- `status`
- `records_seen`
- `records_inserted`
- `started_at`
- `finished_at`
- `message`

## 18. Visual Design Direction

### 17.1. Tinh thần giao diện

Nên là:

- Enterprise BI.
- Sạch, rõ, dễ scan.
- Tin cậy, không quá màu mè.
- Dành cho lãnh đạo và analyst.

Không nên:

- Giống landing page marketing.
- Dùng quá nhiều gradient.
- Dùng layout card trang trí quá dày.
- Dùng font quá lớn ở bảng/table.
- Dùng màu quá rực làm mất tính dữ liệu.

### 17.2. Palette đề xuất

Nền:

- `#f4f7fb`
- `#ffffff`

Text:

- `#17202a`
- `#526071`
- `#687384`

Primary:

- `#2563eb`

Positive:

- `#0f8a64`

Warning:

- `#d97706`

Risk:

- `#c2410c`

Accent:

- `#0891b2`
- `#7c3aed`

### 17.3. Component Style

Cards:

- Border radius khoảng 8px.
- Border nhẹ.
- Shadow rất nhẹ hoặc không cần.

Tables:

- Header nền nhạt.
- Row spacing vừa phải.
- Cần xử lý overflow.

Badges:

- Risk level.
- Action recommendation.
- LLM online/fallback.
- Source status.
- ETL status.

Charts:

- Có legend.
- Tooltip rõ.
- Axis label đọc được.
- Tránh label chồng nhau.

Map:

- Có legend.
- Popup compact.
- Marker color/radius có ý nghĩa.

## 19. UI States Cần Thiết Kế

### 18.1. Loading

Xuất hiện khi:

- App load metadata/analytics.
- Refresh ETL.
- Gửi câu hỏi RAG.
- Dự đoán giá.

Gợi ý:

- Skeleton KPI cards.
- Spinner nhỏ trong button.
- Status pill `Đang cập nhật`.

### 18.2. Empty State

Xuất hiện khi:

- Filter không còn dữ liệu.
- RAG không retrieve được source.
- Map không có district phù hợp.

Nội dung:

- Nói rõ “Không có dữ liệu phù hợp với bộ lọc hiện tại”.
- Gợi ý reset filter.

### 18.3. Error State

Xuất hiện khi:

- Backend offline.
- API lỗi.
- Ollama offline.

Phân biệt:

- Backend offline là lỗi nghiêm trọng.
- Ollama offline không phải lỗi nghiêm trọng vì có retrieval fallback.

### 18.4. Success State

Xuất hiện khi:

- ETL refresh xong.
- RAG reindex xong.
- Prediction trả kết quả.

Nên có:

- Toast hoặc inline confirmation.
- Timestamp update.

## 20. Demo Flow Cho Designer Hiểu Ưu Tiên Màn Hình

Thứ tự demo nên hỗ trợ:

1. Tổng quan: lãnh đạo nhìn KPI.
2. Thị trường: analyst xem ROI và giá/m².
3. Slice & Dice: doanh nghiệp cắt dữ liệu theo nhiều chiều để tìm phân khúc hiệu quả.
4. Chiến lược: DSS đưa ra khuyến nghị.
5. GIS Map: kiểm tra bối cảnh khu vực.
6. Data Pipeline: chứng minh hệ thống có dữ liệu cập nhật và source governance.
7. Dự đoán giá: nhập tài sản và nhận giá dự đoán.
8. RAG/LLM: hỏi về pháp lý/quy hoạch/chiến lược.
9. MIS/DSS/EIS: kết luận theo môn học và rubric.

Thiết kế nên làm cho flow này mượt, không cần người demo giải thích quá nhiều.

## 21. Nội Dung Text Quan Trọng Nên Giữ

Một số câu nên xuất hiện trong UI hoặc tài liệu:

```text
Market Intelligence
GIS Planning
Realtime Data Pipeline
Legal/Planning RAG
Executive Decision Center
Data Coverage & Governance
Transaction proxy
Opportunity score
Slice and dice analysis
Legal/planning risk
```

Không nên dùng câu:

```text
Hạn chế: dữ liệu listing...
```

Thay bằng:

```text
Data Coverage & Governance: hệ thống ghi nguồn, timestamp, confidence score và cache snapshot để sẵn sàng thay bằng nguồn dữ liệu chính thức của doanh nghiệp.
```

## 22. Rubric Mapping

### Mô tả đề tài/bài toán - 1 điểm

Nằm ở:

- README.
- Tab MIS/DSS/EIS.
- Demo intro.

### Mô tả công cụ/thuật toán/phương pháp - 2 điểm

Nằm ở:

- Tab MIS/DSS/EIS.
- `/api/methodology`.
- `/api/model-info`.
- README.

Nội dung:

- FastAPI.
- React.
- SQLite.
- Recharts.
- Leaflet.
- Random Forest.
- RAG.
- Ollama.
- ETL.

### Demo ứng dụng - 2 điểm

Nằm ở:

- Toàn bộ frontend.
- Demo script.

### Trực quan hóa kết quả/giải thích/phân tích - 2 điểm

Nằm ở:

- KPI cards.
- Charts.
- Map.
- Strategy table.
- Prediction result.
- RAG citations.

### Kết luận - 0.5 điểm

Nằm ở:

- Tab MIS/DSS/EIS, Executive Conclusion.

### Thuyết trình/demo - 2 điểm

Nằm ở:

- `DEMO_SCRIPT.md`.
- `PRESENTATION_OUTLINE.md`.

### Trình bày - 0.5 điểm

Phụ thuộc vào:

- Visual consistency.
- Layout rõ.
- Không lỗi text overflow.
- Demo flow mượt.

## 23. Gợi Ý Cải Tiến UI Cho Bản Thiết Kế Mới

### 23.0. Chuyển Từ Tab Dashboard Sang Multi-Page App

Ưu tiên thiết kế mới:

- Tách các tab hiện tại thành page riêng.
- Dùng sidebar navigation theo module.
- Mỗi page có headline, purpose, primary action và trạng thái riêng.
- Giữ global filters ở sidebar hoặc toolbar, nhưng cho phép từng page có local controls.
- Thêm breadcrumb hoặc page title để người dùng biết đang ở module nào.

Mapping từ tab hiện tại sang page:

| Tab hiện tại | Page đề xuất |
|---|---|
| Tổng quan | Executive Overview |
| Thị trường | Market Intelligence |
| Slice & Dice | Slice & Dice |
| Chiến lược + Dự đoán giá | Decision Lab |
| GIS Map | GIS & Planning |
| Data Pipeline | Data Operations |
| RAG/LLM | AI Analyst |
| MIS/DSS/EIS | Methodology & Baseline |
| Dữ liệu | Data Explorer |

### 22.1. Sidebar

Hiện tại sidebar hoạt động nhưng có thể nâng cấp:

- Thêm nút `Reset filters`.
- Thêm counter số filter đang active.
- Nhóm filter thành accordion nếu màn hình nhỏ.

### 22.2. Dashboard

Có thể cải tiến:

- KPI cards có icon.
- Khu ưu tiên có badge `Top opportunity`.
- Transaction proxy có tooltip giải thích.

### 22.3. GIS Map

Có thể cải tiến:

- Legend riêng.
- Search district.
- Side panel khi click marker.
- Risk filter.

### 22.4. Data Pipeline

Có thể cải tiến:

- Timeline view cho ETL run.
- Source status cards.
- Progress indicator khi refresh.

### 22.5. RAG/LLM

Có thể cải tiến:

- Suggested prompt chips.
- Citation cards collapsible.
- Display markdown answer.
- LLM online/offline indicator ở header.

### 22.6. MIS/DSS/EIS

Có thể cải tiến:

- Diagram mapping hệ thống thông tin.
- Flow chart: Data -> ETL -> BI -> ML -> RAG -> Decision.

## 24. File Liên Quan Trong Repo

Frontend:

- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `frontend/vite.config.js`
- `frontend/package.json`

Backend:

- `backend/main.py`
- `backend/__init__.py`

Data:

- `clean_data.csv`
- `data/propertyvision.db`

Docs:

- `README.md`
- `DEMO_SCRIPT.md`
- `PRESENTATION_OUTLINE.md`
- `UI_DESIGN_SPEC.md`

Entry note:

- `app.py`

## 25. Chạy Demo

Terminal 1:

```bash
cd "/Users/springwang/Library/Mobile Documents/com~apple~CloudDocs/juniorYear/BI/PropertyVision"
uvicorn backend.main:app --reload
```

Terminal 2:

```bash
cd "/Users/springwang/Library/Mobile Documents/com~apple~CloudDocs/juniorYear/BI/PropertyVision/frontend"
npm run dev
```

Ollama nếu muốn demo LLM thật:

```bash
ollama serve
ollama run qwen2.5:14b
```

Mở:

```text
http://localhost:5173
```

Nếu port 5173 bị chiếm, xem terminal frontend để lấy port mới, ví dụ:

```text
http://localhost:5174
```

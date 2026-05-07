# PropertyVision Baseline Document

Baseline này dùng để trình bày phần nền tảng dữ liệu, chỉ số, thuật toán và kết quả định lượng của PropertyVision. Đây là tài liệu nên đưa kèm khi demo để người chấm thấy rõ hệ thống không chỉ có giao diện mà còn có định nghĩa nghiệp vụ và mô hình đo lường.

## 1. Business Problem

Doanh nghiệp bất động sản cần một hệ thống BI/DSS/EIS để:

- Theo dõi thị trường theo khu vực và phân khúc.
- Định giá bất động sản dựa trên dữ liệu.
- So sánh ROI, giá/m², thanh khoản proxy và rủi ro pháp lý/quy hoạch.
- Mô phỏng kịch bản đầu tư trước khi ra quyết định.
- Dùng RAG/LLM để giải thích kết quả và truy xuất ngữ cảnh pháp lý/quy hoạch.

## 2. Dataset Baseline

Nguồn dữ liệu chính:

- `clean_data.csv`
- Số dòng: `23,722`
- SQLite warehouse: `data/propertyvision.db`
- Transaction proxy sau ETL: `23,722`

Nguồn bổ sung/citation:

- HCMGIS Portal: https://portal.hcmgis.vn/
- HCMGIS/GeoNode registry: https://dateno.io/registry/catalog/cdi00001949/
- HCMC land data platform reference: https://vietnam.opendevelopmentmekong.net/news/hcmc-launches-online-land-data-platform/
- HCMC planning lookup portal: https://thongtinquyhoach.hochiminhcity.gov.vn
- Kaggle HCMC Real Estate Data 2025: https://www.kaggle.com/datasets/cnglmph/ho-chi-minh-city-real-estate-data-2025
- Kaggle House Pricing HCM: https://www.kaggle.com/datasets/trnduythanhkhttt/housepricinghcm/data

## 3. Data Dictionary

| Field | Meaning | Business Use |
|---|---|---|
| `Location` | Địa chỉ/vị trí dạng text | Hiển thị dữ liệu chi tiết, trích xuất phường/xã |
| `Price` | Giá gốc dạng text | Đối chiếu dữ liệu ban đầu |
| `Type of House` | Loại bất động sản | Slice-and-dice theo phân khúc |
| `Land Area` | Diện tích gốc dạng text | Đối chiếu dữ liệu ban đầu |
| `Bedrooms` | Số phòng ngủ dạng text | Feature dự đoán giá |
| `Toilets` | Số WC dạng text | Feature dự đoán giá |
| `Total Floors` | Số tầng | Feature dự đoán giá |
| `Main Door Direction` | Hướng cửa chính | Biến bổ sung cho phân tích phong thủy/niche |
| `Balcony Direction` | Hướng ban công | Biến bổ sung |
| `Legal Documents` | Tình trạng pháp lý | Risk screening, prediction feature |
| `price_vnd` | Giá hiện tại đã chuẩn hóa VND | KPI, prediction target |
| `area` | Diện tích chuẩn hóa m² | Prediction feature, price/m² |
| `price_per_m2` | Đơn giá/m² = `price_vnd / area` | So sánh định giá giữa khu vực/phân khúc |
| `district` | Quận/huyện | Chiều phân tích chính |
| `purchase_price` | Giá mua/giá vốn ước tính trong dataset | Tính ROI |
| `current_price` | Giá hiện tại | Tính ROI |
| `ROI` | Return on Investment = `(current_price - purchase_price) / purchase_price` | Đánh giá hiệu quả đầu tư |
| `date` | Ngày quan sát | Trend/time-series |

## 4. KPI Definitions

### Total Value

```text
total_value = sum(price_vnd)
```

Ý nghĩa: quy mô giá trị thị trường trong bộ lọc hiện tại.

### Median Price

```text
median_price = median(price_vnd)
```

Ý nghĩa: mức giá đại diện, ít bị ảnh hưởng bởi outlier hơn giá trung bình.

### Average Price per m²

```text
avg_price_m2 = mean(price_per_m2)
```

Ý nghĩa: so sánh mặt bằng định giá giữa quận/huyện và phân khúc.

### ROI

```text
ROI = (current_price - purchase_price) / purchase_price
ROI % = ROI * 100
```

Ý nghĩa: tỷ suất sinh lời trên giá vốn.

### Transaction Proxy

`fact_transactions` lưu dữ liệu listing/time-series công khai như proxy giao dịch. Mỗi bản ghi có:

- `source_id` để chống nạp trùng.
- `source_name`, `source_url` để citation.
- `confidence_score` để thể hiện độ tin cậy của proxy.

## 5. Opportunity Score Definition

Điểm cơ hội dùng cho DSS ranking:

```text
opportunity_score =
  normalized(avg_roi) * 0.42
  + normalized(listings) * 0.18
  + inverse_normalized(avg_price_m2) * 0.22
  + inverse_normalized(volatility) * 0.18
```

Ý nghĩa:

- ROI cao hơn → tốt hơn.
- Listing count cao hơn → thanh khoản proxy tốt hơn.
- Giá/m² thấp hơn → còn dư địa mua tốt hơn.
- Biến động ROI thấp hơn → rủi ro ổn định hơn.

Điểm được scale về `0-100`.

## 6. Model Baseline

Model hiện tại:

```text
RandomForestRegressor with legal/planning risk feature
```

Target:

```text
log1p(price_vnd)
```

Features:

- `district`
- `Type of House`
- `Legal Documents`
- `area`
- `bedrooms_num`
- `toilets_num`
- `floor_num`
- `price_per_m2`
- `ROI`
- `planning_risk_score`

Train/test:

- Test size: `20%`
- Random state: `42`

Kết quả định lượng baseline:

| Metric | Value |
|---|---:|
| Rows trained | `23,722` |
| MAE | `71,462,359 VND` |
| R² | `0.9317` |
| Median price | `4.66 tỷ VND` |
| Average ROI | `14.60%` |
| Top opportunity district | `Quận 6` |
| Top opportunity score | `67.52 / 100` |

## 7. What-If Simulation Baseline

What-If Simulation biến model thành DSS thực sự. Người dùng thay đổi 3 biến:

- Ngân sách đầu tư.
- Tăng trưởng giá hằng năm.
- Số năm nắm giữ.

Output:

- Future Value.
- Capital Gain.
- Cumulative ROI.
- Annualized ROI.
- Payback Period.
- Investable Units.

Công thức:

```text
future_value = budget * (1 + annual_growth_pct / 100) ^ years
capital_gain = future_value - budget
cumulative_roi_pct = capital_gain / budget * 100
annualized_roi_pct = ((future_value / budget) ^ (1 / years) - 1) * 100
annual_cash_yield = budget * roi_expected
payback_years = budget / (annual_cash_yield + average_annual_capital_gain)
```

## 8. Multi-Scenario Projection

Hệ thống dự phóng 5-10 năm theo 3 kịch bản:

- Xấu: `growth - 4%`
- Cơ sở: `growth`
- Lạc quan: `growth + 4%`

Confidence band:

```text
confidence_width = MAE * sqrt(year) * 1.25
confidence_low = base_value - confidence_width
confidence_high = base_value + confidence_width
```

Ý nghĩa: đây là dải bất định minh họa cho demo DSS, dựa trên sai số MAE của model.

## 9. RAG Architecture Baseline

Prototype hiện tại:

- Document sources: BI summaries, planning zones, legal documents, public-source notes.
- Embedding: `sentence-transformers`.
- Retrieval: `sklearn.neighbors.NearestNeighbors`.
- Similarity: cosine similarity.
- Generation: Ollama local LLM.

Giải thích khi được hỏi:

> Trong prototype, chúng tôi dùng NearestNeighbors để thực hiện cosine similarity search trên embedding matrix. Đây là kiến trúc RAG hợp lệ cho demo/local prototype vì dữ liệu nhỏ và cần dễ triển khai. Khi production, retrieval layer sẽ migrate sang vector database chuyên dụng như ChromaDB, FAISS, Milvus hoặc pgvector để hỗ trợ indexing lớn, persistence, metadata filtering và scaling.

Fallback:

- Nếu Ollama offline, hệ thống vẫn trả retrieved context và citation.
- UI hiển thị mode `retrieval-fallback`.

## 10. Baseline Demo Claims

Có thể nói trong thuyết trình:

- “Hệ thống có 23,722 bản ghi sau xử lý.”
- “ETL đã tạo 23,722 transaction proxy có source/citation.”
- “Model dự đoán giá đạt R² khoảng 0.932 và MAE khoảng 71.5 triệu VND.”
- “Khu vực có điểm cơ hội cao nhất trong baseline là Quận 6.”
- “What-If Simulation giúp chuyển dashboard từ BI báo cáo sang DSS hỗ trợ quyết định.”
- “RAG dùng NearestNeighbors cho prototype và có lộ trình production sang ChromaDB/FAISS.”


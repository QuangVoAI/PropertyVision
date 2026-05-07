# PropertyVision Demo Script

## 1. Problem

PropertyVision giải quyết bài toán doanh nghiệp cần ra quyết định đầu tư bất động sản dựa trên dữ liệu. Thay vì chỉ xem từng listing riêng lẻ, hệ thống tổng hợp thị trường, transaction proxy, GIS, pháp lý/quy hoạch, dự đoán giá và RAG/LLM.

## 2. Executive Dashboard

Mở `http://localhost:5173`.

Nói:

> Đây là màn hình Executive Decision Center. Lãnh đạo có thể xem tổng giá trị thị trường, giá trung vị, giá/m², ROI trung bình, khu vực ưu tiên và số transaction proxy đã ingest.

Demo:

- Dùng filter khu vực hoặc loại tài sản.
- Chỉ ra KPI thay đổi theo filter.
- Chỉ ra xu hướng giá và ROI.

## 3. Market Intelligence

Nói:

> Tab Thị trường giúp so sánh ROI, giá/m² và thanh khoản proxy giữa các quận/huyện. Đây là chức năng MIS: tổng hợp và báo cáo thông tin quản trị.

Demo:

- Mở tab Thị trường.
- Chỉ ra top ROI và scatter giá/m² - số tin.

## 4. Slice & Dice Analysis

Nói:

> Đây là chức năng BI doanh nghiệp chuẩn: slice and dice. Người dùng có thể đổi chiều phân tích theo khu vực, loại tài sản, pháp lý, nhóm giá, nhóm diện tích hoặc nhóm ROI để xem metric thay đổi thế nào.

Demo:

- Mở tab Slice & Dice.
- Chọn Row dimension = Khu vực.
- Chọn Column dimension = Loại tài sản.
- Chọn Metric = ROI TB hoặc Điểm cơ hội.
- Chỉ ra benchmark filtered vs market.
- Chỉ ra pivot matrix và top cross-segments.

## 5. Investment Strategy

Nói:

> Đây là lớp DSS. Hệ thống không chỉ báo cáo mà còn tính opportunity score và đề xuất hành động như mở rộng danh mục, gom chọn lọc, hoặc kiểm soát rủi ro.

Demo:

- Mở tab Chiến lược.
- Chọn 1-2 khu vực có điểm cao.

## 6. GIS Map

Nói:

> PropertyVision tích hợp lớp GIS Planning. Marker càng lớn thì điểm cơ hội càng cao; màu thể hiện rủi ro quy hoạch/pháp lý ở mức screening.

Demo:

- Mở GIS Map.
- Click marker.
- Đọc popup: ROI, giá/m², risk level, planning note, recommendation.

## 7. Data Pipeline

Nói:

> Đây là realtime ETL trong phạm vi demo. Hệ thống có manual refresh, scheduled refresh, incremental ingest bằng source_id để tránh nạp trùng, và log ETL.

Demo:

- Mở Data Pipeline.
- Bấm `Refresh ETL`.
- Chỉ ra transaction proxy, planning zones, legal docs, ETL logs.
- Chỉ ra Public Data Hub với citation/source.

## 8. Price Prediction

Nói:

> Mô hình Random Forest dự đoán giá bất động sản từ khu vực, loại tài sản, pháp lý, diện tích, phòng, tầng, ROI kỳ vọng và legal/planning risk score. Phần này không chỉ là prediction mà còn là Decision Support vì có What-If Simulation.

Demo:

- Mở Dự đoán giá.
- Nhập Quận Tân Bình, Nhà hẻm/ngõ, diện tích 70m².
- Chỉnh 3 slider: ngân sách, tăng trưởng %, số năm.
- Bấm `Chạy What-If DSS`.
- Giải thích giá dự đoán, khoảng tham chiếu, R², MAE và planning risk.
- Giải thích Future Value, ROI, payback period.
- Chỉ ra line chart 3 kịch bản xấu/cơ sở/lạc quan và confidence band.

## 9. Legal/Planning RAG

Nói:

> Đây là lớp KWS/AI. RAG retrieve dữ liệu BI, legal documents, planning zones, sau đó gọi local LLM qua Ollama để trả lời có citation.

Câu hỏi mẫu:

- `Quận Tân Bình có rủi ro quy hoạch gì?`
- `Nên ưu tiên khu vực nào nếu muốn ROI tốt và pháp lý an toàn?`
- `So sánh Bình Chánh và Thủ Đức về giá/m2, ROI và thanh khoản.`

Demo:

- Mở RAG/LLM.
- Gõ câu hỏi.
- Chỉ ra Mode, Model, LLM online/fallback, sources, citation.

## 10. MIS/DSS/EIS Conclusion

Nói:

> PropertyVision là hệ thống MIS/DSS/EIS: MIS để báo cáo, DSS để hỗ trợ quyết định, EIS cho lãnh đạo, KWS cho khai thác tri thức bằng RAG/LLM, TPS là lớp transaction proxy, OAS là phần báo cáo và citation hỗ trợ truyền thông nội bộ.

Kết luận:

> Hệ thống giúp doanh nghiệp chuyển từ quyết định cảm tính sang quyết định dựa trên dữ liệu, bản đồ, pháp lý/quy hoạch, mô hình dự đoán và giải thích bằng AI.

# PropertyVision BI x RAG

PropertyVision BI là nền tảng **decision intelligence** cho bất động sản tại **TP.HCM** và **Hà Nội**.
Repo này kết hợp dashboard BI, dự đoán giá, mô phỏng đầu tư, bản đồ quy hoạch và trợ lý AI/RAG phục vụ báo cáo điều hành.

## Chạy nhanh

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Khi upload lên Hugging Face Space

- Dùng `Dockerfile` ở root repo
- App sẽ chạy trên port `7860`
- Frontend build sẽ được serve cùng backend FastAPI

## Tính năng chính

- Tổng quan điều hành
- Phân tích thị trường
- Phân tích đa chiều
- Mô phỏng đầu tư
- Bản đồ quy hoạch
- Trợ lý phân tích AI/RAG
- Báo cáo định kỳ kiểu executive

## Dữ liệu

- Dataset chính: `datasets/clean_dataset.csv`
- Nguồn dataset trên Hugging Face: `SpringWang08/hanoi-hcmc-real-estate`
- Có thêm lớp dữ liệu metro impact cho TP.HCM và Hà Nội

## Lưu ý

- Nếu không có token Hugging Face, app vẫn chạy ở chế độ retrieval-first.
- Muốn có câu trả lời AI đầy đủ hơn, đặt biến `HF_TOKEN` và bật hosted Qwen.


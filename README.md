# PropertyVision BI

PropertyVision là web app BI cho phân tích bất động sản, dự đoán giá, ROI, quy hoạch và trợ lý hỏi đáp dữ liệu.

Repo này đã được dọn lại để **clone về là chạy được**. Dataset chính được ưu tiên tải trực tiếp từ Hugging Face, nên máy clone mới không bắt buộc phải có sẵn file CSV local.

## Cấu trúc

```text
PropertyVision/
├── backend/                  FastAPI API
├── frontend/                 React + Vite UI
├── data/                     SQLite demo database
├── datasets/
│   ├── processed/            Dataset chính để app chạy
│   └── raw/                  Dataset gốc trước khi hợp nhất
├── docs/                     Tài liệu dự án
├── notebooks/                Notebook xử lý dữ liệu
├── app.py                    Gợi ý lệnh chạy nhanh
├── README.md
└── requirements.txt
```

## File quan trọng

- `backend/main.py`: backend chính của hệ thống.
- `frontend/src/main.jsx`: giao diện dashboard.
- `datasets/processed/clean_dataset.csv`: fallback dataset local nếu không tải được từ Hugging Face.
- `data/propertyvision.db`: SQLite dùng cho planning, ETL và dữ liệu phát sinh khi chạy app.
- `docs/BASELINE.md`: baseline kỹ thuật.
- `docs/DEMO_SCRIPT.md`: kịch bản demo.
- `docs/PRESENTATION_OUTLINE.md`: khung thuyết trình.
- `docs/UI_DESIGN_SPEC.md`: đặc tả UI.

## Chạy dự án

### Backend

macOS/Linux:

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

Backend chạy tại `http://localhost:8000`.

Khi khởi động:

- app sẽ ưu tiên tải dataset từ Hugging Face repo `SpringWang08/hanoi-hcmc-real-estate`
- nếu tải lỗi nhưng máy vẫn có `datasets/processed/clean_dataset.csv`, app sẽ dùng file local
- nếu cả hai đều không có, backend mới fallback sang dữ liệu raw trong `datasets/raw/`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend chạy tại `http://localhost:5173`.

## Dữ liệu

- App ưu tiên đọc dataset từ Hugging Face:
  `https://huggingface.co/datasets/SpringWang08/hanoi-hcmc-real-estate`
- Fallback local là `datasets/processed/clean_dataset.csv`.
- Hai file trong `datasets/raw/` được giữ lại làm nguồn gốc tham chiếu và dự phòng.
- Một phần trường của dữ liệu Hà Nội đã được chuẩn hóa/fill theo rule-based preprocessing để thống nhất schema phục vụ demo.

Nếu muốn chạy hoàn toàn offline, chỉ cần giữ sẵn:

```text
datasets/processed/clean_dataset.csv
```

Nếu chạy online bình thường sau khi clone, bạn không cần tự tải CSV thủ công.

## Tính năng chính

- Dashboard KPI thị trường bất động sản.
- Phân tích district và property type.
- Dự đoán giá bằng Random Forest.
- What-if simulation và future recommendation.
- GIS/planning map.
- Assistant với retrieval fallback và hỗ trợ Ollama khi có local model.

## Tài liệu

- [BASELINE.md](docs/BASELINE.md)
- [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)
- [PRESENTATION_OUTLINE.md](docs/PRESENTATION_OUTLINE.md)
- [UI_DESIGN_SPEC.md](docs/UI_DESIGN_SPEC.md)

## Ghi chú dọn repo

- Đã bỏ các file trùng hoặc file tạm như `README 2.md`, `backend/main 2.py`, `merge_datasets.py`.
- Repo hiện chỉ giữ một `README.md` làm đầu mối hướng dẫn chính.

## Quy trình nhanh sau khi clone

1. Clone repo.
2. Tạo virtual environment.
3. `pip install -r requirements.txt`
4. Chạy `uvicorn backend.main:app --reload`
5. Mở terminal khác, vào `frontend/`, chạy `npm install` rồi `npm run dev`
6. Mở `http://localhost:5173`

# PropertyVision BI

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.x-blue)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 📋 Giới thiệu dự án

PropertyVision là một hệ thống **Business Intelligence và Decision Support** cấp doanh nghiệp dành cho lĩnh vực bất động sản tại TP.HCM. Nền tảng tích hợp phân tích thị trường, quy hoạch địa lý, mô hình dự đoán, và những insight được hỗ trợ bởi AI để giúp đưa ra quyết định đầu tư dựa trên dữ liệu.

### Tính năng chính

- 📊 **Bảng điều khiển quản lý**: KPI thực tế, chỉ số ROI, phân tích giá trị thị trường
- 🗺️ **Tích hợp bản đồ GIS**: Hình dung quy hoạch và rủi ro theo quận
- 🤖 **Trợ lý AI**: RAG pháp lý/quy hoạch với hỗ trợ LLM cục bộ (Ollama)
- 🔮 **Dự đoán giá**: Mô hình Random Forest với các yếu tố rủi ro
- 📈 **Mô phỏng What-If**: Dự báo đa tình huống với khoảng tin cậy
- 🔍 **Thông tin thị trường**: Phân tích đa chiều theo quận, loại hình bất động sản, mức giá
- 🔄 **ETL thực tế**: Quy trình dữ liệu tự động và phục hợp tăng dần
- 📱 **Giao diện đáp ứng**: Frontend React + Vite với hình dung tương tác

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

### 1. Clone & Thiết lập

```bash
git clone https://github.com/QuangVoAI/PropertyVision.git
cd PropertyVision

# Tạo môi trường ảo
python -m venv .venv
source .venv/bin/activate  # Trên Windows: .venv\Scripts\activate
```

### 2. Cài đặt dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Khởi động dịch vụ

**Terminal 1 - Backend:**
```bash
uvicorn backend.main:app --reload
# Backend tại: http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Frontend tại: http://localhost:5173
```

**Terminal 3 - LLM cục bộ (Tùy chọn):**
```bash
ollama serve
ollama run qwen2.5:14b
```

> **Lưu ý**: Nếu Ollama không có sẵn, RAG sẽ vẫn hoạt động với các mô hình dự phòng (`llama3.1`, `llama3`). Nếu không có LLM nào, hệ thống sẽ trả về bối cảnh được lấy với các trích dẫn.

---

## 📁 Cấu trúc dự án

```
PropertyVision/
├── backend/
│   ├── __init__.py
│   └── main.py              # Ứng dụng FastAPI
├── frontend/
│   ├── src/
│   │   ├── main.jsx         # React entry point
│   │   └── styles.css       # Kiểu toàn cầu
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── data/
│   └── propertyvision.db    # Database SQLite
├── requirements.txt         # Các dependency Python
├── README.md               # Tệp này
├── BASELINE.md             # Thông số kỹ thuật
├── DEMO_SCRIPT.md          # Hướng dẫn demo
└── PRESENTATION_OUTLINE.md # Hướng dẫn trình bày
```

---

## 🎯 Các module chính

### Dashboard & Phân tích
- **Bảng điều khiển quản lý**: Chỉ số chính, phân tích ROI, giá trị thị trường, quận hứa hẹn nhất
- **Thông tin thị trường**: Phân tích so sánh theo quận và loại hình bất động sản
- **Phân tích Slice & Dice**: Phân tích OLAP đa chiều

### Tính năng nâng cao
- **Chiến lược đầu tư**: Chỉ số cơ hội và engine đề xuất
- **Bản đồ GIS**: Hình dung quy hoạch và rủi ro tương tác
- **Dự đoán giá**: Ước tính giá được hỗ trợ bởi ML với đánh giá rủi ro
- **Mô phỏng What-If**: Lập kế hoạch tình huống với các tham số ngân sách và tăng trưởng
- **Dự báo đa tình huống**: Dự báo 5-10 năm (bi quan/cơ bản/lạc quan)
- **RAG Pháp lý/Quy hoạch**: AI hội thoại với truy xuất tài liệu

### Quản lý dữ liệu
- **Quy trình dữ liệu**: Làm mới thủ công/theo lịch trình với ghi nhật ký ETL
- **Phục hợp tăng dần**: Đồng bộ hóa dữ liệu proxy giao dịch
- **Ánh xạ MIS/DSS/EIS**: Khung hệ thống thông tin doanh nghiệp

---

## 🔌 Các điểm cuối API

| Phương thức | Điểm cuối | Mục đích |
|--------|----------|---------|
| `GET` | `/api/health` | Kiểm tra sức khỏe |
| `GET` | `/api/metadata` | Siêu dữ liệu hệ thống |
| `POST` | `/api/analytics` | Truy vấn phân tích |
| `POST` | `/api/slice-dice` | Phân tích đa chiều |
| `POST` | `/api/predict` | Dự đoán giá |
| `POST` | `/api/what-if` | Engine mô phỏng |
| `POST` | `/api/assistant` | Q&A dựa trên RAG |
| `GET` | `/api/map/districts` | Dữ liệu quận GIS |
| `GET` | `/api/planning/zones` | Dữ liệu vùng quy hoạch |
| `POST` | `/api/etl/run` | Kích hoạt quy trình dữ liệu |
| `GET` | `/api/etl/status` | Trạng thái công việc ETL |

Xem `BASELINE.md` để biết tài liệu API chi tiết.

---

## 📊 Nguồn dữ liệu

Hệ thống tích hợp dữ liệu công khai và mã nguồn mở:

- **Cổng thông tin HCMGIS**: https://portal.hcmgis.vn/
- **Cổng thông tin quy hoạch TP.HCM**: https://thongtinquyhoach.hochiminhcity.gov.vn
- **Bộ dữ liệu Kaggle**:
  - [Dữ liệu bất động sản HCMC 2025](https://www.kaggle.com/datasets/cnglmph/ho-chi-minh-city-real-estate-data-2025)
  - [Định giá nhà ở HCM](https://www.kaggle.com/datasets/trnduythanhkhttt/housepricinghcm/data)

---

## 📚 Tài liệu

- **`BASELINE.md`**: Từ điển dữ liệu, công thức KPI, thông số kỹ thuật, ghi chú kiến trúc
- **`DEMO_SCRIPT.md`**: Hướng dẫn demo từng bước
- **`PRESENTATION_OUTLINE.md`**: Cấu trúc trình bày và các ý chính
- **`UI_DESIGN_SPEC.md`**: Thông số kỹ thuật UI/UX

---

## 🏗️ Kiến trúc

```
┌─────────────────────────────────────┐
│   Frontend React (Vite)             │
│   - Bảng điều khiển, Biểu đồ, Bản đồ          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Backend FastAPI                   │
│   - Engine phân tích                │
│   - ML Pipeline                     │
│   - Dịch vụ RAG                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Lớp dữ liệu                       │
│   - Database SQLite                 │
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

## 🤝 Đóng góp

Chúng tôi hoan nghênh các đóng góp! Vui lòng:

1. Fork kho lưu trữ
2. Tạo nhánh tính năng (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push tới nhánh (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

---

## 📝 Ghi chú phát triển

- **Nhật ký Backend**: Kiểm tra đầu ra Uvicorn để tìm lỗi API
- **Nhật ký Frontend**: Mở DevTools trình duyệt (F12)
- **Database**: Tệp SQLite nằm tại `data/propertyvision.db`
- **Dự phòng LLM**: Hệ thống giảm nhẹ thành công nếu Ollama không có sẵn

---

## 📄 Giấy phép

Dự án này được cấp phép theo Giấy phép MIT - xem tệp LICENSE để biết chi tiết.

---

## 👥 Tác giả

- **Trưởng dự án**: Quang Vo AI Team
- **Kho lưu trữ**: https://github.com/QuangVoAI/PropertyVision

---

## 🙋 Hỗ trợ

Đối với các vấn đề, câu hỏi hoặc đề xuất:
- Mở một [Issue](https://github.com/QuangVoAI/PropertyVision/issues)
- Kiểm tra [Tài liệu](./BASELINE.md) hiện có

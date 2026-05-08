FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY datasets ./datasets
COPY README.md ./

RUN cd frontend && npm install && npm run build

EXPOSE 7860

CMD ["bash", "-lc", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

# PropertyVision Project Diagrams

This file contains Mermaid diagrams for README, report writing, and presentation slides.

## 1. System Architecture

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Browser["Browser"]
        React["React + Vite UI"]
        Browser --> React
    end

    subgraph Backend["Application Layer"]
        FastAPI["FastAPI API Server"]
        Analytics["Analytics Service"]
        Prediction["Price Prediction"]
        Simulation["Investment Simulation"]
        Planning["GIS / Planning Risk"]
        Assistant["AI Assistant Endpoints"]
    end

    subgraph Data["Data Layer"]
        HFDataset["Hugging Face Dataset"]
        CSV["datasets/clean_dataset.csv"]
        SQLite["Runtime SQLite Tables"]
        Mart["Pandas Data Mart"]
    end

    subgraph AI["AI Layer"]
        Retriever["RAG Retriever"]
        Sources["Market / Legal / Planning Sources"]
        Qwen["Hosted Qwen2.5-1.5B-Instruct"]
    end

    React --> FastAPI
    HFDataset --> CSV
    CSV --> Mart
    Mart --> SQLite
    SQLite --> FastAPI
    Mart --> Analytics
    Mart --> Prediction
    Mart --> Simulation
    Mart --> Planning
    Analytics --> FastAPI
    Prediction --> FastAPI
    Simulation --> FastAPI
    Planning --> FastAPI
    Assistant --> Retriever
    Retriever --> Sources
    Retriever --> Qwen
    Qwen --> Assistant
    FastAPI --> React
```

## 2. First-Run Dataset Flow

```mermaid
flowchart TD
    Start["Start backend"] --> CheckLocal{"datasets/clean_dataset.csv exists?"}
    CheckLocal -- Yes --> LoadLocal["Load local processed CSV"]
    CheckLocal -- No --> Download["Download processed CSV from Hugging Face"]
    Download --> DownloadStatus{"Download successful?"}
    DownloadStatus -- Yes --> SaveLocal["Save to datasets/clean_dataset.csv"]
    SaveLocal --> LoadLocal
    DownloadStatus -- No --> RawFallback["Fallback to datasets/raw if available"]
    RawFallback --> LoadLocal
    LoadLocal --> Normalize["Rule-based normalization and validation"]
    Normalize --> Seed["Seed SQLite runtime tables"]
    Seed --> Ready["Backend APIs ready"]
```

## 3. Dashboard Analytics Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as React UI
    participant API as FastAPI
    participant Data as Data Mart

    User->>UI: Select city, district, price, ROI filters
    UI->>API: POST /api/analytics
    API->>Data: Apply filters
    Data-->>API: Filtered listings
    API->>API: Compute KPI, trend, district scores
    API-->>UI: KPI, chart series, ranked districts
    UI-->>User: Render dashboard cards and charts
```

## 4. Investment Simulation And AI Recommendation

```mermaid
sequenceDiagram
    participant User
    participant UI as Decision Lab UI
    participant API as FastAPI
    participant ML as Prediction Model
    participant RAG as RAG Retriever
    participant Qwen as Hosted Qwen

    User->>UI: Click "Chạy mô phỏng đầu tư"
    UI->>API: POST /api/recommendation/future/stream
    API-->>UI: stage: Đang khởi tạo mô phỏng
    API->>ML: Predict price and run what-if
    ML-->>API: Predicted price and scenario rows
    API-->>UI: what_if result
    API->>RAG: Retrieve market, legal, planning context
    RAG-->>API: Ranked sources
    API->>Qwen: Prompt with context and simulation result
    Qwen-->>API: Stream Vietnamese recommendation
    API-->>UI: Stream sectioned recommendation
    UI-->>User: Show financial result first, AI text after
```

## 5. RAG Assistant Flow

```mermaid
flowchart LR
    Question["User question"] --> Filter["Apply active dashboard filters"]
    Filter --> Retrieve["Retrieve relevant documents"]
    Retrieve --> Context["Build grounded context"]
    Context --> Qwen["Hosted Qwen text generation"]
    Qwen --> Stream["NDJSON streaming response"]
    Stream --> Answer["Structured answer"]
    Retrieve --> Sources["Source inspector"]
    Sources --> Answer
```

## 6. Main Feature Map

```mermaid
mindmap
  root((PropertyVision))
    Executive Overview
      Market KPI
      ROI trend
      District ranking
    Market Intelligence
      City filter
      District comparison
      Property type breakdown
    Decision Lab
      Price prediction
      What-if simulation
      Future recommendation
      AI chart caption
    GIS Planning
      District map
      Planning risk
      Opportunity score
    AI Analyst
      RAG retrieval
      Hosted Qwen
      Source inspector
    Data Operations
      Dataset status
      RAG reindex
      Refresh logs
```

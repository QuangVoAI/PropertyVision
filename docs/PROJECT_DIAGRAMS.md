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

## 6. RAG Data-to-Answer Flow

```mermaid
flowchart TB
    subgraph DataPrep["Document preparation"]
        Market["Market analytics docs"]
        Ward["Ward / micro-market docs"]
        Street["Street-level docs"]
        Legal["Legal documents table"]
        Planning["Planning zones table"]
        Market --> Docs["load_rag_documents()"]
        Ward --> Docs
        Street --> Docs
        Legal --> Docs
        Planning --> Docs
        Docs --> Index["build_rag_index()"]
    end

    subgraph Retrieval["Retrieval and ranking"]
        Query["User question"] --> Filters["Active filters + district focus"]
        Filters --> Cache["get_rag_index() cache key"]
        Cache --> Candidate["candidate_doc_indices()"]
        Candidate --> Focus["Focus by district / city / ward / street"]
        Focus --> Rank["Similarity ranking\nSentenceTransformers or TF-IDF fallback"]
        Rank --> Sources["Top-k sources with scores"]
    end

    subgraph Generation["Grounded generation"]
        Sources --> Prompt["Build assistant / decision prompt"]
        Prompt --> Qwen["Hosted Qwen"]
        Qwen --> Parse["Parse sections + clean text"]
        Parse --> Enrich["Enrich with fallback data\nif answer is too generic"]
        Enrich --> UI["Stream to React UI"]
    end

    Index --> Cache
    Query --> Retrieval
    Sources --> Prompt
    Enrich --> UI
```

Key behaviors:
- The index is rebuilt when data or planning/legal counts change.
- District filters narrow the candidate set before similarity ranking.
- Street-level questions prefer street documents; ward questions prefer micro-market documents.
- If the model response is too generic, the backend enriches it with grounded summary data before returning it.

## 7. Main Feature Map

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

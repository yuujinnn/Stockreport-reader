# Multi-Agent System Documentation
## ChatClovaX & LangGraph Based Stock Analysis Platform

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Multi-Agent Interaction Flows](#multi-agent-interaction-flows)
4. [Agent System Structure](#agent-system-structure)
5. [Data Flow Analysis](#data-flow-analysis)
6. [RAG Pipeline Detailed Architecture](#rag-pipeline-detailed-architecture)
7. [API Integration](#api-integration)
8. [Upload API System Analysis](#upload-api-system-analysis)
9. [Chunk-based Document Reference System](#chunk-based-document-reference-system)
10. [Technology Stack](#technology-stack)
11. [Extension Points](#extension-points)
12. [Testing & Quality Assurance](#testing--quality-assurance)
13. [Change Log](#change-log)
14. [Next Steps & Roadmap](#next-steps--roadmap)

---

## System Overview

This is a comprehensive multi-agent system built with **ChatClovaX (HCX-005)** and **LangGraph** for analyzing stock market data, corporate disclosures, news information, and documents. The system combines advanced PDF document processing with intelligent chunk-based citation, multi-source data analysis, and coordinated agent orchestration.

### Core Components
- **Frontend**: React 19 + TypeScript + Tailwind CSS with Interactive PDF Viewer
- **Backend**: FastAPI + LangGraph + ChatClovaX Multi-Agent System
- **Agent Architecture**: Supervisor + 3 Specialized Worker Agents
- **RAG Integration**: PDF Processing + Chunk-based Citation + Context Injection
- **Data Sources**: Kiwoom API, DART Open API, Tavily Search, Naver News, PDF Documents

### RAG Pipeline Integration
The system features advanced **RAG (Retrieval-Augmented Generation)** capabilities that enhance multi-agent analysis:

- **Intelligent PDF Processing**: Automatic extraction of text, image, and table chunks with precise bounding box coordinates
- **Interactive Chunk Citation**: Users can visually select and cite specific document sections through the PDF viewer
- **Context Injection**: Selected chunks are automatically injected into the Supervisor's system prompt as `{context}`
- **Multi-Modal Analysis**: Agents can analyze uploaded documents alongside real-time data sources
- **Chunk Metadata Storage**: `processed_states.json` maintains chunk relationships and enables precise source attribution

---

## Architecture Diagrams

### 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Frontend (React)"
        UI[Web Interface<br/>React + TypeScript]
        PDF[PDF Viewer<br/>react-pdf]
        Chat[Chat Interface<br/>ChatPane]
        State[State Management<br/>Zustand]
    end
    
    subgraph "Backend Services"
        Upload[Upload API<br/>:9000]
        Supervisor[Supervisor API<br/>:8000]
        
        subgraph "Multi-Agent System"
            SupervisorAgent[Supervisor Agent<br/>ChatClovaX HCX-005]
            StockAgent[Stock Price Agent<br/>ChatClovaX HCX-005]
            SearchAgent[Search Agent<br/>ChatClovaX HCX-005]
            DartAgent[DART Agent<br/>ChatClovaX HCX-005]
        end
        
        subgraph "RAG Pipeline Integration"
            ProcessedStates[processed_states.json<br/>📄 Chunk Metadata & BBox]
            ChunkContext[Chunk Context Provider<br/>🔗 Context Injection]
        end
    end
    
    subgraph "External APIs"
        Kiwoom[Kiwoom REST API<br/>Historical Stock Chart Data]
        Clova[CLOVA Studio API<br/>ChatClovaX Models]
        Tavily[Tavily Search API<br/>Global Web Search]
        Naver[Naver News API<br/>Korean News Search]
        DARTAPI[DART Open API<br/>Corporate Disclosure Data]
    end
    
    subgraph "Storage"
        PDFs[PDF Files<br/>uploads/]
        Processed[Processed Data<br/>processed/]
        StockData[Stock Chart Data<br/>data/]
    end
    
    UI --> Upload
    UI --> Supervisor
    PDF --> Upload
    Chat --> Supervisor
    
    Upload --> PDFs
    Upload --> Processed
    
    Supervisor --> SupervisorAgent
    SupervisorAgent --> StockAgent
    SupervisorAgent --> SearchAgent
    SupervisorAgent --> DartAgent
    
    StockAgent --> Kiwoom
    StockAgent --> StockData
    
    ProcessedStates --> ChunkContext
    ChunkContext --> SupervisorAgent
    
    SupervisorAgent --> Clova
    StockAgent --> Clova
    StockAgent --> Kiwoom
    SearchAgent --> Clova
    SearchAgent --> Tavily
    SearchAgent --> Naver
    DartAgent --> Clova  
    DartAgent --> DARTAPI
    
    style SupervisorAgent fill:#e1f5fe
    style StockAgent fill:#f3e5f5
    style SearchAgent fill:#e8f5e8
    style DartAgent fill:#fff3e0
    style ProcessedStates fill:#fce4ec
    style ChunkContext fill:#e8f5e8
    style Clova fill:#fff8e1
    style Kiwoom fill:#e3f2fd
    style Tavily fill:#f1f8e9
    style Naver fill:#fff3e0
    style DARTAPI fill:#fce4ec
```

### 2. Multi-Agent System Architecture

```mermaid
graph TB
    subgraph "LangGraph Multi-Agent System"
        subgraph "Supervisor Layer"
            Supervisor[Supervisor Agent<br/>ChatClovaX HCX-005<br/>🎯 Coordinator & Router]
        end
        
        subgraph "Worker Agents"
            StockAgent[Stock Price Agent<br/>ChatClovaX HCX-005<br/>📊 Stock Data Analysis<br/>Kiwoom REST API]
            SearchAgent[Search Agent<br/>ChatClovaX HCX-005<br/>🔍 Web Search & News Analysis<br/>Tavily + Naver News]
            DARTAgent[DART Agent<br/>ChatClovaX HCX-005<br/>📈 Corporate Filings Analysis<br/>DART API Integration]
        end
        
        subgraph "Shared Components"
            State[MessagesState<br/>📝 Shared State]
            Graph[LangGraph<br/>🔄 Workflow Engine]
        end
        
        subgraph "Tools & APIs"
            KiwoomTools[Kiwoom API Tools<br/>📡 Chart Data Retrieval]
            SearchTools[Search & News Tools<br/>🌐 Tavily Web Search + 📰 Naver News + 🔗 Content Crawling]
            DARTTools[DART API Tools<br/>📊 Corporate Filings Retrieval<br/>🔍 Report Analysis & Section Extraction]
        end
    end
    
    User[👤 User Query] --> Supervisor
    Supervisor -->|handoff| StockAgent
    Supervisor -->|handoff| SearchAgent
    Supervisor -->|handoff| DARTAgent
    
    StockAgent --> KiwoomTools
    SearchAgent --> SearchTools
    DARTAgent --> DARTTools
    
    StockAgent --> State
    SearchAgent --> State
    DARTAgent --> State
    
    State --> Graph
    Graph --> Supervisor
    
    style Supervisor fill:#e3f2fd
    style StockAgent fill:#f3e5f5
    style SearchAgent fill:#e8f5e8
    style DARTAgent fill:#fff3e0
    style State fill:#fce4ec
```

### 3. Multi-Agent Interaction Flows

#### A. Stock Price Agent Flow
```mermaid
sequenceDiagram
    participant User
    participant API as Supervisor API
    participant Supervisor as Supervisor Agent
    participant StockAgent as Stock Price Agent
    participant Kiwoom as Kiwoom API
    participant DataMgr as Data Manager
    
    User->>API: POST /query {"query": "삼성전자 Q1 주가 분석"}
    API->>Supervisor: invoke(initial_state)
    
    Note over Supervisor: ChatClovaX 분석<br/>주가 분석 요청 판단
    
    Supervisor->>Supervisor: 종목: 삼성전자(005930)<br/>기간: Q1 (20250101-20250331)<br/>목적: 기술적 분석
    
    Supervisor->>StockAgent: call_stock_price_agent(<br/>"삼성전자(005930) Q1 주가 데이터 분석")
    
    Note over StockAgent: ChatClovaX + LangGraph<br/>ReAct Pattern
    
    StockAgent->>StockAgent: Thought: 일봉 데이터 필요
    StockAgent->>Kiwoom: get_day_chart(005930, 20250101, 20250331)
    Kiwoom-->>StockAgent: Raw Chart Data
    
    StockAgent->>DataMgr: process_chart_data(raw_data, "day")
    DataMgr-->>StockAgent: Processed DataFrame + Indicators
    
    StockAgent->>StockAgent: Final Answer: 기술적 분석 보고서
    StockAgent-->>Supervisor: 상세 분석 결과
    
    Supervisor->>Supervisor: 결과 종합 & 최종 답변 작성
    Supervisor-->>API: 최종 답변
    API-->>User: QueryResponse
```

#### B. Search Agent Flow  
```mermaid
sequenceDiagram
    participant User
    participant API as Supervisor API
    participant Supervisor as Supervisor Agent
    participant SearchAgent as Search Agent
    participant Tavily as Tavily API
    participant Naver as Naver News API
    participant Crawler as Content Crawler
    
    User->>API: POST /query {"query": "올해 삼성전자 반도체 신규 수주"}
    API->>Supervisor: invoke(initial_state)
    
    Note over Supervisor: ChatClovaX 분석<br/>뉴스 검색 요청 판단
    
    Supervisor->>Supervisor: 삼성전자 반도체 최신 뉴스 필요
    
    Supervisor->>SearchAgent: call_search_agent(<br/>"삼성전자 반도체 최신 뉴스 및 수주 현황")
    
    Note over SearchAgent: ChatClovaX + LangGraph<br/>Autonomous Tool Selection
    
    SearchAgent->>SearchAgent: Thought: 한국 뉴스 최신순 검색
    SearchAgent->>Naver: search_naver_news_by_date("삼성전자 반도체 계약")
    Naver-->>SearchAgent: Latest News Articles
    
    SearchAgent->>Crawler: crawl_content(article_urls)
    Crawler-->>SearchAgent: Full Article Content
    
    SearchAgent->>SearchAgent: Thought: 글로벌 정보도 확인
    SearchAgent->>Tavily: tavily_web_search("Samsung Electronics chip deal")
    Tavily-->>SearchAgent: Global Web Results
    
    SearchAgent->>SearchAgent: Final Answer: 종합 뉴스 분석 보고서
    SearchAgent-->>Supervisor: 뉴스 동향 분석 결과
    
    Supervisor->>Supervisor: 결과 종합 & 최종 답변 작성
    Supervisor-->>API: 최종 답변
    API-->>User: QueryResponse
```

#### C. DART Agent Flow
```mermaid
sequenceDiagram
    participant User
    participant API as Supervisor API
    participant Supervisor as Supervisor Agent
    participant DartAgent as DART Agent
    participant DARTAPI as DART API
    participant XMLParser as XML Parser
    participant SectionAnalyzer as Section Analyzer
    
    User->>API: POST /query {"query": "삼성전자 최근 분기보고서 분석"}
    API->>Supervisor: invoke(initial_state)
    
    Note over Supervisor: ChatClovaX 분석<br/>공시 문서 분석 요청 판단
    
    Supervisor->>Supervisor: 삼성전자의 최근 공시자료와 25년 2분기 보고서 필요
    
    Supervisor->>DartAgent: call_dart_agent(<br/>"삼성전자 25년 2분기보고서 핵심 내용 분석")
    
    Note over DartAgent: ChatClovaX + LangGraph<br/>Autonomous DART Analysis
    
    DartAgent->>DartAgent: Thought: 분기보고서 유형 결정
    DartAgent->>DartAgent: get_dart_report_type_code("분기보고서")
    DartAgent->>DartAgent: Action: A003 (분기보고서)
    
    DartAgent->>DARTAPI: get_dart_report_list(005930, "A003")
    DARTAPI-->>DartAgent: Report List
    
    DartAgent->>DartAgent: get_rcept_no_by_date(20250101, report_list)
    DartAgent->>XMLParser: extract_report_then_title_list_from_xml(rcept_no)
    XMLParser-->>DartAgent: Document Section Titles
    
    DartAgent->>SectionAnalyzer: recommend_section_from_titles_list(titles, query)
    SectionAnalyzer-->>DartAgent: Recommended Sections
    
    DartAgent->>XMLParser: extract_report_then_section_text(sections, titles, rcept_no)
    XMLParser-->>DartAgent: Section Content
    
    DartAgent->>DartAgent: Final Answer: 분기보고서 분석 보고서
    DartAgent-->>Supervisor: 공시 분석 결과
    
    Supervisor->>Supervisor: 결과 종합 & 최종 답변 작성
    Supervisor-->>API: 최종 답변
    API-->>User: QueryResponse
```

---

## Agent System Structure

### 4. Supervisor Agent Internal Architecture

```mermaid
flowchart TD
    subgraph "Supervisor Agent (ChatClovaX HCX-005)"
        Prompt["System Prompt<br/>📋 Date-aware Instructions + Pinned Chunk(context)"]
        LLM[ChatClovaX HCX-005<br/>🧠 Core Intelligence]
        Tools[Handoff Tools<br/>🔧 Worker Agent Connectors]
        
        subgraph "Tool Registry"
            StockTool[call_stock_price_agent<br/>📊 Stock Analysis Tool]
            SearchTool[call_search_agent<br/>🔍 Search & News Analysis Tool]
            DARTTool[call_dart_agent<br/>📈 Corporate Filings Analysis Tool]
        end
        
        subgraph "Manual Supervisor Implementation"
            ReactAgent[create_react_agent<br/>🔄 LangGraph ReAct Pattern]
            Workflow[StateGraph Workflow<br/>START → supervisor → END]
        end
    end
    
    UserQuery[User Query] --> Prompt
    Prompt --> LLM
    LLM --> Tools
    Tools --> StockTool
    Tools --> SearchTool
    Tools --> DARTTool
    
    ReactAgent --> LLM
    ReactAgent --> Tools
    Workflow --> ReactAgent
    
    style LLM fill:#e1f5fe
    style StockTool fill:#f3e5f5
    style SearchTool fill:#e8f5e8
    style DARTTool fill:#fff3e0
```

### 5. Stock Price Agent Internal Architecture

```mermaid
flowchart TD
    subgraph "Stock Price Agent (ChatClovaX HCX-005)"
        StockLLM[ChatClovaX HCX-005<br/>🧠 Stock Analysis Intelligence]
        StockPrompt[Stock Analysis Prompt<br/>📋 Date-formatted Instructions]
        
        subgraph "LangChain Tools"
            MinuteTool[get_minute_chart<br/>⏱️ 1-60분 데이터]
            DayTool[get_day_chart<br/>📅 일봉 데이터]
            WeekTool[get_week_chart<br/>📆 주봉 데이터]
            MonthTool[get_month_chart<br/>🗓️ 월봉 데이터]
            YearTool[get_year_chart<br/>📊 년봉 데이터]
        end
        
        subgraph "React Agent System"
            ReactEngine[create_react_agent<br/>🔄 Tool-calling Engine]
            ThoughtAction[Thought → Action → Observation<br/>🤔 ReAct Loop]
        end
        
        subgraph "Data Processing Layer"
            KiwoomAPI[Kiwoom API Client<br/>📡 Chart Data Access]
            DataManager[Data Manager<br/>📊 Processing & Indicators]
            TechIndicators[Technical Indicators<br/>📈 SMA, EMA, MACD, RSI, etc.]
        end
    end
    
    StockLLM --> StockPrompt
    StockLLM --> ReactEngine
    ReactEngine --> ThoughtAction
    ThoughtAction --> MinuteTool
    ThoughtAction --> DayTool
    ThoughtAction --> WeekTool
    ThoughtAction --> MonthTool
    ThoughtAction --> YearTool
    
    MinuteTool --> KiwoomAPI
    DayTool --> KiwoomAPI
    WeekTool --> KiwoomAPI
    MonthTool --> KiwoomAPI
    YearTool --> KiwoomAPI
    
    KiwoomAPI --> DataManager
    DataManager --> TechIndicators
    
    style StockLLM fill:#f3e5f5
    style ReactEngine fill:#e8f5e8
    style KiwoomAPI fill:#fff3e0
    style DataManager fill:#fce4ec
```

### 6. Search Agent Internal Architecture

```mermaid
flowchart TD
    subgraph "Search Agent (ChatClovaX HCX-005)"
        SearchLLM[ChatClovaX HCX-005<br/>🧠 Search Analysis Intelligence]
        SearchPrompt[Search Agent Prompt<br/>📋 Autonomous search reasoning instructions]
        
        subgraph "LangChain Tools"
            TavilyTool[tavily_web_search<br/>🌐 Global Web Search]
            NaverRelevanceTool[search_naver_news_by_relevance<br/>📰 Korean News Relevance]
            NaverDateTool[search_naver_news_by_date<br/>📅 Korean News Latest]
        end
        
        subgraph "React Agent System"
            SearchReactEngine[create_react_agent<br/>🔄 Tool-calling Engine]
            SearchThoughtAction[Thought → Action → Observation<br/>🤔 ReAct Loop]
        end
        
        subgraph "Data Processing Layer"
            TavilyAPI[Tavily API Client<br/>🌐 Global Web Search Access]
            NaverAPI[Naver News API Client<br/>📰 Korean News Access]
            ContentCrawler[Content Crawler<br/>🔗 Deep Article Analysis]
        end
    end
    
    SearchLLM --> SearchPrompt
    SearchLLM --> SearchReactEngine
    SearchReactEngine --> SearchThoughtAction
    SearchThoughtAction --> TavilyTool
    SearchThoughtAction --> NaverRelevanceTool
    SearchThoughtAction --> NaverDateTool
    
    TavilyTool --> TavilyAPI
    NaverRelevanceTool --> NaverAPI
    NaverDateTool --> NaverAPI
    
    TavilyAPI --> ContentCrawler
    NaverAPI --> ContentCrawler
    
    style SearchLLM fill:#e8f5e8
    style SearchReactEngine fill:#f3e5f5
    style TavilyAPI fill:#e1f5fe
    style NaverAPI fill:#fff3e0
    style ContentCrawler fill:#fce4ec
```

### 7. DART Agent Internal Architecture

```mermaid
flowchart TD
    subgraph "DART Agent (ChatClovaX HCX-005)"
        DARTLLm[ChatClovaX HCX-005<br/>🧠 DART Analysis Intelligence]
        DARTPrompt[DART Analysis Prompt<br/>📋 Autonomous DART reasoning instructions]
        
        subgraph "LangChain Tools"
            ReportTypeTool[get_dart_report_type_code<br/>📋 Report Type Classification]
            ReportListTool[get_dart_report_list<br/>📄 Report List Retrieval]
            RceptNoTool[get_rcept_no_by_date<br/>📅 Receipt Number by Date]
            TitleListTool[extract_report_then_title_list_from_xml<br/>📑 Document Structure Analysis]
            SectionRecommendTool[recommend_section_from_titles_list<br/>🎯 Section Recommendation]
            SectionTextTool[extract_report_then_section_text<br/>📝 Section Content Extraction]
        end
        
        subgraph "React Agent System"
            DARTReactEngine[create_react_agent<br/>🔄 Tool-calling Engine]
            DARTThoughtAction[Thought → Action → Observation<br/>🤔 ReAct Loop]
        end
        
        subgraph "Data Processing Layer"
            DARTAPI[DART API Client<br/>📡 Electronic Disclosure Access]
            ReportParser[Report Parser<br/>📊 XML Processing & Section Extraction]
            ContentAnalyzer[Content Analyzer<br/>📈 Financial Data Analysis]
        end
    end
    
    DARTLLm --> DARTPrompt
    DARTLLm --> DARTReactEngine
    DARTReactEngine --> DARTThoughtAction
    DARTThoughtAction --> ReportTypeTool
    DARTThoughtAction --> ReportListTool
    DARTThoughtAction --> RceptNoTool
    DARTThoughtAction --> TitleListTool
    DARTThoughtAction --> SectionRecommendTool
    DARTThoughtAction --> SectionTextTool
    
    ReportTypeTool --> DARTAPI
    ReportListTool --> DARTAPI
    RceptNoTool --> DARTAPI
    TitleListTool --> DARTAPI
    SectionRecommendTool --> ReportParser
    SectionTextTool --> ReportParser
    
    DARTAPI --> ReportParser
    ReportParser --> ContentAnalyzer
    
    style DARTLLm fill:#fff3e0
    style DARTReactEngine fill:#e8f5e8
    style DARTAPI fill:#e1f5fe
    style ReportParser fill:#fce4ec
```

---

## Data Flow Analysis

### 8. Complete Data Flow Pipeline

```mermaid
flowchart LR
    subgraph "Input Layer"
        UserQuery[👤 User Query<br/>삼성전자 Q1 분석]
        PDFUpload[📄 PDF Upload<br/>Research Reports]
        ChunkSelection[📌 Chunk Selection<br/>Interactive Citation]
    end
    
    subgraph "RAG Pipeline Processing"
        subgraph "PDF Analysis (LangGraph)"
            PDFSplit[📄 PDF Split<br/>Batch Processing]
            LayoutAnalysis[🔍 Layout Analysis<br/>Upstage API]
            ElementExtract[🎯 Element Extraction<br/>Text/Image/Table]
            ContentCrop[✂️ Content Cropping<br/>Image & Table Isolation]
            Summarization[📝 Multi-Modal Summarization<br/>OpenAI API]
        end
        
        subgraph "Vector Storage"
            VectorStore[🗃️ ChromaDB Storage<br/>Semantic Embeddings]
            ProcessedStates[📋 processed_states.json<br/>Chunk Metadata + BBox]
            ChunkProvider[🔗 Chunk Context Provider<br/>Selected Content Injection]
        end
    end
    
    subgraph "Multi-Agent Processing"
        subgraph "Supervisor Processing"
            Parse[🔍 Query Parsing<br/>Extract: 종목, 기간, 목적]
            Route[🎯 Agent Routing<br/>Determine: Stock/Search/DART]
            ContextInject["💉 Context Injection<br/>Pinned Chunks → {context}"]
            Coordinate[🤝 Result Coordination<br/>Integrate Multi-Source Responses]
        end
        
        subgraph "Specialized Agents"
            StockAnalyze[📊 Stock Analysis<br/>Kiwoom API + Technical Indicators]
            SearchAnalyze[🔍 Search Analysis<br/>Tavily + Naver News + Crawling]
            DartAnalyze[📈 DART Analysis<br/>Corporate Disclosure + XML Parsing]
        end
        
        subgraph "Data Integration"
            Fetch[📡 Multi-Source Data Fetching<br/>Parallel API Calls]
            Process[⚙️ Cross-Agent Synthesis<br/>Information Fusion]
            Report[📋 Integrated Report<br/>Multi-Domain Analysis + Citations]
        end
    end
    
    subgraph "Output Layer"
        Response[📝 Final Response<br/>Contextualized Analysis]
        PDF_UI[🖥️ Interactive PDF Viewer<br/>Chunk Overlays + Selection]
        Chat_UI[💬 Chat Interface<br/>Streaming + Source Attribution]
    end
    
    %% PDF Processing Flow
    PDFUpload --> PDFSplit
    PDFSplit --> LayoutAnalysis
    LayoutAnalysis --> ElementExtract
    ElementExtract --> ContentCrop
    ContentCrop --> Summarization
    Summarization --> VectorStore
    Summarization --> ProcessedStates
    
    %% Chunk Citation Flow
    ProcessedStates --> PDF_UI
    PDF_UI --> ChunkSelection
    ChunkSelection --> ChunkProvider
    
    %% Query Processing Flow
    UserQuery --> Parse
    Parse --> Route
    ChunkProvider --> ContextInject
    ContextInject --> Route
    
    Route --> StockAnalyze
    Route --> SearchAnalyze
    Route --> DartAnalyze
    
    StockAnalyze --> Fetch
    SearchAnalyze --> Fetch
    DartAnalyze --> Fetch
    
    Fetch --> Process
    Process --> Report
    Report --> Coordinate
    Coordinate --> Response
    Response --> Chat_UI
    
    %% Cross-references
    VectorStore -.-> Process
    ProcessedStates -.-> Coordinate
    
    style Parse fill:#e3f2fd
    style Route fill:#e3f2fd
    style ContextInject fill:#e1f5fe
    style StockAnalyze fill:#f3e5f5
    style SearchAnalyze fill:#e8f5e8
    style DartAnalyze fill:#fff3e0
    style Process fill:#fce4ec
    style LayoutAnalysis fill:#fff8e1
    style Summarization fill:#f0f8ff
    style VectorStore fill:#f5f5dc
    style ProcessedStates fill:#ffefd5
    style ChunkProvider fill:#e6ffe6
```

### 9. RAG Pipeline Detailed Architecture

```mermaid
flowchart TD
    subgraph "RAG Processing Pipeline (LangGraph)"
        subgraph "Input Processing"
            PDFInput[PDF Document<br/>📄 Source File]
            InitState[Initial State<br/>🗂️ GraphState Init]
        end
        
        subgraph "Document Analysis"
            SplitNode[Split PDF Node<br/>📑 Batch Processing]
            LayoutNode[Layout Analyzer Node<br/>🔍 Upstage API]
            ExtractNode[Extract Page Elements Node<br/>🎯 Content Identification]
        end
        
        subgraph "Content Processing"
            ImageCrop[Image Cropper Node<br/>🖼️ Visual Content Isolation]
            TableCrop[Table Cropper Node<br/>📊 Structured Data Extraction]
            TextExtract[Extract Page Text Node<br/>📝 Textual Content]
        end
        
        subgraph "AI Summarization"
            PageSummary[Page Summary Node<br/>📋 OpenAI GPT-4]
            ImageSummary[Image Summary Node<br/>🖼️ Vision Analysis]
            TableSummary[Table Summary Node<br/>📊 Structured Analysis]
            TableMarkdown[Table Markdown Node<br/>📐 Format Conversion]
        end
        
        subgraph "Storage & Indexing"
            ProcessedState[processed_states.json<br/>📋 Metadata + BBox Coordinates]
            ChromaDB[ChromaDB Vector Store<br/>🗃️ Semantic Embeddings]
            EmbeddingGen[Embedding Generation<br/>🔢 CLOVA Embeddings]
        end
    end
    
    PDFInput --> InitState
    InitState --> SplitNode
    SplitNode --> LayoutNode
    LayoutNode --> ExtractNode
    
    ExtractNode --> ImageCrop
    ExtractNode --> TableCrop
    ExtractNode --> TextExtract
    
    ImageCrop --> PageSummary
    TableCrop --> PageSummary
    TextExtract --> PageSummary
    
    PageSummary --> ImageSummary
    PageSummary --> TableSummary
    
    ImageSummary --> ProcessedState
    TableSummary --> TableMarkdown
    TableMarkdown --> ProcessedState
    
    ProcessedState --> EmbeddingGen
    EmbeddingGen --> ChromaDB
    
    style PDFInput fill:#e8f5e8
    style LayoutNode fill:#fff8e1
    style ExtractNode fill:#e3f2fd
    style PageSummary fill:#f0f8ff
    style ProcessedState fill:#ffefd5
    style ChromaDB fill:#f5f5dc
```

#### RAG Pipeline Key Features

##### **1. Advanced Document Processing**
- **PDF Splitting**: Batch processing for large documents (configurable batch size)
- **Layout Analysis**: Upstage API for precise element detection and positioning
- **Multi-Modal Extraction**: Simultaneous text, image, and table content identification
- **Bounding Box Precision**: Exact coordinate mapping for interactive citation

##### **2. AI-Powered Content Analysis**
- **Page Summarization**: OpenAI GPT-4 for contextual page summaries
- **Image Analysis**: Vision-based understanding of charts, diagrams, and visual content
- **Table Processing**: Structured data extraction with Markdown formatting
- **Korean Language Optimization**: Specialized processing for Korean financial documents

##### **3. Intelligent Storage System**
- **Dual Storage Strategy**: 
  - `processed_states.json`: Metadata, coordinates, and chunk relationships
  - `ChromaDB`: Vector embeddings for semantic search
- **CLOVA Embeddings**: Korean-optimized embedding generation
- **Chunk-Level Granularity**: Individual element tracking for precise citation

##### **4. Interactive Citation System**
- **Visual Overlay**: Real-time chunk visualization on PDF viewer
- **Multi-Type Support**: Text, image, and table chunks with type-specific styling
- **Context Injection**: Selected chunks automatically injected into agent prompts
- **Source Attribution**: Complete traceability from analysis back to source content

### 10. State Management Flow

```mermaid
stateDiagram-v2
    [*] --> UserInput
    
    state "User Input Processing" as UserInput {
        [*] --> QueryReceived
        QueryReceived --> StateCreation
        StateCreation --> InitialState
    }
    
    state "Supervisor Processing" as SupervisorProc {
        [*] --> QuestionAnalysis
        QuestionAnalysis --> AgentSelection
        AgentSelection --> ToolCalling
        ToolCalling --> ResultIntegration
    }
    
    state "Stock Agent Processing" as StockProc {
        [*] --> ChartSelection
        ChartSelection --> APICall
        APICall --> DataProcessing
        DataProcessing --> TechnicalAnalysis
        TechnicalAnalysis --> ReportGeneration
    }
    
    state "Final State" as FinalState {
        [*] --> ResponseExtraction
        ResponseExtraction --> UserResponse
    }
    
    UserInput --> SupervisorProc
    SupervisorProc --> StockProc : handoff_tool
    StockProc --> SupervisorProc : analysis_result
    SupervisorProc --> FinalState
    FinalState --> [*]
    
    note right of SupervisorProc
        MessagesState maintains:
        - messages: List[BaseMessage]
        - user_query: str
        - extracted_info: Dict
        - stock_data: Dict
        - metadata: Dict
    end note
```

---

## API Integration

### 11. API Architecture & Endpoints

```mermaid
graph TB
    subgraph "Frontend (Port 5173)"
        ReactApp[React Application]
        PDFViewer[PDF Viewer Component]
        ChatComponent[Chat Component]
    end
    
    subgraph "Backend APIs"
        subgraph "Upload Service (Port 9000)"
            UploadAPI[Upload API<br/>FastAPI]
            UploadEndpoints["Endpoints:<br/>POST /upload<br/>GET /chunks/{fileId}<br/>GET /file/{fileId}/download"]
        end
        
        subgraph "Query Service (Port 8000)"
            SupervisorAPI[Supervisor API<br/>FastAPI]
            QueryEndpoints["Endpoints:<br/>POST /query<br/>GET /health<br/>GET /status"]
        end
    end
    
    subgraph "External Services"
        KiwoomAPI[Kiwoom REST API<br/>Chart Data]
        ClovaAPI[CLOVA Studio API<br/>ChatClovaX Models]
        LangSmith[LangSmith<br/>Observability]
    end
    
    ReactApp -->|PDF Upload| UploadAPI
    PDFViewer -->|Get Chunks| UploadAPI
    ChatComponent -->|Query| SupervisorAPI
    
    UploadAPI --> UploadEndpoints
    SupervisorAPI --> QueryEndpoints
    
    SupervisorAPI --> ClovaAPI
    SupervisorAPI --> KiwoomAPI
    SupervisorAPI --> LangSmith
    
    style UploadAPI fill:#e8f5e8
    style SupervisorAPI fill:#e3f2fd
    style KiwoomAPI fill:#fff3e0
    style ClovaAPI fill:#fce4ec
```

### 12. Multi-Agent Request/Response Flow

```mermaid
sequenceDiagram
    participant User as 사용자
    participant FE as Frontend
    participant Upload as Upload API<br/>:9000
    participant Query as Query API<br/>:8000
    participant Supervisor as Supervisor Agent
    participant StockAgent as Stock Price Agent
    participant SearchAgent as Search Agent  
    participant DartAgent as DART Agent
    participant ProcessedStates as processed_states.json
    participant Kiwoom as Kiwoom API
    participant Tavily as Tavily API
    participant Naver as Naver News API
    participant DARTAPI as DART API
    participant Clova as CLOVA Studio
    
    Note over User,Clova: PDF Upload & Chunk Citation Flow
    User->>FE: Upload PDF document
    FE->>Upload: POST /upload (PDF file)
    Upload->>Upload: RAG processing & chunk extraction
    Upload->>ProcessedStates: Save chunk metadata & bounding boxes
    Upload-->>FE: {fileId, pageCount}
    
    FE->>Upload: GET /chunks/{fileId} (polling)
    Upload->>ProcessedStates: Load chunk data
    Upload-->>FE: ChunkInfo[] with bbox coordinates
    FE->>FE: Render interactive PDF overlays
    
    User->>FE: Select chunks & cite pages
    FE->>FE: Pin selected chunks
    
    Note over User,Clova: Multi-Agent Query Processing Flow
    User->>FE: "삼성전자에 대해 최근 분기보고서 분석, 뉴스 동향, 주가 흐름을 종합해서 분석해줘"
    FE->>Query: POST /query + pinned chunks context
    
    Query->>ProcessedStates: Load pinned chunks text content
    Query->>Supervisor: invoke() with {context} = chunk_texts
    
    Note over Supervisor: ChatClovaX 분석<br/>복합 질의 → 다중 에이전트 필요
    
    Supervisor->>Supervisor: 라우팅 결정:<br/>1) DART: 분기보고서<br/>2) Search: 뉴스 동향<br/>3) Stock: 주가 분석
    
    par DART Agent Processing
        Supervisor->>DartAgent: call_dart_agent("삼성전자 분기보고서")
        DartAgent->>DARTAPI: 보고서 검색 & 분석
        DARTAPI-->>DartAgent: 공시 문서 내용
        DartAgent->>Clova: 재무 분석 & 요약
        Clova-->>DartAgent: 재무 분석 결과
        DartAgent-->>Supervisor: 공시 분석 완료
    and Search Agent Processing  
        Supervisor->>SearchAgent: call_search_agent("삼성전자 뉴스")
        SearchAgent->>Naver: 한국 뉴스 검색
        Naver-->>SearchAgent: 뉴스 기사들
        SearchAgent->>Tavily: 글로벌 웹 검색
        Tavily-->>SearchAgent: 글로벌 정보
        SearchAgent->>Clova: 뉴스 동향 분석
        Clova-->>SearchAgent: 뉴스 분석 결과
        SearchAgent-->>Supervisor: 뉴스 분석 완료
    and Stock Agent Processing
        Supervisor->>StockAgent: call_stock_price_agent("삼성전자 주가")
        StockAgent->>Kiwoom: 주가 데이터 조회
        Kiwoom-->>StockAgent: 차트 데이터
        StockAgent->>Clova: 기술적 분석
        Clova-->>StockAgent: 주가 분석 결과
        StockAgent-->>Supervisor: 주가 분석 완료
    end
    
    Note over Supervisor: 모든 에이전트 결과 통합<br/>+ 인용된 PDF 컨텍스트 반영
    
    Supervisor->>Clova: 종합 분석 & 보고서 작성
    Clova-->>Supervisor: 최종 통합 보고서
    
    Supervisor-->>Query: 종합 분석 결과
    Query-->>FE: Streaming response with sources
    FE-->>User: 통합 분석 보고서 + 출처 표시
```

---

## Upload API System Analysis

### 13. Upload API Service Architecture

The Upload API (`backend/upload_api.py`) serves as a critical integration point between frontend PDF handling and backend RAG processing, operating on port 9000.

```mermaid
graph TB
    subgraph "Upload API Service (Port 9000)"
        UploadAPI[Upload API<br/>FastAPI Application]
        
        subgraph "Core Endpoints"
            Upload["POST /upload<br/>PDF Upload & Validation"]
            Status["GET /status/{file_id}<br/>Processing Status"]
            Download["GET /file/{file_id}/download<br/>PDF Streaming"]
            Summaries["GET /summaries/{file_id}<br/>RAG Results"]
            Health["GET /health<br/>System Health Check"]
        end
        
        subgraph "Background Processing"
            BGTask["Background Tasks<br/>process_pdf_with_rag()"]
            RAGCall["RAG Script Executor<br/>subprocess calls"]
        end
        
        subgraph "Data Management"
            Metadata[File Metadata<br/>JSON storage]
            FileStorage[PDF Storage<br/>rag/data/pdf/]
        end
    end
    
    subgraph "RAG Integration"
        RAGScript[process_pdfs.py<br/>RAG Pipeline Script]
        RAGResults[RAG Results<br/>JSON output files]
        VectorDB[Vector Database<br/>ChromaDB storage]
    end
    
    subgraph "Frontend Integration"
        PDFDropzone[PdfDropzone Component<br/>File Upload UI]
        PDFViewer[PdfViewer Component<br/>Document Display]
        StatusPolling[Status Polling<br/>Processing Updates]
    end
    
    PDFDropzone -->|POST /upload| Upload
    PDFViewer -->|GET /file/download| Download
    StatusPolling -->|GET /status| Status
    
    Upload --> BGTask
    BGTask --> RAGCall
    RAGCall --> RAGScript
    RAGScript --> RAGResults
    RAGScript --> VectorDB
    
    Upload --> Metadata
    Upload --> FileStorage
    Status --> RAGResults
    
    style UploadAPI fill:#e8f5e8
    style BGTask fill:#fff3e0
    style RAGScript fill:#e1f5fe
    style PDFDropzone fill:#f3e5f5
```

### Key Features:
- **FastAPI-based Service**: Robust web framework with automatic OpenAPI documentation
- **RAG Pipeline Integration**: Automatic background processing with `rag/scripts/process_pdfs.py`
- **File Management**: UUID-based file identification with metadata persistence
- **Background Processing**: Non-blocking uploads with 10-minute processing timeout
- **Status Monitoring**: Real-time processing status with completion detection
- **CORS Support**: Full frontend integration with streaming file downloads
- **✅ Chunk-based Document Analysis**: Bounding box extraction from `processed_states.json`
- **✅ Multi-type Chunk Support**: Text, image, and table chunks with type-specific styling
- **✅ Interactive PDF Overlays**: Visual chunk selection with normalized coordinates
- **✅ Page-level Citation**: Bulk selection of all chunks on a page

### File Processing Flow:
1. **Upload**: PDF validation, unique ID generation, file storage to `backend/rag/data/pdf/`
2. **Metadata**: JSON metadata storage with page count and timestamps
3. **Background Task**: Queued RAG processing via subprocess execution
4. **RAG Processing**: Creation of `processed_states.json` with chunk data and bounding boxes
5. **Status Tracking**: Monitoring through JSON result file detection
6. **✅ Chunk Extraction**: Parse chunks from `processed_states.json` with coordinate normalization
7. **✅ Frontend Display**: Interactive PDF overlays with type-specific chunk visualization
8. **Result Access**: Structured summaries (text/image/table) via API endpoints

### Integration Points:
- **Directory Structure**: Unified with RAG system (`backend/rag/data/pdf/`)
- **Environment Variables**: Shared secrets from `backend/secrets/.env`
- **Multi-Agent Connection**: Processed documents available for agent consumption
- **Vector Database**: ChromaDB integration through RAG pipeline
- **✅ Chunk Data Source**: `backend/rag/data/vectordb/processed_states.json`
- **✅ Frontend Integration**: Real-time chunk polling via `/chunks/{file_id}` endpoint
- **✅ Interactive UI**: PDF viewer with visual chunk selection and page-level citation
- **✅ Query Integration**: Selected chunks passed to chat API for contextual responses

---

## Chunk-based Document Reference System

### Interactive PDF Analysis Flow

```mermaid
sequenceDiagram
    participant User as 사용자
    participant PDF as PDF Viewer
    participant API as Upload API
    participant RAG as RAG System
    participant FS as File System
    participant Chat as Chat System
    
    Note over User,Chat: Document Upload & Processing
    User->>"API: POST /upload (PDF)"
    API->>RAG: Background processing
    RAG->>FS: Create processed_states.json
    
    Note over User,Chat: Chunk Visualization
    PDF->>"API: GET /chunks/{fileId} (every 5s)"
    API->>FS: Load processed_states.json
    API->>API: Parse & normalize coordinates
    API-->>PDF: ChunkInfo[] (text/image/table)
    PDF->>PDF: Render interactive overlays
    
    Note over User,Chat: Interactive Selection
    User->>PDF: Click chunk overlay
    PDF->>PDF: Toggle chunk selection
    User->>PDF: Click "페이지 전체 인용"
    PDF->>PDF: Select all page chunks
    
    Note over User,Chat: Query with Context
    User->>Chat: Enter question
    Chat->>API: query + pinChunks[]
    API->>Chat: Context-aware response
```

### Chunk Type Visualization

```mermaid
graph LR
    subgraph "PDF Page"
        TextChunk[📝 Text Chunk<br/>Blue Border<br/>Green when pinned]
        ImageChunk[🖼️ Image Chunk<br/>Purple Border<br/>Purple when pinned]
        TableChunk[📊 Table Chunk<br/>Orange Border<br/>Orange when pinned]
    end
    
    subgraph "Pinned Chips"
        TextChip[📝 텍스트 청크<br/>Green chip]
        ImageChip[🖼️ 이미지 청크<br/>Purple chip]
        TableChip[📊 테이블 청크<br/>Orange chip]
    end
    
    TextChunk -->|User clicks| TextChip
    ImageChunk -->|User clicks| ImageChip
    TableChunk -->|User clicks| TableChip
    
    style TextChunk fill:#dbeafe
    style ImageChunk fill:#ede9fe
    style TableChunk fill:#fed7aa
    style TextChip fill:#dcfce7
    style ImageChip fill:#f3e8ff
    style TableChip fill:#ffedd5
```

---

## Technology Stack

### 14. Technology Stack Overview

```mermaid
graph TB
    subgraph "Frontend Stack"
        React[React 19<br/>🔄 Component Framework]
        TS[TypeScript<br/>🔒 Type Safety]
        Tailwind[Tailwind CSS<br/>🎨 Styling]
        Vite[Vite<br/>⚡ Build Tool]
        Zustand[Zustand<br/>🗃️ State Management]
        ReactPDF[react-pdf<br/>📄 PDF Rendering]
        Vitest[Vitest<br/>🧪 Testing Framework]
    end
    
    subgraph "Backend Stack"
        FastAPI[FastAPI<br/>🚀 Web Framework]
        LangGraph[LangGraph<br/>🕸️ Agent Orchestration]
        LangChain[LangChain<br/>🔗 LLM Integration]
        ChatClovaX[ChatClovaX<br/>🧠 AI Model HCX-005]
        Pydantic[Pydantic<br/>📝 Data Validation]
        Uvicorn[Uvicorn<br/>🏃 ASGI Server]
    end
    
    subgraph "Data Processing"
        Pandas[pandas<br/>📊 Data Analysis]
        PandasTA[pandas-ta<br/>📈 Technical Analysis]
        PyPDF2[PyPDF2<br/>📄 Basic PDF Processing]
        Requests[requests<br/>🌐 HTTP Client]
    end
    
    subgraph "RAG & Vector Processing"
        ChromaDB[ChromaDB<br/>🗃️ Vector Database]
        UpstageAPI[Upstage Layout API<br/>🔍 Document Analysis]
        ClovaEmbeddings[CLOVA Embeddings<br/>🔢 Korean Optimization]
        BeautifulSoup[BeautifulSoup<br/>🕸️ Content Crawling]
        OpenAIVision[OpenAI GPT-4 Vision<br/>🖼️ Multi-Modal Analysis]
    end
    
    subgraph "External APIs"
        KiwoomAPI[Kiwoom REST API<br/>📡 Stock Chart Data]
        ClovaStudio[CLOVA Studio API<br/>🤖 AI Services]
        LangSmithAPI[LangSmith API<br/>📊 Observability]
    end
    
    React --> FastAPI
    LangGraph --> ChatClovaX
    FastAPI --> LangChain
    LangChain --> ClovaStudio
    FastAPI --> KiwoomAPI
    FastAPI --> ChromaDB
    LangGraph --> LangSmithAPI
    LangGraph --> UpstageAPI
    ChromaDB --> ClovaEmbeddings
    UpstageAPI --> OpenAIVision
    
    style React fill:#61dafb,color:#000
    style FastAPI fill:#009688,color:#fff
    style LangGraph fill:#ff6b6b,color:#fff
    style ChatClovaX fill:#4caf50,color:#fff
    style ChromaDB fill:#f5f5dc,color:#000
    style UpstageAPI fill:#fff8e1,color:#000
    style ClovaEmbeddings fill:#e6ffe6,color:#000
    style OpenAIVision fill:#f0f8ff,color:#000
```

---

## Extension Points

### 15. Implemented Search Agent Architecture

```mermaid
graph TB
    subgraph "Active System"
        CurrentSupervisor[Supervisor Agent<br/>✅ Active]
        CurrentStock[Stock Price Agent<br/>✅ Active]
        CurrentSearch[Search Agent<br/>✅ Active]
    end
    
    subgraph "Search Agent Capabilities"
        SearchTools[Search & News Tools<br/>🌐 Comprehensive Search Suite]
        SearchPrompt[Search Agent Prompt<br/>📋 Autonomous reasoning instructions]
        
        subgraph "Search Agent Tools"
            TavilyTool[tavily_web_search<br/>🌐 Global Web Search]
            NaverRelevance[search_naver_news_by_relevance<br/>📰 Korean News Relevance]
            NaverDate[search_naver_news_by_date<br/>📅 Korean News Latest]
            ContentCrawl[Content Crawling<br/>🔗 Deep article analysis]
        end
    end
    
    subgraph "Integration Points"
        SupervisorTools[Supervisor Handoff Tools<br/>🔧 call_search_agent]
        SharedState[MessagesState<br/>📝 Shared between agents]
        CommonGraph[LangGraph Workflow<br/>🔄 Agent orchestration]
    end
    
    CurrentSupervisor --> SupervisorTools
    SupervisorTools --> CurrentSearch
    CurrentSearch --> SearchTools
    CurrentSearch --> SearchPrompt
    CurrentSearch --> TavilyTool
    CurrentSearch --> NaverRelevance
    CurrentSearch --> NaverDate
    CurrentSearch --> ContentCrawl
    
    CurrentStock --> SharedState
    CurrentSearch --> SharedState
    SharedState --> CommonGraph
    
    style CurrentSearch fill:#e8f5e8
    style SearchTools fill:#e8f5e8
    style SupervisorTools fill:#fff3e0
```

### 16. Implemented DART Agent Architecture

```mermaid
graph TB
    subgraph "Active System"
        CurrentSupervisor[Supervisor Agent<br/>✅ Active]
        CurrentStock[Stock Price Agent<br/>✅ Active]
        CurrentSearch[Search Agent<br/>✅ Active]
        CurrentDART[DART Agent<br/>✅ Active]
    end
    
    subgraph "DART Agent Capabilities"
        DARTTools[DART API Tools<br/>📊 Corporate Disclosure Analysis Suite]
        DARTPrompt[DART Agent Prompt<br/>📋 Autonomous reasoning instructions]
        
        subgraph "DART Agent Tools"
            TypeCodeTool[get_dart_report_type_code<br/>📋 Report classification]
            ReportListTool[get_dart_report_list<br/>📄 Corporate report lists]
            DateTool[get_rcept_no_by_date<br/>📅 Date-based report search]
            XMLTool[extract_report_then_title_list_from_xml<br/>📑 Document structure]
            SectionTool[recommend_section_from_titles_list<br/>🎯 Smart section selection]
            ContentTool[extract_report_then_section_text<br/>📝 Content extraction]
        end
    end
    
    subgraph "Integration Points"
        SupervisorTools[Supervisor Handoff Tools<br/>🔧 call_dart_agent]
        SharedState[MessagesState<br/>📝 Shared between agents]
        CommonGraph[LangGraph Workflow<br/>🔄 Agent orchestration]
        RetryLogic[Retry Logic<br/>🔄 Exponential backoff]
    end
    
    CurrentSupervisor --> SupervisorTools
    SupervisorTools --> CurrentDART
    SupervisorTools --> RetryLogic
    CurrentDART --> DARTTools
    CurrentDART --> DARTPrompt
    CurrentDART --> TypeCodeTool
    CurrentDART --> ReportListTool
    CurrentDART --> DateTool
    CurrentDART --> XMLTool
    CurrentDART --> SectionTool
    CurrentDART --> ContentTool
    
    CurrentStock --> SharedState
    CurrentSearch --> SharedState
    CurrentDART --> SharedState
    SharedState --> CommonGraph
    
    style CurrentDART fill:#fff3e0
    style DARTTools fill:#fff3e0
    style SupervisorTools fill:#e1f5fe
```

### 17. Future Multi-Agent Expansion

```mermaid
graph TB
    subgraph "Core Supervisor"
        Supervisor[Supervisor Agent<br/>🎯 Master Coordinator]
    end
    
    subgraph "Current Agents"
        StockAgent[Stock Price Agent<br/>📊 ✅ Active]
        SearchAgent[Search Agent<br/>🔍 ✅ Active]
        DARTAgent[DART Agent<br/>📈 ✅ Active]
    end
    
    subgraph "Planned Agents"
        FutureAgent1[Custom Analysis Agent<br/>🔮 Future Extension]
        FutureAgent2[Risk Assessment Agent<br/>🔮 Future Extension]
    end
    
    subgraph "Extension Pattern"
        HandoffTools[Handoff Tools Pattern<br/>🔧 call_agent_name]
        ToolRegistry[Tool Registry<br/>📋 Dynamic tool addition]
        StateManagement[Shared State Management<br/>📝 MessagesState extension]
    end
    
    Supervisor --> StockAgent
    Supervisor --> SearchAgent
    Supervisor --> DARTAgent
    Supervisor -.-> FutureAgent1
    Supervisor -.-> FutureAgent2
    
    HandoffTools --> Supervisor
    ToolRegistry --> HandoffTools
    StateManagement --> HandoffTools
    
    style StockAgent fill:#f3e5f5
    style SearchAgent fill:#e8f5e8
    style DARTAgent fill:#fff3e0
    style FutureAgent1 fill:#f0f0f0,stroke-dasharray: 10 10
    style FutureAgent2 fill:#f0f0f0,stroke-dasharray: 10 10

```

---

## Current Implementation Status

### ✅ Completed Components
- **Supervisor Agent**: ChatClovaX-based coordinator with handoff tools for Stock, Search, and DART agents
- **Stock Price Agent**: Full stock analysis with Kiwoom API integration  
- **Search Agent**: Comprehensive search capabilities with Tavily web search and Naver News API
- **DART Agent**: Complete DART API integration with corporate filings analysis
- **PDF Processing**: Upload, chunking, and viewer system
- **Frontend**: React-based UI with chat and PDF viewing
- **APIs**: Upload service (9000) and Query service (8000)
- **State Management**: LangGraph MessagesState and Zustand frontend state
- **Error Handling**: Exponential backoff retry logic for all agents
- **Testing**: E2E integration tests and smoke tests

### 🔜 Ready for Extension
- **Future Agents**: Framework ready for additional specialized agents
- **Additional Tools**: Easy integration pattern established
- **Shared Components**: Reusable state and graph infrastructure
- **API Expansion**: Scalable FastAPI structure

### 🎯 Implementation Status for Search Agent (Evolved from News Agent)

#### ✅ **Production Implementation Completed**
1. **Architecture Evolution**: Refactored from NewsAgent to SearchAgent with expanded capabilities
2. **Comprehensive Tool Suite**: 
   - `tavily_web_search`: Global web search with Tavily API integration and content crawling
   - `search_naver_news_by_relevance`: Korean news search with relevance ranking
   - `search_naver_news_by_date`: Korean news search with latest-first sorting
   - Integrated content crawling for all search results
3. **Pure Autonomous Agent Logic**: True ReAct-style reasoning with NO hard-coded tool selection logic
4. **Supervisor Integration**: `call_search_agent` handoff tool fully integrated
5. **API Integration**: 
   - Tavily Search API for global web search
   - Naver News API for Korean news with enhanced sorting options
   - Content crawling capabilities for deep article analysis
6. **Enhanced Prompts & Tool Descriptions**: Autonomous reasoning guided by detailed system prompts and crystal-clear tool descriptions
7. **Package Structure**: Complete refactored module with expanded capabilities

#### 🚀 **READY FOR PRODUCTION**
- **Full Integration**: SearchAgent is now part of the multi-agent system
- **Supervisor Handoff**: Users can request search analysis through Supervisor
- **Test Coverage**: Test script available at `backend/agents/search_agent/test.py`
- **Documentation**: Complete architecture documentation and implementation guide

### 🎯 Implementation Status for DART Agent

#### ✅ **Production Implementation Completed**
1. **Complete DART API Integration**: Full DART electronic disclosure system access
2. **Comprehensive Tool Suite**: 
   - `get_dart_report_type_code`: AI-powered report type classification
   - `get_dart_report_list`: Corporate report list retrieval with filtering
   - `get_rcept_no_by_date`: Date-based report search and selection
   - `extract_report_then_title_list_from_xml`: Document structure analysis
   - `recommend_section_from_titles_list`: AI-powered section recommendation
   - `extract_report_then_section_text`: Targeted content extraction
3. **Pure Autonomous Agent Logic**: True ReAct-style reasoning with NO hard-coded logic
4. **Supervisor Integration**: `call_dart_agent` handoff tool fully integrated with retry logic
5. **API Integration**: 
   - DART Open API for corporate disclosure documents
   - XML parsing and content extraction capabilities
   - Multi-encoding support for Korean documents
6. **Enhanced Prompts & Tool Descriptions**: Autonomous reasoning guided by detailed system prompts
7. **Package Structure**: Complete modular architecture with proper abstractions

#### 🚀 **READY FOR PRODUCTION**
- **Full Integration**: DART Agent is now part of the multi-agent system
- **Supervisor Handoff**: Users can request corporate disclosure analysis through Supervisor
- **Test Coverage**: Test script available at `backend/agents/dart_agent/test.py`
- **Documentation**: Complete architecture documentation and implementation guide
- **Error Handling**: Robust retry logic and graceful failure handling

This documentation provides a comprehensive view of the current system with the fully implemented SearchAgent and DART Agent, showcasing a production-ready multi-agent architecture with autonomous search and corporate disclosure analysis capabilities.

---

## Testing & Quality Assurance

### Integration Testing

#### E2E Test Suite
**Location**: `backend/test_integrated_mas.py`

**Test Coverage**:
- **DART Agent Tests**: 4 test cases covering report analysis, filing disclosure, audit reports, and M&A announcements
- **Search Agent Tests**: 3 test cases covering latest news, corporate trends, and industry analysis  
- **Stock Price Agent Tests**: 2 test cases covering price analysis and technical indicators
- **Multi-Agent Tests**: 1 complex case requiring coordination between multiple agents

**Test Execution**:
```bash
cd backend
python test_integrated_mas.py
```

**Expected Results**:
- Success Rate: ≥80%
- Average Response Time: <30 seconds per query
- Agent Routing Accuracy: >95%

#### Smoke Tests
**Location**: `backend/smoke_test.sh`

**Coverage**:
- Health check endpoints (Upload API, Supervisor API)
- Agent routing validation
- Error handling verification
- API endpoint availability

**Execution**:
```bash
cd backend
chmod +x smoke_test.sh
./smoke_test.sh
```

### Tool Registry

| Tool Name | Agent | Description | Input | Output |
|-----------|--------|-------------|--------|---------|
| `call_stock_price_agent` | Supervisor | Stock price analysis handoff | Stock query string | Analysis report |
| `call_search_agent` | Supervisor | Web/news search handoff | Search query string | Search results & analysis |
| `call_dart_agent` | Supervisor | Corporate disclosure handoff | DART query string | Filing analysis |
| `get_dart_report_type_code` | DART | Report type classification | User query | Report type code |
| `get_dart_report_list` | DART | Report list retrieval | Company code, report type | Report metadata list |
| `get_rcept_no_by_date` | DART | Date-based report search | Target date, report list | Receipt number |
| `extract_report_then_title_list_from_xml` | DART | Document structure analysis | Receipt number | Title list |
| `recommend_section_from_titles_list` | DART | Section recommendation | Titles, query | Section names |
| `extract_report_then_section_text` | DART | Content extraction | Sections, titles, receipt | Section content |

### Routing Policy

#### DART Agent Triggers
- Keywords: "전자공시", "공시", "DART", "사업보고서", "분기보고서", "반기보고서", "감사보고서"
- Financial Events: "증자", "감자", "전환사채", "합병", "분할", "M&A"
- Corporate Actions: "임원변경", "주주총회", "대주주", "신규사업"

#### Search Agent Triggers  
- Keywords: "뉴스", "속보", "기사", "최신", "동향", "루머"
- Web Queries: General information not in DART or stock data

#### Stock Price Agent Triggers
- Keywords: "주가", "차트", "기술적분석", "이동평균선", "RSI", "MACD"
- Price Actions: "상승", "하락", "거래량", "변동성"

#### Backup Strategy
1. Primary routing failure → Retry with alternative agent
2. Multiple routing failures → Supervisor provides integrated response
3. All agent failures → Error message with troubleshooting guidance

---

## Change Log

### 2025-01-25: DART Agent Integration (v2.0.0)

#### ✅ **Major Features Added**
- **DART Agent Implementation**: Complete corporate disclosure analysis system
- **Enhanced Supervisor**: 3-agent coordination with `call_dart_agent` handoff tool
- **Retry Logic**: Exponential backoff for all agent handoff tools
- **Extended Routing**: Comprehensive routing policy covering DART, Search, and Stock domains
- **Advanced RAG Pipeline**: LangGraph-based PDF processing with Upstage + OpenAI integration
- **Interactive Chunk Citation**: Visual PDF viewer with precise bounding box selection
- **Context Injection System**: Automated chunk content injection into agent prompts

#### 🔧 **Technical Improvements**  
- **Tool Registry**: 6 new DART-specific tools with autonomous reasoning
- **Error Handling**: Graceful degradation and detailed error messages
- **State Management**: Enhanced MessagesState with DART analysis metadata
- **Testing Suite**: E2E integration tests and smoke tests
- **Multi-Modal Processing**: Text, image, and table content analysis pipeline
- **Vector Database Integration**: ChromaDB with CLOVA embeddings optimization
- **Dual Storage Architecture**: processed_states.json + ChromaDB for complete coverage
- **Layout Analysis**: Upstage API for precise document structure understanding

#### 📊 **Architecture Updates**
- **Multi-Agent Graph**: Stock + Search + DART agents fully integrated
- **RAG Pipeline Integration**: Complete LangGraph-based document processing workflow
- **Prompt Engineering**: Updated supervisor prompt with detailed routing examples + context injection
- **Documentation**: Complete architecture diagrams and implementation guides
- **Interactive UI Enhancement**: PDF viewer with chunk overlay and citation capabilities
- **Cross-System Integration**: Seamless data flow between RAG, agents, and frontend

#### 🚀 **Production Readiness**
- **Performance**: <30s average response time for complex queries
- **Reliability**: 80%+ success rate with automatic retry mechanisms  
- **Scalability**: Modular design ready for additional agent integration
- **Monitoring**: Structured logging and test coverage
- **Document Processing**: Production-grade RAG pipeline with batch processing
- **Multi-Modal Support**: Text, image, and table analysis with GPT-4 Vision
- **Korean Optimization**: CLOVA embeddings and specialized language processing
- **Interactive Citation**: Real-time chunk selection and context injection

**Files Modified**:
- `backend/agents/supervisor/agent.py`: Added DART handoff tool with retry logic
- `backend/agents/supervisor/prompt.py`: Enhanced routing policy and examples + context injection
- `backend/agents/dart_agent/`: Complete DART agent implementation
- `backend/rag/src/parser.py`: LangGraph-based PDF processing workflow
- `backend/rag/scripts/process_pdfs.py`: Main RAG pipeline orchestration
- `backend/rag/scripts/import_to_chroma.py`: Vector database integration
- `backend/upload_api.py`: RAG pipeline integration with chunk extraction
- `frontend/components/pdf/`: Interactive PDF viewer with chunk overlay
- `backend/test_integrated_mas.py`: E2E test suite
- `backend/smoke_test.sh`: API smoke tests
- `backend/MULTI_AGENT_SYSTEM_DOCUMENTATION.md`: Complete architecture documentation

**Commit Hash**: `[Generated on deployment]`

---

## Next Steps & Roadmap

### Phase 3: Advanced Features (Future)
- **Custom Analysis Agents**: Domain-specific analysis capabilities
- **Risk Assessment Agent**: Market risk and compliance analysis
- **Multi-language Support**: English/Korean hybrid analysis
- **Real-time Streaming**: WebSocket-based live updates

### Technical Debt & Optimizations
- **Caching Layer**: Redis integration for frequent DART queries
- **Batch Processing**: Multiple query optimization
- **Model Fine-tuning**: ChatClovaX optimization for financial domain
- **Monitoring Dashboard**: Real-time system health visualization

This completes the comprehensive integration of DART Agent and advanced RAG pipeline into the production multi-agent system, establishing a robust foundation for intelligent Korean financial market analysis with interactive document processing capabilities. 
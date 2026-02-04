# ClarityCheck Workflow Mindmap

## Core Processing Flow

```mermaid
flowchart TD
    subgraph UserInterface["🖥️ User Interface"]
        A[Upload PDF] --> B[View Progress]
        B --> C[Review Report]
        C --> D[Compare Views]
        D --> E[Download Clean PDF]
    end

    subgraph Backend["⚙️ Backend Processing"]
        F[Receive Upload] --> G[Validate PDF]
        G --> H[Create Job Record]
        H --> I[Queue for Processing]
    end

    subgraph DetectionEngine["🔍 Detection Engine"]
        J[Load Document] --> K[Run Detector Pipeline]
        K --> L1[Zero-Width Chars]
        K --> L2[Hidden Text]
        K --> L3[Off-Screen Text]
        K --> L4[Opacity Issues]
        K --> L5[Annotations]
        K --> L6[Metadata]
        L1 & L2 & L3 & L4 & L5 & L6 --> M[Aggregate Findings]
        M --> N[Generate Report]
        N --> O[Create Cleaned PDF]
    end

    subgraph n8nAutomation["🔄 n8n Automation"]
        P[Job Complete Webhook]
        Q[Email Notification]
        R[Slack Alert]
        S[Usage Logging]
        T[Batch Processor]
    end

    A --> F
    I --> J
    O --> C
    O --> P
    P --> Q & R & S
```

## Detection Module Architecture

```mermaid
flowchart LR
    subgraph DetectorRegistry["Detector Registry"]
        REG[Registry Manager]
    end

    subgraph Detectors["Pluggable Detectors"]
        D1["ZeroWidthCharDetector"]
        D2["MatchingColorDetector"]
        D3["OffScreenTextDetector"]
        D4["OpacityHiddenDetector"]
        D5["HiddenAnnotationDetector"]
        D6["MetadataDetector"]
    end

    subgraph Interface["Common Interface"]
        I1["detect(doc) → Findings"]
        I2["remediate(doc, finding) → Doc"]
        I3["severity: str"]
        I4["enabled: bool"]
    end

    REG --> D1 & D2 & D3 & D4 & D5 & D6
    D1 & D2 & D3 & D4 & D5 & D6 --> Interface
```

## Data Flow

```mermaid
flowchart TD
    subgraph Input
        PDF[("📄 Original PDF")]
    end

    subgraph Processing
        PARSE["Parse with PyMuPDF"]
        EXTRACT["Extract Text + Metadata"]
        DETECT["Run Detectors"]
        ANNOTATE["Generate Highlighted PDF"]
        CLEAN["Generate Cleaned PDF"]
    end

    subgraph Storage
        DB[("💾 SQLite/Postgres")]
        FILES[("📁 File Storage")]
    end

    subgraph Output
        REPORT["📊 JSON Report"]
        ORIG_HL["📄 Original + Highlights"]
        CLEANED["📄 Cleaned PDF"]
    end

    PDF --> PARSE --> EXTRACT --> DETECT
    DETECT --> REPORT --> DB
    DETECT --> ANNOTATE --> ORIG_HL --> FILES
    DETECT --> CLEAN --> CLEANED --> FILES
```

## n8n Integration Points

```mermaid
flowchart LR
    subgraph Backend
        API["FastAPI Backend"]
        WEBHOOK["Webhook Sender"]
    end

    subgraph n8n["n8n Workflows"]
        W1["Job Complete Handler"]
        W2["Daily Summary Generator"]
        W3["Batch Upload Watcher"]
        W4["Error Alert Handler"]
    end

    subgraph External["External Services"]
        EMAIL["📧 Email (SMTP)"]
        SLACK["💬 Slack"]
        S3["☁️ S3/Storage"]
        METRICS["📈 Analytics"]
    end

    API --> WEBHOOK --> W1
    W1 --> EMAIL & SLACK
    W2 --> EMAIL & METRICS
    W3 --> S3 --> API
    API --> W4 --> SLACK
```

## User Journey

```mermaid
journey
    title ClarityCheck User Journey
    section Upload
      Visit site: 5: User
      Drag & drop PDF: 5: User
      See upload progress: 4: User
    section Analysis
      Wait for processing: 3: User
      View findings summary: 5: User
      Explore detailed report: 4: User
    section Review
      See highlighted issues: 5: User
      Compare original vs clean: 5: User
      Understand each issue: 4: User
    section Export
      Download clean PDF: 5: User
      Share report: 4: User
```

## Component Mindmap

```mermaid
mindmap
  root((ClarityCheck))
    Frontend
      React SPA
      PDF Viewer
        pdf.js
        Dual Pane
        Highlighting
      Upload Component
      Report Display
    Backend
      FastAPI
        REST API
        File Handling
        Job Management
      Detection Engine
        Detector Plugins
        Finding Aggregator
        Report Generator
      Workers
        Celery Tasks
        PDF Processing
        Cleanup Jobs
    Data Layer
      SQLite/Postgres
        Jobs Table
        Findings Table
        Users Table
      File Storage
        Uploaded PDFs
        Processed PDFs
        Reports
    Automation
      n8n
        Notifications
        Batch Processing
        Integrations
    Infrastructure
      Redis
        Job Queue
        Caching
      Docker
        Containerization
```

## State Machine: Job Processing

```mermaid
stateDiagram-v2
    [*] --> Pending: Upload received
    Pending --> Validating: Worker picks up
    Validating --> Processing: Valid PDF
    Validating --> Failed: Invalid file
    Processing --> Analyzing: Detectors running
    Analyzing --> Generating: Findings complete
    Generating --> Complete: Reports ready
    Complete --> [*]
    Failed --> [*]
    
    Processing --> Failed: Processing error
    Analyzing --> Failed: Detection error
    Generating --> Failed: Generation error
```

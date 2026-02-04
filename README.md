# ClarityCheck

**Document Sanitization for Assistive Technology Compliance**

ClarityCheck detects and removes "digital clutter" from PDFs—invisible elements that screen readers vocalize but sighted users never see. This includes zero-width characters, hidden text layers, off-screen content, and more.

## Why ClarityCheck?

Screen readers interpret documents differently than visual rendering. Elements like:
- Zero-width spaces (​) causing unexpected pauses
- White text on white backgrounds being read aloud
- Hidden annotations and metadata cluttering the experience

...create a confusing, inaccessible experience for visually impaired users.

## Features (MVP)

- **Deep Analysis Engine**: Modular detection of 6+ accessibility artifacts
- **Comprehensive Reporting**: Detailed findings with locations and explanations
- **Dual-Pane Visualizer**: See what screen readers "see" vs. the cleaned version
- **One-Click Remediation**: Download sanitized, accessible PDFs

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, Celery |
| PDF Processing | PyMuPDF (fitz), pdfplumber |
| Frontend | React, TypeScript, pdf.js |
| Database | SQLite (MVP) → PostgreSQL |
| Queue | Redis |
| Automation | n8n (local) |

## Project Structure

```
ClarityCheck/
├── docs/                    # Documentation & diagrams
├── src/
│   ├── api/                 # FastAPI routes
│   ├── core/                # Detection engine, models
│   └── workers/             # Celery background tasks
├── frontend/                # React application
├── n8n-workflows/           # Exported n8n workflow definitions
└── tests/                   # pytest test suite
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (for job queue)
- n8n (optional, for automation)

### Backend Setup

```bash
cd ClarityCheck
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### n8n Setup (Optional)

```bash
# Run n8n locally with Docker
docker run -it --rm \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# Import workflows from n8n-workflows/ directory
```

## Detection Modules

| Detector | Description | Severity |
|----------|-------------|----------|
| ZeroWidthCharDetector | ZWSP, ZWNJ, ZWJ, soft hyphens | High |
| MatchingColorDetector | Text color matches background | High |
| OffScreenTextDetector | Text positioned outside page bounds | Medium |
| OpacityHiddenDetector | Text with zero or near-zero opacity | High |
| HiddenAnnotationDetector | Non-visible PDF annotations | Medium |
| MetadataDetector | Potentially problematic metadata | Low |

## API Endpoints

```
POST /api/documents/upload     Upload PDF, returns job_id
GET  /api/jobs/{id}            Get job status
GET  /api/jobs/{id}/report     Get findings report
GET  /api/jobs/{id}/preview/original   Highlighted original
GET  /api/jobs/{id}/preview/cleaned    Cleaned preview
GET  /api/jobs/{id}/download   Download cleaned PDF
```

## Target Users

- 🎓 Educational institutions (course materials)
- 🏛️ Government agencies (ADA compliance)
- 🏢 Corporations (public-facing documents)
- 👩‍💻 Developers (QA workflow integration)

## Roadmap

- [x] Project setup and architecture
- [ ] Phase 1: Foundation (FastAPI, first detector)
- [ ] Phase 2: Detection engine (all MVP detectors)
- [ ] Phase 3: Frontend (React, dual-pane viewer)
- [ ] Phase 4: Integration (n8n, polish)

## License

TBD

## Contributing

TBD

# ClarityCheck

**PDF hidden-content and AI trap scanner**

ClarityCheck is a live web app for finding hidden or misleading content inside PDFs before people or AI systems trust the document. It detects invisible text, off-page content, tiny text, low-contrast content, metadata issues, and prompt-injection style instructions, then lets the user review findings and download a sanitized PDF.

Live app: https://clarity-frontend-0unn.onrender.com

API health: https://clarity-api-znva.onrender.com/health

## Why It Exists

PDFs can contain content that is not obvious to a human reviewer but still affects downstream systems. Examples include:

- White text on white backgrounds
- Text placed outside the visible page
- Tiny or low-contrast text
- Hidden annotations and metadata
- Prompt-injection instructions aimed at AI tools

ClarityCheck turns that hidden layer into a visible review workflow.

## Features

- **PDF upload and analysis**: Upload a PDF and receive a structured risk report.
- **Hidden-content detectors**: Finds invisible, off-page, tiny, low-contrast, annotation, metadata, and zero-width character issues.
- **Optional LLM refinement**: Uses Gemini to help classify whether suspicious hidden text is an AI instruction trap.
- **Review workflow**: Inspect findings by type, location, severity, and explanation.
- **Sanitization**: Download a cleaned PDF with selected hidden content removed.
- **Live deployment**: React frontend and FastAPI backend deployed on Render.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| PDF Processing | PyMuPDF (fitz), pdfplumber |
| Frontend | React, TypeScript, pdf.js |
| Database | SQLite demo fallback / Postgres-ready config |
| LLM | Gemini API for optional semantic refinement |
| Deployment | Render static site + Docker web service |

## Project Structure

```
ClarityCheck/
├── backend/                 # FastAPI routes, database, detection engine
├── frontend/                # React application
├── docs/                    # Documentation and diagrams
├── tests/                   # pytest test suite
├── render.yaml              # Render deployment config
└── trap_factory.py          # Generates test PDFs with hidden traps
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Optional: Google Gemini API key for LLM refinement

### Backend Setup

```bash
cd ClarityCheck
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Optional LLM Settings

```env
LLM_DETECTOR_ENABLED=true
GEMINI_API_KEY=your_google_api_key
LLM_MODEL=gemini-2.5-flash
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
| TinyTextDetector | Very small text that can hide instructions | Medium |
| InvisibleRenderDetector | Text using invisible PDF render modes | High |

## API Endpoints

```
POST /api/documents/upload     Upload PDF, returns job_id
GET  /api/jobs/{id}            Get job status
GET  /api/jobs/{id}/analysis   Get findings report
POST /api/jobs/{id}/sanitize   Download sanitized PDF
GET  /api/usage                Get upload usage
```

## Demo Validation

The live API was smoke-tested with `trap_gallery.pdf`: upload completed, analysis finished, and the app returned a structured risk report.

## Best Fit Use Cases

- Reviewing uploaded PDFs before passing them into AI tools
- Checking contracts, resumes, school documents, or forms for hidden content
- Demonstrating document-trust and prompt-injection defense workflows
- Sanitizing PDFs before downstream processing

## License

TBD

## Contributing

TBD

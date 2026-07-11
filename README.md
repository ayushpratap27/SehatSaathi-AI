# SehatSaathi-AI

**AI-powered Medical Report Understanding System**

SehatSaathi-AI helps patients understand complex medical reports in plain, simple language using modern AI, NLP, and Retrieval-Augmented Generation (RAG) techniques.

> ⚠️ **Disclaimer:** This is an informational tool only. It explains the contents of uploaded medical reports but does **not** diagnose, prescribe, or replace professional medical advice. Always consult a qualified healthcare professional for medical decisions.

---

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Foundation & project scaffolding | ✅ Complete |
| **Phase 2** | Document ingestion pipeline (PDF + OCR) | ✅ Complete |
| **Phase 3** | Medical information extraction (NER + structured JSON) | ✅ Complete |
| **Phase 4** | Medical Analysis Engine (reference ranges + insights) | ✅ Complete |
| Phase 5 | AI report understanding & summaries | 🔜 Next |
| Phase 6 | Intelligent chat assistant | 🔜 Planned |
| Phase 7 | Streamlit MVP frontend | 🔜 Planned |
| Phase 8 | Authentication & user management | 🔜 Planned |
| Phase 9 | Testing, hardening & CI/CD | 🔜 Planned |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Config | Pydantic BaseSettings |
| Database | SQLAlchemy + Alembic (SQLite dev / PostgreSQL prod) |
| AI / NLP | spaCy, SciSpaCy, LangChain, FAISS, Sentence Transformers |
| OCR | EasyOCR, PyMuPDF, pdfplumber |
| Frontend | Streamlit (MVP) |
| Infrastructure | Docker, GitHub Actions |

---

## Project Structure

```
SehatSaathi-AI/
├── app/                    # FastAPI application
│   ├── api/v1/             # Versioned API routes
│   │   └── endpoints/      # upload, report, analysis, chat, auth
│   ├── config/             # Pydantic settings
│   ├── core/               # Logging, exceptions
│   ├── database/           # SQLAlchemy session (Phase 2)
│   ├── models/             # ORM models (Phase 2)
│   ├── schemas/            # Pydantic request/response models (Phase 2)
│   ├── services/           # Business logic layer (Phase 2+)
│   ├── middleware/         # FastAPI middleware (Phase 8)
│   └── utils/              # Shared utilities
├── ai/                     # AI module (Phase 2+)
│   ├── ocr/                # OCR pipeline
│   ├── preprocessing/      # Text cleaning
│   ├── ner/                # Medical NER
│   ├── summarization/      # Report summarization
│   ├── rag/                # RAG pipeline
│   └── embeddings/         # Sentence embeddings
├── data/
│   ├── uploads/            # Uploaded documents
│   ├── processed/          # Processed outputs
│   ├── temp/               # Temporary working files
│   └── reference_ranges/   # Lab reference range configs
├── frontend/               # Streamlit UI
├── tests/                  # Unit & integration tests
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── docker/                 # Docker configuration
├── logs/                   # Application logs
├── main.py                 # FastAPI entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher (3.12 recommended)
- pip
- Git
- **For OCR (scanned documents):** PaddleOCR requires `paddlepaddle` + `paddleocr`

### 1. Clone the repository

```bash
git clone https://github.com/ayushpratap27/SehatSaathi-AI.git
cd SehatSaathi-AI
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install PaddleOCR (required for scanned documents and images)

```bash
# CPU version (works on macOS, Linux, Windows)
pip install paddlepaddle paddleocr

# PaddleOCR downloads model weights (~200 MB) on first use.
# Ensure you have internet access when running OCR for the first time.
```

### 5. Set up environment variables

```bash
cp .env.example .env
# Edit .env if you need non-default paths or settings
```

### 6. Start the backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

### 7. Start the frontend

Open a new terminal (keep the backend running):

```bash
streamlit run frontend/app.py
```

The Streamlit app will open at http://localhost:8501

---

## API Overview (Phase 3)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/` | Application info | ✅ |
| GET | `/health` | Health check | ✅ |
| POST | `/api/v1/upload/` | Upload & store a medical report | ✅ Phase 2 |
| POST | `/api/v1/report/extract` | Extract text from a report | ✅ Phase 2 |
| **POST** | **`/api/v1/report/parse`** | **Structured JSON from report** | **✅ Phase 3** |
| **POST** | **`/api/v1/analysis/analyze`** | **Medical analysis from ParsedReport** | **✅ Phase 4** |
| GET | `/api/v1/report/{id}` | Get structured report data | 🔜 Phase 5 |
| GET | `/api/v1/analysis/{id}/entities` | Medical entities | 🔜 Phase 4 |
| GET | `/api/v1/analysis/{id}/lab-values` | Lab results | 🔜 Phase 4 |
| POST | `/api/v1/chat/session` | Create chat session | 🔜 Phase 6 |
| POST | `/api/v1/auth/register` | Register user | 🔜 Phase 8 |

### `/parse` endpoint — two ways to call it

**Option A — Upload a file:**
```bash
curl -X POST http://localhost:8000/api/v1/report/parse \
  -F "file=@blood_test.pdf"
```

**Option B — Send extracted text directly (from Phase 2 `/extract`):**
```bash
curl -X POST http://localhost:8000/api/v1/report/parse \
  -F "text=Patient Name: John Doe\nHemoglobin\n12.4 g/dL\nReference\n13.5-17.5"
```

### Example structured JSON response

```json
{
  "patient": { "name": "John Doe", "age": 45, "gender": "Male" },
  "hospital": { "name": "ABC Hospital" },
  "doctor": { "name": null },
  "tests": [
    { "test_name": "Hemoglobin", "value": 12.4, "unit": "g/dL",
      "reference_range": "13.5-17.5", "status": "Low" },
    { "test_name": "WBC Count", "value": 11200, "unit": "/uL",
      "reference_range": "4000-11000", "status": "High" }
  ],
  "diagnosis": ["Iron Deficiency Anemia"],
  "medicines": [{ "name": "Ferrous Sulfate", "dosage": "150mg", "frequency": "Once daily" }]
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Contributing

This project is developed incrementally. Each phase builds on the previous one while maintaining backward compatibility. See the phase table above for current status.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

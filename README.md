# SehatSaathi-AI

**AI-powered Medical Report Understanding System**

SehatSaathi-AI helps patients understand complex medical reports in plain, simple language using modern AI, NLP, and Retrieval-Augmented Generation (RAG) techniques.

> ⚠️ **Disclaimer:** This is an informational tool only. It explains the contents of uploaded medical reports but does **not** diagnose, prescribe, or replace professional medical advice. Always consult a qualified healthcare professional for medical decisions.

---

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Foundation & project scaffolding | ✅ Complete |
| Phase 2 | Document upload & PDF/OCR processing | 🔜 Next |
| Phase 3 | Medical NLP & lab value extraction | 🔜 Planned |
| Phase 4 | Vector store & RAG pipeline | 🔜 Planned |
| Phase 5 | AI report understanding & summaries | 🔜 Planned |
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

- Python 3.12 or higher
- pip
- Git

### 1. Clone the repository

```bash
git clone https://github.com/ayushpratap27/SehatSaathi-AI.git
cd SehatSaathi-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Edit .env and update any values as needed
```

### 5. Start the backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

### 6. Start the frontend

Open a new terminal tab (keep the backend running):

```bash
streamlit run frontend/app.py
```

The Streamlit app will open at http://localhost:8501

---

## API Overview (Phase 1 — Placeholders)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Application info |
| GET | `/health` | Health check |
| POST | `/api/v1/auth/register` | Register user *(Phase 8)* |
| POST | `/api/v1/auth/login` | Login *(Phase 8)* |
| POST | `/api/v1/upload/` | Upload medical report *(Phase 2)* |
| GET | `/api/v1/upload/status/{id}` | Processing status *(Phase 2)* |
| GET | `/api/v1/report/{id}` | Get report data *(Phase 3)* |
| GET | `/api/v1/report/{id}/summary` | Report summary *(Phase 5)* |
| GET | `/api/v1/analysis/{id}/entities` | Medical entities *(Phase 3)* |
| GET | `/api/v1/analysis/{id}/lab-values` | Lab results *(Phase 3)* |
| POST | `/api/v1/chat/session` | Create chat session *(Phase 6)* |
| POST | `/api/v1/chat/session/{id}/message` | Chat Q&A *(Phase 6)* |

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

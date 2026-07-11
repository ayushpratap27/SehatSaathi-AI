<div align="center">

# 🏥 SehatSaathi-AI

### AI-powered Medical Report Understanding System

**Transform complex medical reports into clear, patient-friendly insights using OCR, Medical NLP, Clinical Rule Engine, and Google Gemini 2.5 Flash.**

[![CI](https://github.com/ayushpratap27/SehatSaathi-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/ayushpratap27/SehatSaathi-AI/actions)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

> ⚠️ **Medical Disclaimer:** SehatSaathi-AI is an informational tool only. It does **not** provide medical diagnoses, prescriptions, or treatment recommendations. All AI-generated insights are based solely on the uploaded report data. Always consult a qualified healthcare professional for medical decisions.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Development Phases](#-development-phases)
- [Quick Start](#-quick-start)
- [Docker Setup](#-docker-setup)
- [API Reference](#-api-reference)
- [Environment Variables](#-environment-variables)
- [Running Tests](#-running-tests)
- [Database Migrations](#-database-migrations)
- [Adding New Lab Tests](#-adding-new-lab-tests)
- [Production Deployment](#-production-deployment)
- [Future Scope](#-future-scope)
- [License](#-license)

---

## 🩺 Project Overview

SehatSaathi-AI helps patients understand their medical reports in plain language. The system:

- **Accepts** PDFs, PNGs, JPGs, and TIFF medical reports
- **Extracts** text using PyMuPDF for digital PDFs and PaddleOCR for scanned documents
- **Identifies** medical entities — diseases, lab tests, medicines, diagnoses — using spaCy/SciSpaCy
- **Analyses** laboratory values against configurable clinical reference ranges
- **Generates** plain-language summaries and explanations using Google Gemini 2.5 Flash
- **Answers** natural-language questions via a RAG pipeline (FAISS + Gemini embeddings)
- **Persists** reports, analyses, and chat history per authenticated user
- **Serves** a modern React 19 dashboard with drag-and-drop upload and an AI chat interface

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React 19 Frontend                        │
│  Dashboard · Upload · Report Viewer · Chat · Profile        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS via Nginx
┌─────────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend (v1)                      │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │   Auth   │  │ Reports  │  │Dashboard │  │Monitoring │  │
│  │  (JWT)   │  │(CRUD+DB) │  │  (Redis) │  │/health    │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AI Processing Pipeline                  │  │
│  │                                                      │  │
│  │  Upload → OCR → NER → Clinical Rules → Gemini AI    │  │
│  │                                                      │  │
│  │  Phase 2       Phase 3     Phase 4      Phase 5/6   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
         │                          │
┌────────▼────────┐      ┌──────────▼──────────┐
│   PostgreSQL    │      │        Redis          │
│  (Users,Reports │      │  (Dashboard cache,   │
│   Chat history) │      │   session store)     │
└─────────────────┘      └──────────────────────┘
```

### AI Pipeline Flow

```
PDF / Image
    │
    ▼
[Phase 2] OCR Engine
    PyMuPDF  ──────► digital PDF text
    PaddleOCR ─────► scanned PDF / image text
    pdfplumber ────► table extraction
    │
    ▼
[Phase 2] Text Cleaner
    Unicode normalise · remove artefacts · merge hyphenations
    │
    ▼
[Phase 3] Medical NER
    spaCy + SciSpaCy · patient info · lab values · medicines · diagnoses
    │
    ▼
[Phase 3] JSON Builder  ──► ParsedReport JSON
    │
    ▼
[Phase 4] Clinical Rule Engine
    YAML reference ranges · gender/age-aware · status: Normal/Low/High/Critical
    │
    ▼
[Phase 4] ReportAnalysisResult JSON
    │                           │
    ▼                           ▼
[Phase 5] Gemini AI         [Phase 6] RAG Pipeline
  Executive Summary           FAISS index per document
  Explanations                Gemini text-embedding-004
  Grounded Chat               Cosine similarity retrieval
                              Reranker + Context Builder
                              Grounded Q&A with citations
```

---

## 🛠️ Technology Stack

### Backend
| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI 0.115 |
| Server | Uvicorn |
| ORM | SQLAlchemy 2.x async |
| Migrations | Alembic |
| Auth | PyJWT + bcrypt |
| Cache | Redis 7 |
| Validation | Pydantic v2 |

### AI & NLP
| Component | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Embeddings | Gemini text-embedding-004 |
| Vector Store | FAISS (IndexFlatIP) |
| OCR | PaddleOCR, PyMuPDF, pdfplumber |
| Medical NLP | spaCy + SciSpaCy |
| Similarity | Cosine similarity (normalised inner product) |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 19 + TypeScript |
| Build | Vite 6 |
| Styling | Tailwind CSS 3 |
| State | TanStack Query v5 |
| Routing | React Router v6 |
| Forms | React Hook Form + Zod |
| HTTP | Axios (with JWT auto-refresh) |
| Markdown | react-markdown |
| Upload | react-dropzone |

### Infrastructure
| Component | Technology |
|---|---|
| Proxy | Nginx |
| Containers | Docker + Docker Compose |
| Database | PostgreSQL 16 (prod) / SQLite (dev) |
| Cache | Redis 7 |
| CI/CD | GitHub Actions |

---

## 📁 Project Structure

```
SehatSaathi-AI/
│
├── frontend/                        # React 19 TypeScript SPA
│   ├── src/
│   │   ├── App.tsx                  # Routes + lazy loading
│   │   ├── main.tsx                 # App entry point
│   │   ├── index.css                # Tailwind base styles
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── UploadPage.tsx
│   │   │   ├── ReportDetailPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   ├── ProfilePage.tsx
│   │   │   └── NotFoundPage.tsx
│   │   ├── components/
│   │   │   ├── auth/ProtectedRoute.tsx
│   │   │   ├── layout/Layout.tsx + Sidebar.tsx
│   │   │   └── ui/Card · StatusBadge · LoadingSpinner
│   │   ├── services/
│   │   │   ├── api.ts               # Axios instance + interceptors
│   │   │   ├── authService.ts
│   │   │   ├── reportService.ts
│   │   │   └── analysisService.ts
│   │   ├── context/AuthContext.tsx
│   │   ├── types/index.ts           # All TypeScript type definitions
│   │   └── test/                    # Vitest component + service tests
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
│
├── app/                             # FastAPI application
│   ├── api/v1/endpoints/
│   │   ├── auth.py                  # register · login · refresh · logout · me
│   │   ├── reports.py               # CRUD report management (authenticated)
│   │   ├── dashboard.py             # Dashboard stats
│   │   ├── upload.py                # Phase 2: upload endpoint
│   │   ├── report.py                # Phase 2-3: extract · parse
│   │   ├── analysis.py              # Phase 4: analyze
│   │   ├── ai.py                    # Phase 5: summary · explain · chat · stream
│   │   ├── rag.py                   # Phase 6: index · search · chat
│   │   ├── chat.py                  # Placeholder (future)
│   │   └── monitoring.py            # /health · /ready · /metrics
│   ├── auth/
│   │   ├── jwt_handler.py           # JWT create/decode + bcrypt
│   │   └── dependencies.py          # get_current_user, get_optional_user
│   ├── config/settings.py           # Pydantic BaseSettings
│   ├── core/
│   │   ├── exceptions.py            # Custom exception types + handlers
│   │   ├── logging.py               # Rotating file + console logger
│   │   ├── redis.py                 # Redis connection (graceful fallback)
│   │   └── cache.py                 # get/set/delete cache helpers
│   ├── database/
│   │   ├── base.py                  # DeclarativeBase + TimestampMixin
│   │   ├── session.py               # Async engine + get_db dependency
│   │   └── init_db.py               # Table creation for dev/test
│   ├── models/
│   │   ├── user.py                  # User · RefreshToken
│   │   ├── report.py                # Report · ReportAnalysis
│   │   ├── chat.py                  # ChatSession · ChatMessage
│   │   └── audit.py                 # AuditLog
│   ├── repositories/
│   │   ├── base_repo.py             # Generic async CRUD base
│   │   ├── user_repo.py
│   │   ├── report_repo.py
│   │   └── chat_repo.py
│   ├── schemas/
│   │   ├── document.py              # Upload/Extraction schemas
│   │   ├── report.py                # ParsedReport · LabTest · MedicineInfo
│   │   ├── analysis.py              # ReportAnalysisResult · TestAnalysisResult
│   │   ├── ai.py                    # SummaryResponse · ChatResponse
│   │   ├── rag.py                   # RAGChatResponse · CitationSource
│   │   ├── auth.py                  # RegisterRequest · LoginRequest · TokenPair
│   │   └── dashboard.py             # DashboardStats · RecentReport
│   ├── services/
│   │   ├── document_service.py      # Phase 2: PDF/OCR orchestration
│   │   ├── user_service.py          # Phase 7: register/login/token lifecycle
│   │   ├── report_service.py        # Phase 7: report CRUD + ownership
│   │   └── dashboard_service.py     # Phase 7: stats aggregation
│   └── utils/
│       ├── file_manager.py          # save · delete · generate UUID filename
│       ├── text_cleaner.py          # clean_text() post-OCR normaliser
│       ├── validators.py            # File validation (extension, size, magic bytes)
│       ├── regex_patterns.py        # 20+ pre-compiled medical regex patterns
│       └── normalizer.py            # Test name · unit · gender normalisation
│
├── ai/                              # AI modules (stateless, no DB)
│   ├── gemini/
│   │   ├── gemini_client.py         # Lazy singleton, async generate + stream
│   │   ├── prompt_templates.py      # Summary · explain · chat · retry prompts
│   │   ├── medical_guardrails.py    # System instruction + forbidden phrases
│   │   ├── response_validator.py    # JSON extraction + hallucination check
│   │   ├── summary_service.py       # Executive + patient-friendly summary
│   │   ├── explanation_service.py   # Per-entity plain-language explanations
│   │   └── chat_service.py          # Grounded Q&A (non-RAG)
│   ├── rag/
│   │   ├── chunker.py               # Section-aware sliding-window chunker
│   │   ├── embedding_service.py     # Gemini text-embedding-004 wrapper
│   │   ├── vector_store.py          # FAISS IndexFlatIP + VectorStoreManager
│   │   ├── retriever.py             # Query embed → FAISS search → top-K
│   │   ├── reranker.py              # Dedup + priority-section boost
│   │   ├── context_builder.py       # Build grounded Gemini prompt
│   │   ├── citation_generator.py    # Source citations with page + score
│   │   ├── rag_chat_service.py      # Full RAG orchestrator
│   │   └── similarity_search.py     # Cosine similarity + top-K filtering
│   ├── ner/
│   │   ├── medical_nlp.py           # spaCy/SciSpaCy pipeline (graceful fallback)
│   │   ├── patient_extractor.py
│   │   ├── doctor_extractor.py
│   │   ├── hospital_extractor.py
│   │   ├── lab_extractor.py         # 3-strategy: multi-line · inline · table
│   │   ├── medicine_extractor.py
│   │   ├── diagnosis_extractor.py
│   │   ├── reference_range_parser.py # Parse ranges + derive status
│   │   └── json_builder.py          # Orchestrates all extractors
│   ├── analysis/
│   │   ├── medical_rules.py         # Status labels · risk levels · thresholds
│   │   ├── reference_engine.py      # Load YAML + resolve gender/age ranges
│   │   ├── status_engine.py         # 11-level status determination
│   │   ├── critical_value_detector.py
│   │   ├── abnormality_detector.py
│   │   ├── insight_generator.py     # Plain-language per-test explanations
│   │   ├── risk_analyzer.py         # Overall risk level + summary
│   │   ├── recommendation_engine.py # Safe general recommendations
│   │   └── report_analyzer.py       # Orchestrates full analysis pipeline
│   └── utils/
│       └── token_counter.py         # Estimate + track Gemini token usage
│
├── config/reference_ranges/         # YAML clinical reference configs
│   ├── haematology.yaml             # Hb · WBC · Platelets · RBC · MCV etc.
│   ├── biochemistry.yaml            # Glucose · Creatinine · Electrolytes · LFT
│   ├── lipids.yaml                  # Cholesterol · LDL · HDL · Triglycerides
│   ├── thyroid.yaml                 # TSH · T3 · T4 · Free T3/T4
│   └── iron_coagulation.yaml        # Ferritin · TIBC · PT · INR · APTT
│
├── alembic/                         # Alembic migration files
│   ├── env.py                       # Async-compatible migration runner
│   └── versions/                    # Migration scripts
│
├── tests/
│   ├── conftest.py                  # Shared fixtures (client, PDF bytes, PNG bytes)
│   ├── unit/
│   │   ├── test_text_cleaner.py
│   │   ├── test_file_manager.py
│   │   ├── test_upload_api.py
│   │   ├── test_extraction_api.py
│   │   ├── test_pdf_extraction.py
│   │   ├── test_patient_extractor.py
│   │   ├── test_lab_extractor.py
│   │   ├── test_medicine_extractor.py
│   │   ├── test_diagnosis_extractor.py
│   │   ├── test_json_builder.py
│   │   ├── test_analysis_engine.py
│   │   ├── test_rag_pipeline.py
│   │   └── test_auth.py
│   └── integration/
│       └── test_full_workflow.py    # End-to-end upload → extract → parse → analyze
│
├── nginx/nginx.conf                 # Reverse proxy + gzip + security headers
├── docs/production_checklist.md    # 40+ item deployment checklist
├── Dockerfile                       # Multi-stage backend image
├── docker-compose.yml               # Full stack: API + React + PostgreSQL + Redis + Nginx
├── Makefile                         # Developer shortcuts (make dev, make test, …)
├── alembic.ini
├── .env.example
├── .editorconfig
├── .pre-commit-config.yaml
├── .gitignore
└── .github/workflows/ci.yml         # lint + test + Docker build CI
```

---

## 🚀 Development Phases

| Phase | Description | Key Deliverables |
|---|---|---|
| **1** | Foundation & scaffolding | FastAPI skeleton, config, logging, placeholder endpoints, Streamlit landing page |
| **2** | Document ingestion | PDF text extraction (PyMuPDF + pdfplumber), OCR (PaddleOCR), scanned detection, text cleaner |
| **3** | Medical NER | spaCy/SciSpaCy pipeline, patient/lab/medicine/diagnosis extractors, JSON builder |
| **4** | Clinical rule engine | YAML reference ranges (50+ tests), 11-level status, risk analyser, insights, recommendations |
| **5** | Gemini AI layer | Executive summary, plain-language explanations, grounded chat, SSE streaming, guardrails |
| **6** | RAG pipeline | Gemini embeddings, FAISS vector store, retriever, reranker, context builder, citations |
| **7** | Authentication & DB | SQLAlchemy async, Alembic, JWT auth, repository pattern, dashboard API, report history |
| **8** | Frontend & production | React 19 SPA, Docker + Nginx, Redis cache, GitHub Actions CI, security headers, integration tests |

**Total tests:** 222 passing · **Zero external test dependencies** (all mocked)

---

## ⚡ Quick Start

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.12+ |
| Node.js | 22+ |
| Git | any |
| Gemini API Key | [Get free key](https://aistudio.google.com/apikey) |

### 1. Clone and configure

```bash
git clone https://github.com/ayushpratap27/SehatSaathi-AI.git
cd SehatSaathi-AI

# Copy environment template
cp .env.example .env

# Edit .env and set at minimum:
# GEMINI_API_KEY=your_key_here
# SECRET_KEY=$(openssl rand -hex 32)
```

### 2. Backend setup

```bash
# Create virtual environment and install dependencies
make install

# Activate the virtual environment
source .venv/bin/activate

# Start the API server
uvicorn main:app --reload
```

The backend starts at:
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 3. Frontend setup

```bash
# In a new terminal
make install-frontend
cd frontend && npm run dev
```

The frontend starts at http://localhost:3000

### 4. Install PaddleOCR (required for scanned documents)

```bash
pip install paddlepaddle paddleocr
# Model weights (~200 MB) download on first OCR request
```

---

## 🐳 Docker Setup

The easiest way to run the full stack:

```bash
cp .env.example .env
# Set GEMINI_API_KEY and SECRET_KEY in .env

docker compose up --build
```

| Service | URL |
|---|---|
| **Frontend** (via Nginx) | http://localhost |
| **Backend API** | http://localhost:8000 |
| **Swagger Docs** | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

```bash
# Useful Docker commands
make docker-logs          # tail all service logs
docker compose logs -f backend   # backend logs only
make docker-down          # stop everything
make docker-clean         # remove containers + volumes
```

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Create account → access + refresh tokens |
| POST | `/api/v1/auth/login` | — | Login → tokens |
| POST | `/api/v1/auth/refresh` | — | Exchange refresh token for new access token |
| POST | `/api/v1/auth/logout` | — | Revoke refresh token |
| GET | `/api/v1/auth/me` | ✅ | Current user profile |

### Report Management (authenticated)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/reports/upload` | ✅ | Upload report → DB record |
| GET | `/api/v1/reports` | ✅ | List user's reports (paginated) |
| GET | `/api/v1/reports/{id}` | ✅ | Report details |
| DELETE | `/api/v1/reports/{id}` | ✅ | Soft-delete report |
| GET | `/api/v1/reports/{id}/analysis` | ✅ | Stored clinical analysis |
| GET | `/api/v1/reports/{id}/chat-history` | ✅ | Chat sessions + messages |

### Dashboard (authenticated)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/dashboard` | ✅ | Stats: total, this month, completed, recent 5 |

### Document Processing Pipeline

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/upload/` | Upload file → store with UUID filename |
| POST | `/api/v1/report/extract` | File → extracted clean text |
| POST | `/api/v1/report/parse` | Text or file → structured JSON (ParsedReport) |
| POST | `/api/v1/analysis/analyze` | ParsedReport → clinical analysis with insights |

### AI Services (Gemini)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/ai/summary` | ParsedReport + Analysis → executive summary |
| POST | `/api/v1/ai/explain` | ParsedReport → per-entity plain-language explanations |
| POST | `/api/v1/ai/chat` | Question + Report → grounded answer (non-RAG) |
| POST | `/api/v1/ai/stream/summary` | SSE streaming summary |
| GET | `/api/v1/ai/health` | Gemini API connectivity check |

### RAG Pipeline

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/rag/index` | Text → FAISS index (stored in `data/vector_stores/`) |
| POST | `/api/v1/rag/search` | Question + doc ID → top-K relevant chunks |
| POST | `/api/v1/rag/chat` | Question + doc ID → grounded answer with citations |

### Monitoring

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness probe (always 200 if running) |
| GET | `/api/v1/ready` | Readiness probe (checks DB + Redis) |
| GET | `/api/v1/metrics` | Uptime, PID, Python version |

---

## 🔧 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | **Yes** | — | Google Gemini API key |
| `SECRET_KEY` | **Yes** | dev-only | JWT signing key — use `openssl rand -hex 32` |
| `DATABASE_URL` | **Yes** | `sqlite+aiosqlite:///./sehat_saathi.db` | Database connection URL |
| `ENV` | No | `development` | `development` / `production` |
| `DEBUG` | No | `true` | SQL echo and verbose logging |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection URL |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model name |
| `GEMINI_TEMPERATURE` | No | `0.3` | Lower = more factual |
| `GEMINI_MAX_TOKENS` | No | `4096` | Max tokens per response |
| `GEMINI_EMBEDDING_MODEL` | No | `models/text-embedding-004` | Embedding model |
| `MAX_UPLOAD_SIZE_MB` | No | `20` | Maximum file upload size |
| `UPLOAD_DIR` | No | `data/uploads` | Local file storage path |
| `VECTOR_STORE_DIR` | No | `data/vector_stores` | FAISS index storage path |
| `CHUNK_SIZE_WORDS` | No | `600` | RAG chunk size |
| `RAG_TOP_K` | No | `5` | Chunks retrieved per query |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | JWT refresh token lifetime |

---

## 🧪 Running Tests

```bash
# Run all backend tests (222 tests)
make test

# Run with verbose output
source .venv/bin/activate && pytest tests/ -v

# Run specific test file
pytest tests/unit/test_lab_extractor.py -v

# Run integration tests only
pytest tests/integration/ -v

# Frontend tests
make test-frontend
```

---

## 🗄️ Database Migrations

```bash
# Apply all pending migrations (production)
make migrate

# Check current migration status
source .venv/bin/activate && alembic current

# Create a new migration after model changes
make migrate-create NAME="add_report_tags_column"

# Rollback the last migration
make migrate-down

# Upgrade to specific revision
alembic upgrade <revision_id>
```

---

## ➕ Adding New Lab Tests

To support a new laboratory test, add an entry to any YAML file in `config/reference_ranges/`:

```yaml
# Example: config/reference_ranges/biochemistry.yaml

vitamin_d:
  display_name: "Vitamin D"
  aliases: ["vitamin d", "25-oh vitamin d", "25-hydroxyvitamin d", "vit d"]
  unit: "ng/mL"
  category: "Vitamins"
  description: >
    Vitamin D supports bone health, immune function, and muscle strength.
    Deficiency is common worldwide.
  ranges:
    deficient:
      min: 0.0
      max: 20.0
    default:
      min: 20.0
      max: 50.0
  critical:
    low: 10.0
    high: 150.0
```

**No Python code changes required.** The `ReferenceEngine` loads all `.yaml` files from that directory automatically on startup.

---

## 🚢 Production Deployment

See [`docs/production_checklist.md`](docs/production_checklist.md) for the complete 40-item checklist.

### Key steps

```bash
# 1. Set production environment variables
export ENV=production
export DEBUG=false
export SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/sehat_saathi
export GEMINI_API_KEY=your_production_key

# 2. Run database migrations (never use init_db() in production)
alembic upgrade head

# 3. Start with multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 4. Or use Docker Compose
docker compose -f docker-compose.yml up -d
```

### Security checklist highlights

- [ ] Change `SECRET_KEY` to a cryptographically strong random value
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure HTTPS via Nginx + Let's Encrypt
- [ ] Restrict `ALLOWED_ORIGINS` to your domain only
- [ ] Set `DEBUG=false` and `ENV=production`
- [ ] Enable Redis authentication
- [ ] Set up automated database backups

---

## 🔮 Future Scope

| Feature | Description |
|---|---|
| Voice interface | Speech-to-text for questions, text-to-speech for answers |
| Multi-language support | Hindi, Tamil, Bengali, and other Indian languages |
| Report comparison | Track lab value trends across multiple reports |
| Doctor dashboard | Separate role for healthcare professionals |
| EHR integration | HL7 FHIR standard support |
| Wearable data | Integrate with fitness trackers and smartwatches |
| Mobile app | React Native companion app |
| Advanced RAG | Cross-encoder reranking, hybrid search |
| Offline mode | On-device inference for sensitive data |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ for better healthcare accessibility

**[SehatSaathi-AI](https://github.com/ayushpratap27/SehatSaathi-AI)** — *Your AI-powered health companion*

</div>

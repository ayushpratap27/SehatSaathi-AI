# SehatSaathi-AI

> **AI-powered Medical Report Understanding System** — helping patients understand their health reports in plain language.

⚠️ **Medical Disclaimer:** SehatSaathi-AI is for informational purposes only. It does not provide medical diagnoses, prescriptions, or treatment advice. Always consult a qualified healthcare professional.

---

## Project Overview

SehatSaathi-AI is a production-ready, full-stack AI platform that transforms complex medical reports into clear, patient-friendly information. It supports PDF/image upload, OCR, medical NER, clinical analysis, AI summaries powered by Google Gemini 2.5 Flash, and a RAG-based chat interface.

---

## Architecture

```
Upload (PDF/Image)
    ↓
OCR (PaddleOCR / PyMuPDF)
    ↓
Medical Extraction (spaCy / SciSpaCy / Regex)
    ↓
Clinical Rule Engine (FAISS reference ranges)
    ↓
Gemini AI (Summary / Explanation / RAG Chat)
    ↓
React Frontend (Dashboard / Report Viewer / Chat)
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Backend | Python 3.12, FastAPI, Uvicorn |
| AI / NLP | Google Gemini 2.5 Flash, SciSpaCy, PaddleOCR, PyMuPDF |
| Vector DB | FAISS (IndexFlatIP cosine similarity) |
| Database | PostgreSQL (production), SQLite (development) |
| Cache | Redis |
| Auth | JWT (PyJWT + bcrypt) |
| ORM | SQLAlchemy 2.x async + Alembic |
| Proxy | Nginx |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Project Structure

```
SehatSaathi-AI/
├── frontend/                  # React 19 TypeScript SPA
│   ├── src/
│   │   ├── pages/             # Login, Dashboard, Upload, Report, Chat, Profile
│   │   ├── components/        # UI, Layout, Auth components
│   │   ├── services/          # API service layer (axios)
│   │   ├── context/           # Auth context
│   │   └── types/             # TypeScript type definitions
│   └── Dockerfile
├── app/                       # FastAPI application
│   ├── api/v1/endpoints/      # REST API endpoints
│   ├── auth/                  # JWT handler + dependencies
│   ├── database/              # SQLAlchemy async session
│   ├── models/                # ORM models (User, Report, Chat, etc.)
│   ├── repositories/          # Database access layer
│   ├── schemas/               # Pydantic schemas
│   └── services/              # Business logic
├── ai/
│   ├── gemini/                # Gemini AI services (summary, chat, explain)
│   ├── rag/                   # RAG pipeline (chunker, FAISS, retriever)
│   ├── ner/                   # Medical NER extractors
│   └── analysis/              # Clinical rule engine
├── config/reference_ranges/   # YAML reference range configs
├── alembic/                   # Database migrations
├── tests/                     # pytest tests (unit + integration)
├── nginx/                     # Nginx reverse proxy config
├── docs/                      # Production checklist
├── Makefile
├── docker-compose.yml
└── .github/workflows/ci.yml   # GitHub Actions CI
```

---

## Completed Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Foundation & project scaffolding | ✅ Complete |
| 2 | Document ingestion pipeline (PDF + OCR) | ✅ Complete |
| 3 | Medical information extraction (NER + structured JSON) | ✅ Complete |
| 4 | Medical Analysis Engine (reference ranges + insights) | ✅ Complete |
| 5 | Gemini AI layer (summary, explanation, chat) | ✅ Complete |
| 6 | RAG pipeline (FAISS + Gemini embeddings) | ✅ Complete |
| 7 | Authentication, database, user accounts, dashboard | ✅ Complete |
| 8 | React frontend, Docker, Redis, CI/CD, production-ready | ✅ Complete |

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.12+
- Node.js 22+
- Git

### 1. Clone and setup

```bash
git clone https://github.com/ayushpratap27/SehatSaathi-AI.git
cd SehatSaathi-AI
make env       # copy .env.example → .env
make install   # create venv + install Python deps
make install-frontend
```

### 2. Add your Gemini API key

```bash
# Edit .env and set:
GEMINI_API_KEY=your_key_here
# Get a free API key at: https://aistudio.google.com/apikey
```

### 3. Start the backend

```bash
source .venv/bin/activate
uvicorn main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 4. Start the frontend

```bash
cd frontend && npm run dev
# Frontend: http://localhost:3000
```

---

## Docker Setup (Recommended)

```bash
cp .env.example .env
# Add GEMINI_API_KEY to .env

docker compose up --build
```

Services:
| Service | URL |
|---|---|
| Frontend (via Nginx) | http://localhost:80 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Liveness probe |
| GET | `/api/v1/ready` | No | Readiness probe |
| POST | `/api/v1/auth/register` | No | Register account |
| POST | `/api/v1/auth/login` | No | Login → tokens |
| GET | `/api/v1/auth/me` | Yes | Current user |
| POST | `/api/v1/reports/upload` | Yes | Upload report to DB |
| GET | `/api/v1/reports` | Yes | List user's reports |
| GET | `/api/v1/dashboard` | Yes | Dashboard stats |
| POST | `/api/v1/report/extract` | No | Extract text (PDF/image) |
| POST | `/api/v1/report/parse` | No | Structured JSON from text |
| POST | `/api/v1/analysis/analyze` | No | Clinical analysis |
| POST | `/api/v1/ai/summary` | No | AI executive summary |
| POST | `/api/v1/ai/chat` | No | Basic AI Q&A |
| POST | `/api/v1/rag/index` | No | Index document for RAG |
| POST | `/api/v1/rag/chat` | No | RAG grounded Q&A |

---

## Running Tests

```bash
# Backend
make test

# Frontend
make test-frontend

# With CI
make test-ci
```

---

## Database Migrations

```bash
# Apply all migrations
make migrate

# Create a new migration
make migrate-create NAME="add_new_column"

# Rollback last migration
make migrate-down
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `SECRET_KEY` | Yes | JWT signing key (min 32 chars) |
| `DATABASE_URL` | Yes | PostgreSQL or SQLite URL |
| `REDIS_URL` | No | Redis connection URL |
| `GEMINI_MODEL` | No | Default: `gemini-2.5-flash` |
| `ENV` | No | `development` / `production` |

---

## Adding New Lab Tests

Edit any YAML file in `config/reference_ranges/`:

```yaml
new_test:
  display_name: "New Test"
  aliases: [new test, nt]
  unit: "units"
  category: "Category"
  description: "What this test measures."
  ranges:
    default:
      min: 10.0
      max: 50.0
  critical:
    low: 5.0
    high: 100.0
```

No Python code changes required.

---

## Production Deployment

See `docs/production_checklist.md` for a complete pre-deployment checklist.

Key points:
- Set `ENV=production` and `DEBUG=false`
- Use PostgreSQL, not SQLite
- Change all default secrets
- Run `alembic upgrade head` instead of `init_db()`
- Configure HTTPS via Nginx + Let's Encrypt

---

## License

MIT — see [LICENSE](LICENSE) for details.

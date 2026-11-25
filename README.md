# ScruCheckAI

Automated Institutional Question Paper Scrutiny and Hybrid RAG Platform built for Anna University examination patterns (`CAT-1`, `CAT-2`, `CAT-3`, and `University`).

## Live Deployment

- **Frontend (Cloudflare Pages):** https://scru-check-ai.pages.dev/
- **Backend API (Hugging Face Spaces):** https://hero1224-scrucheck-api.hf.space
- **Database (Neon PostgreSQL 16 + pgvector):** Cloud-hosted vector store for syllabus chunk ingestion and semantic retrieval.

---

## Core Scrutiny Capabilities

ScruCheckAI evaluates uploaded `.pdf` and `.docx` question papers (and optional syllabus documents) across 8 structured criteria:

1. **Overview & Unified Punchlist** — Overall scrutiny summary, pass/fail indicators, `Show Flagged Only` filter, and downloadable PDF audit reports.
2. **Format Compliance** — Validates question counts, part structure, and maximum marks against `CAT-1`, `CAT-2`, `CAT-3`, and `University` templates.
3. **Mandatory Exam Details** — Checks 8 institutional header fields (subject code, course title, regulation year, semester, etc.) with `Auto`, `2023`, and `2021` regulation enforcement.
4. **Hybrid RAG Syllabus Alignment** — Ingests syllabus files, generates embeddings with `all-MiniLM-L6-v2` (384-dim), stores/retrieves chunks via `pgvector` (or local simple vector store), and maps each question to syllabus units/topics.
5. **Mark Distribution & Arithmetic** — Verifies part totals, question marks, and subdivision arithmetic consistency.
6. **Bloom's Taxonomy (K1–K6)** — Classifies cognitive levels and checks `OR`-choice parity across paired questions.
7. **Grammar & Clarity Review** — Flags grammatical, spelling, and phrasing issues with technical whitelist awareness and suggested revisions.
8. **Repetition Risk** — Detects near-duplicate or overlapping questions across the question paper.
9. **PDF Report Export** — Generates structured scrutiny reports using ReportLab (`/api/v1/reports/download-pdf`).

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| **Frontend** | React 19, TypeScript, Vite 8, Tailwind CSS 4, TanStack React Query, Recharts, Lucide React, Radix UI |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, Alembic |
| **Database / Vector Store** | PostgreSQL 16 + `pgvector` (`asyncpg` / `psycopg`), with local `simple` fallback |
| **Embeddings & Document Parsing** | `sentence-transformers` (`all-MiniLM-L6-v2`), `llama-index-core`, PyMuPDF (`pymupdf`), `python-docx`, `pytesseract` |
| **LLM Providers** | Groq / Google Gemini (with automatic fallback and local heuristic fallback) |
| **Reporting** | ReportLab (`reportlab>=5.1.0`) |
| **Deployment** | Cloudflare Pages (Frontend), Hugging Face Spaces Docker + Gradio passthrough (Backend), Neon (Database) |

---

## Repository Structure

```text
Scru-Check-AI/
├── backend/
│   ├── app/
│   │   ├── core/            # Settings (config.py) and database/vector configuration
│   │   ├── services/        # Scrutiny, Hybrid RAG, Bloom's, Grammar, Repetition, and PDF services
│   │   └── main.py          # FastAPI application and /api/v1/* endpoints
│   ├── patterns/            # Question paper pattern definitions (CAT-1, CAT-2, CAT-3, University)
│   ├── Dockerfile           # Production container for Hugging Face Spaces
│   ├── packages.txt         # System packages for container builds
│   ├── pyproject.toml       # Python dependencies (uv / pip)
│   ├── requirements.txt     # Exported requirements for Docker/Spaces
│   └── server.py            # Gradio + FastAPI passthrough entrypoint (port 7860)
├── frontend/
│   ├── src/
│   │   └── App.tsx          # Single-page scrutiny dashboard, uploaders, 8-criteria nav, PDF export
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml       # Optional local PostgreSQL + pgvector service
├── neon.ts                  # Neon database helper/configuration
├── SECURITY.md              # Security guidelines and secret handling
└── README.md
```

---

## Local Development

### Prerequisites

- **Python 3.12+** (with `uv` or `venv`)
- **Node.js 20+** and `npm`
- **PostgreSQL 16 with `pgvector`** (Neon cloud `DATABASE_URL` or local Docker container)

### 1. Environment Configuration

Configure `backend/.env` (or `.env.local` at the repository root) without committing secrets:

```env
ENVIRONMENT="development"
ENABLE_API_DOCS="true"
VECTOR_STORE_BACKEND="pgvector"
POSTGRES_URL="postgresql+asyncpg://<user>:<password>@<host>/<db>"
LLM_PROVIDER="groq"
GROQ_API_KEY="your_groq_api_key"
FALLBACK_LLM_PROVIDER="gemini"
GEMINI_API_KEY="your_gemini_api_key"
BACKEND_CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

For the frontend (`frontend/.env.local`):

```env
VITE_API_URL="http://127.0.0.1:8000/api/v1"
```

### 2. Optional Local Database (Docker)

```powershell
docker compose up -d postgres
```

### 3. Start the Backend

```powershell
cd C:\Users\vigne\Desktop\Scru-Check-AI\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

> **Note (Windows `uv`):** If `.\.venv\Scripts\uvicorn` fails with `uv trampoline failed to canonicalize script path` after moving the project folder, invoke Uvicorn via `.\.venv\Scripts\python.exe -m uvicorn ...` or recreate the virtual environment (`Remove-Item .venv -Recurse -Force; uv sync`).

Backend health check: `http://127.0.0.1:8000/healthz`

### 4. Start the Frontend

```powershell
cd C:\Users\vigne\Desktop\Scru-Check-AI\frontend
npm install
npm run dev
```

Frontend local URL: `http://localhost:5173`

### 5. Production Frontend Build

```powershell
cd C:\Users\vigne\Desktop\Scru-Check-AI\frontend
npm run build
```

---

## Key API Endpoints

- `GET /healthz` — Service and vector/LLM readiness check
- `GET /api/v1/scrutiny/patterns` — Supported question paper patterns
- `POST /api/v1/scrutiny/check-format` — Format compliance check
- `POST /api/v1/scrutiny/extract-syllabus` — Syllabus text extraction
- `POST /api/v1/scrutiny/check-regulation` — Mandatory exam details & regulation validation
- `POST /api/v1/syllabus/ingest` — Chunk and embed syllabus into vector store
- `POST /api/v1/syllabus/retrieve` — Semantic retrieval from ingested syllabus
- `POST /api/v1/syllabus/map-questions` — Map questions against syllabus units/topics
- `POST /api/v1/scrutiny/check-mark-distribution` — Mark totals and subdivision arithmetic
- `POST /api/v1/scrutiny/check-blooms-taxonomy` — Bloom's K1–K6 classification & OR-choice parity
- `POST /api/v1/scrutiny/check-grammar` — Grammar and clarity analysis
- `POST /api/v1/scrutiny/check-repetition-risk` — Cross-question repetition detection
- `POST /api/v1/reports/download-pdf` — Generate and download PDF scrutiny report

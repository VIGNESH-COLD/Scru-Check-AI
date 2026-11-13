# Project Setup & Environment

A clean, production-grade full-stack boilerplate initialized with all requested technologies.

---

## 🛠️ Verified Technology Stack

| Layer | Technologies & Tools | Status |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, npm | Verified & Built |
| **UI & Styling** | Tailwind CSS 4, shadcn/ui utilities, Lucide React | Verified |
| **Charts** | Recharts | Verified |
| **API State** | TanStack Query (`@tanstack/react-query`) | Configured |
| **Frontend Testing** | Vitest, React Testing Library, `@testing-library/jest-dom` | 100% Pass |
| **Backend Core** | Python 3.12 (managed via `uv`), FastAPI, Pydantic (v2) | 100% Import Pass |
| **Database & Vector** | PostgreSQL 16, pgvector, SQLAlchemy 2 (asyncpg + psycopg), Alembic | Configured |
| **Document Parsers** | PyMuPDF (`pymupdf` / `fitz`), `python-docx` | Verified |
| **OCR** | Tesseract / `pytesseract` | Installed |
| **Embeddings & RAG** | Sentence Transformers (`all-MiniLM-L6-v2`), LlamaIndex Core & Postgres | Verified |
| **LLM Integrations** | `httpx` (for APInex API), `ollama` (for local models) | Verified |
| **Report Generation** | `python-docx`, Matplotlib, Pillow | Verified |
| **Security & Auth** | `pyjwt[crypto]`, `argon2-cffi` | Verified |
| **Backend Testing** | `pytest`, `pytest-asyncio` | 100% Pass |
| **Code Quality** | Ruff (v0.17+), TypeScript compiler | 100% Clean |

---

## 📁 Repository Structure

```text
final/
├── backend/
│   ├── alembic/                # Alembic migration environment
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py       # Pydantic Settings (DB, JWT, Vector settings)
│   │   │   └── database.py     # Async SQLAlchemy 2 engine & Base model
│   │   └── main.py             # Minimal FastAPI starter app with CORS
│   ├── tests/
│   │   ├── conftest.py         # Async test client fixture
│   │   └── test_main.py        # Health & root test
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml          # uv dependency manifest
│   └── uv.lock
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── ui/             # shadcn reusable components
│   │   │       ├── badge.tsx
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── input.tsx
│   │   │       └── tabs.tsx
│   │   ├── lib/
│   │   │   ├── queryClient.ts  # TanStack Query client
│   │   │   └── utils.ts        # shadcn cn() helper
│   │   ├── test/
│   │   │   └── setup.ts        # Vitest jest-dom setup
│   │   ├── App.tsx             # Clean starter component
│   │   ├── index.css           # Tailwind CSS 4 theme
│   │   └── main.tsx            # React 19 root with QueryClientProvider
│   ├── tests/
│   │   └── App.test.tsx        # Vitest starter test
│   ├── .env.example
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── docker-compose.yml           # PostgreSQL 16 with pgvector & Ollama
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Commands

### 1. Start Database & Local Ollama (Docker)
```bash
docker compose up -d
```

### 2. Backend (FastAPI + Python 3.12)
```bash
cd backend

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest

# Check & format code quality with Ruff
uv run ruff check .
uv run ruff format .
```

### 3. Frontend (React 19 + Vite + Tailwind 4)
```bash
cd frontend

# Run development server
npm run dev

# Run Vitest test suite
npm test

# Build for production
npm run build
```

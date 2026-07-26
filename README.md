# ScruCheck AI

> **AI-Powered Question Paper Scrutiny System for Higher Education**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-RAG-FF6B35.svg)](https://mistral.ai)

---

## Overview

ScruCheck AI automatically analyzes question papers against **10 scrutiny criteria**, providing AI-powered recommendations for format compliance, syllabus alignment, Bloom's taxonomy distribution, and more.

### Key Features

| Feature | Description |
|---------|-------------|
| **10 Criteria Analysis** | Format, regulation, syllabus, Bloom's, marks, grammar, diagrams, aids, repetition, figures |
| **RAG System** | Mistral AI + MiniLM embeddings for intelligent syllabus matching |
| **Visualizations** | Bloom's taxonomy chart + Syllabus coverage heatmap |
| **Report Generation** | Downloadable DOCX with embedded charts |
| **RBAC** | 5 roles (Faculty, HOD, COE, Auditor, External) with 17 permissions |
| **External Portal** | Time-limited access tokens for external examiners |
| **Audit Logging** | Complete activity trail for compliance |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Mistral AI API key

### Backend Setup

```bash
cd backend
python -m venv venv
pip install -r requirements.txt

# Create .env file
echo MISTRAL_API_KEY=your_key > .env
echo SECRET_KEY=your_jwt_secret >> .env

# Run server
 .\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Demo Accounts

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `admin` | `admin123` | COE | Full access (16 permissions) |
| `hod_demo` | `hod123` | HOD | Department oversight (11 permissions) |
| `faculty_demo` | `faculty123` | Faculty | Upload & view own (5 permissions) |
| `auditor_demo` | `auditor123` | Auditor | Read-only compliance view (5 permissions) |
| `external_demo` | `external123` | External | Token-scoped read-only (2 permissions) |

---

## 10 Scrutiny Criteria

The system evaluates uploaded papers against the following academic and compliance checks:

| # | Criterion | Level | Blocks Approval? | Description |
|---|-----------|-------|------------------|-------------|
| 1 | Format Compliance | **STRICT** | Yes | Verifies that the paper follows the required structure and layout. |
| 2 | Regulation Check | **STRICT** | Yes | Ensures the paper meets institutional or university regulations. |
| 3 | Syllabus Alignment | ENFORCED | Conditional | Checks whether the questions align with the prescribed syllabus. |
| 4 | Bloom's Taxonomy | ADVISORY | No | Reviews whether the question distribution reflects appropriate cognitive levels. |
| 5 | Mark Distribution | **STRICT** | Yes | Confirms marks are allocated consistently and correctly. |
| 6 | Grammar & Clarity | ADVISORY | No | Identifies unclear wording or grammatical issues. |
| 7 | Diagrams/Symbols | ADVISORY | No | Checks whether diagrams and symbols are used appropriately. |
| 8 | Permitted Aids | ENFORCED | Conditional | Verifies that only allowed aids or resources are referenced. |
| 9 | Repetition Check | ADVISORY | No | Detects repeated questions or duplicated concepts. |
| 10 | Figure Naming | ADVISORY | No | Ensures figures, labels, and naming conventions are consistent. |

---

## Project Structure

```
Scru-Check-AI/
├── backend/
│   ├── auth/
│   ├── middleware/
│   ├── models/
│   ├── patterns/
│   ├── rag/
│   ├── services/
│   │   └── analyzers/
│   ├── samples/
│   ├── temp_images/
│   ├── training_data/
│   ├── audit_log.jsonl
│   ├── main.py
│   ├── requirements.txt
│   └── test_format_validation.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── tests/
│   └── java/
├── EVALUATION_CRITERIA.md
└── README.md

---

## API Endpoints

### Analysis
- `POST /api/analyze` - Analyze question paper
- `GET /api/download/{paper_id}` - Download report
- `GET /api/patterns` - Get exam patterns

### Authentication
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Current user
- `GET /api/auth/users` - List users (admin)

### External Access
- `POST /api/external/generate` - Generate access link
- `GET /api/external/verify/{token}` - Verify token
- `GET /api/external/view/{token}` - View papers

---

## Environment Variables

Create `.env` in `backend/`:

```env
MISTRAL_API_KEY=your_mistral_api_key
SECRET_KEY=your_jwt_secret_key
DATABASE_URL=sqlite:///./scrucheck.db
```
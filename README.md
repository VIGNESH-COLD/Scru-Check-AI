# ScruCheck AI

> **AI-Powered Question Paper Scrutiny System for Higher Education**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-RAG-FF6B35.svg)](https://mistral.ai)

---

## 🎯 Overview

ScruCheck AI automatically analyzes question papers against **10 scrutiny criteria**, providing AI-powered recommendations for format compliance, syllabus alignment, Bloom's taxonomy distribution, and more.

### Key Features

| Feature | Description |
|---------|-------------|
| 📊 **10 Criteria Analysis** | Format, regulation, syllabus, Bloom's, marks, grammar, diagrams, aids, repetition, figures |
| 🤖 **RAG System** | Mistral AI + MiniLM embeddings for intelligent syllabus matching |
| 📈 **Visualizations** | Bloom's taxonomy chart + Syllabus coverage heatmap |
| 📄 **Report Generation** | Downloadable DOCX with embedded charts |
| 🔐 **RBAC** | 5 roles (Faculty, HOD, COE, Auditor, External) with 17 permissions |
| 🔗 **External Portal** | Time-limited access tokens for external examiners |
| 📝 **Audit Logging** | Complete activity trail for compliance |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Mistral AI API key

### Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Create .env file
echo MISTRAL_API_KEY=your_key > .env
echo SECRET_KEY=your_jwt_secret >> .env

# Run server
uvicorn main:app --host 127.0.0.1 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 👥 Demo Accounts

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `admin` | `admin123` | COE | Full access, manage users |
| `hod_demo` | `hod123` | HOD | Department access, external links |
| `faculty_demo` | `faculty123` | Faculty | Upload, view own papers |

---

## 📋 10 Scrutiny Criteria

| # | Criterion | Level | Blocks Approval? |
|---|-----------|-------|------------------|
| 1 | Format Compliance | **STRICT** | ✅ Yes |
| 2 | Regulation Check | **STRICT** | ✅ Yes |
| 3 | Syllabus Alignment | ENFORCED | ⚠️ Conditional |
| 4 | Bloom's Taxonomy | ADVISORY | ❌ No |
| 5 | Mark Distribution | **STRICT** | ✅ Yes |
| 6 | Grammar & Clarity | ADVISORY | ❌ No |
| 7 | Diagrams/Symbols | ADVISORY | ❌ No |
| 8 | Permitted Aids | ENFORCED | ⚠️ Conditional |
| 9 | Repetition Check | ADVISORY | ❌ No |
| 10 | Figure Naming | ADVISORY | ❌ No |

---

## 📁 Project Structure

```
scrucheck-ai/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── auth/                # JWT + RBAC + External tokens
│   ├── services/            # Scrutiny engine + analyzers
│   ├── rag/                 # Embeddings + LLM client
│   ├── models/              # SQLAlchemy models
│   └── middleware/          # Audit logging
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── context/         # AuthContext
    │   └── components/      # Login, AdminPanel, etc.
    └── vite.config.js
```

---

## 🔌 API Endpoints

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

## ⚙️ Environment Variables

Create `.env` in `backend/`:

```env
MISTRAL_API_KEY=your_mistral_api_key
SECRET_KEY=your_jwt_secret_key
DATABASE_URL=sqlite:///./scrucheck.db
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

**Built with ❤️ for Higher Education Quality Assurance**

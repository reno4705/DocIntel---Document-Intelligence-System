# DocIntel - Document Intelligence System

## AI-Powered Forensic Analysis of Corporate Document Archives

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![License](https://img.shields.io/badge/License-Research-yellow.svg)](LICENSE)

A production-ready document intelligence system that automates forensic analysis of corporate document archives. Uses OCR, NLP, and **Groq AI (LLaMA 3.3 70B)** to extract accountability trails, identify key stakeholders, and answer the critical question: **"Who knew what, and when did they know it?"**

![DocIntel Dashboard](docs/screenshot.png)

---

## ✨ Key Features

### 🔍 Document Processing
- **Multi-format Support:** PDF, PNG, JPG, TIFF, BMP
- **Advanced OCR:** Tesseract with image preprocessing
- **Batch Upload:** Process multiple documents simultaneously

### 🤖 AI-Powered Analysis (Groq)
- **Document Classification:** Auto-detect document types
- **Stakeholder Extraction:** Identify people, roles, and actions
- **Evidence Extraction:** Direct quotes with significance
- **Red Flag Detection:** Highlight concerning patterns
- **Risk Scoring:** Rate documents 1-10 for importance

### 📊 Forensic Intelligence
- **Accountability Trail:** Track who knew what and when
- **Relationship Mapping:** Actor connections and hierarchies
- **Causal Chain Analysis:** Connect causes to effects
- **Knowledge Timeline:** Attribute knowledge to specific dates
- **Pattern Detection:** Identify recurring themes

### 💬 Interactive Features
- **Document Q&A:** Ask questions about your document corpus
- **Search & Filter:** Find documents by name instantly
- **AI Chat:** Natural language queries with citations

---

## 🛠 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + Vite | Modern SPA framework |
| **Styling** | TailwindCSS | Utility-first CSS |
| **Icons** | Lucide React | Beautiful icons |
| **Charts** | Recharts | Data visualization |
| **Backend** | FastAPI (Python 3.11) | High-performance API |
| **OCR** | Tesseract 5.x | Text extraction |
| **NLP** | spaCy | Entity recognition |
| **AI** | Groq (LLaMA 3.3 70B) | Intelligent analysis |
| **Storage** | JSON | Document store |

---

## 📁 Project Structure

```
/IDUS_Project
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Config, logging
│   │   ├── services/     # Business logic
│   │   │   ├── groq_service.py      # AI analysis
│   │   │   ├── ocr_service.py       # Text extraction
│   │   │   └── nlp_service.py       # NLP processing
│   │   └── schemas/      # Data models
│   ├── data/             # Document store
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # App pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Upload.jsx
│   │   │   ├── History.jsx
│   │   │   ├── ResearchDemo.jsx
│   │   │   ├── Chat.jsx
│   │   │   └── DocumentDetail.jsx
│   │   └── services/     # API client
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── Documentation.md      # Full research documentation
└── DOCKER.md            # Docker deployment guide
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Tesseract OCR installed
- Groq API key (free at https://console.groq.com)

### 1. Clone & Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create .env file with your Groq API key
echo GROQ_API_KEY=your_groq_api_key_here > .env

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### 3. Access Application

- **Application:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🐳 Docker Deployment

```bash
# Set your Groq API key
echo "GROQ_API_KEY=your_key" > backend/.env

# Build and run
docker-compose up --build -d

# Access at http://localhost (port 80)
```

See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

---

## 📡 API Endpoints

### Document Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload document for processing |
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}` | Get document details |
| DELETE | `/api/documents/{id}` | Delete document |

### AI Analysis (Groq)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai/groq/status` | Check AI availability |
| POST | `/api/ai/analyze-document/{id}` | Deep analysis of single document |
| GET | `/api/ai/accountability-trail` | Build cross-document accountability trail |
| POST | `/api/ai/chat` | Chat with documents |
| POST | `/api/ai/ask` | Ask question about corpus |

### Intelligence

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/intelligence/corpus` | Corpus-wide statistics |
| GET | `/api/intelligence/stakeholders` | Stakeholder network |
| GET | `/api/intelligence/timeline` | Event timeline |

---

## 🖥 Application Pages

| Page | URL | Description |
|------|-----|-------------|
| **Dashboard** | `/` | Overview statistics |
| **Upload** | `/upload` | Document upload interface |
| **Documents** | `/history` | Document list with search |
| **Research** | `/research` | AI-powered forensic analysis |
| **Chat** | `/chat` | Document Q&A interface |
| **Document Detail** | `/document/:id` | Single document analysis |

---

## 🔬 Research Features

### AI Analysis Output

The system extracts:

- **Executive Summary:** AI-generated overview
- **Red Flags:** Critical/high/medium severity issues
- **Key Actors:** With accountability levels and actions
- **Relationships:** Who reports to whom, communication chains
- **Evidence:** Direct quotes with confidence levels
- **Timeline:** Events with significance and quotes
- **Causal Chain:** Cause → Effect connections
- **Knowledge Timeline:** Who knew what, when
- **Patterns:** Recurring themes with instances
- **Recommendations:** Follow-up investigation actions

### Sample Groq Analysis Output

```json
{
  "executive_summary": "Documents reveal systematic...",
  "red_flags": [
    {
      "issue": "Evidence of prior knowledge",
      "severity": "high",
      "evidence": "Direct quote from document...",
      "actors_implicated": ["John Doe", "Jane Smith"]
    }
  ],
  "key_actors": [
    {
      "name": "John Doe",
      "role": "Research Director",
      "accountability_level": "high",
      "key_actions": ["Approved study", "Signed authorization"],
      "evidence_strength": "strong"
    }
  ],
  "timeline": [...],
  "causal_chain": [...],
  "recommendations": [...]
}
```

---

## 📊 Dataset

The system is tested with the **Truth Tobacco Industry Documents** archive (UCSF):
- 14+ million documents available
- 159 documents in demo corpus
- Document types: Memos, Reports, Test Results, Specifications

Compatible with any corporate document archive.

---

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Primary Groq API key for AI features | Yes |
| `GROQ_API_KEY_SECONDARY` | Fallback API key (auto-switches on rate limit) | No |
| `DEBUG` | Enable debug mode | No |

**Note:** The system supports automatic API key fallback. If the primary key hits rate limit, it automatically switches to the secondary key.

---

## 📚 Documentation

- **[Documentation.md](Documentation.md)** - Complete research documentation
- **[DOCKER.md](DOCKER.md)** - Docker deployment guide
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is for research and educational purposes.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com) for fast AI inference
- [UCSF](https://www.industrydocuments.ucsf.edu) for document archives
- [Tesseract](https://github.com/tesseract-ocr/tesseract) for OCR
- [spaCy](https://spacy.io) for NLP

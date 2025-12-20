A complete AI-powered educational system that transforms long educational texts into interactive learning experiences with concept hierarchies, adaptive explanations, and difficulty-validated quizzes.


## Overview

Upload any educational text (textbook chapters, articles, lecture notes) and the system will:

1. **Extract key concepts** using AI (Agent 1)
2. **Build a dependency-based hierarchy** (foundational → advanced)
3. **Generate adaptive explanations** with tone selection (Agent 2, Mode A)
4. **Create validated quizzes** with Bloom's taxonomy alignment (Agent 2, Mode B)


Traditional learning materials are static. This system makes them interactive:
- Automatic concept extraction (no manual tagging)
- Dependency-aware learning paths
- Personalized explanation styles
- Validated, difficulty-appropriate assessments


### Agent 2 (Adaptive Tutor)
- **NEVER sees raw text** (prevents hallucination)
- Works from concept metadata only
- Two modes:
  - **Mode A**: Explanations (4 tones)
  - **Mode B**: Quizzes (3 difficulties)

## Key Features

### Intelligent Concept Extraction
- Adaptive (no fixed concept count)
- Dependency-based hierarchy
- Importance scoring
- Prerequisite detection

### Adaptive Explanations
Four tone styles:
- **Simple**: ELI5, minimal jargon
- **Exam-Oriented**: Formal, structured
- **Detailed**: Comprehensive, technical
- **Intuitive**: Analogies, real-world examples

### Validated Quizzes
- Exactly 10 questions per quiz
- Bloom's taxonomy alignment:
  - Remember → Understand → Apply → Analyze → Evaluate → Create
- Three difficulty levels:
  - **Easy**: Remember & Understand (1-4)
  - **Medium**: Apply & Analyze (4-7)
  - **Hard**: Evaluate & Create (7-10)
- Autonomous validation & retry

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **LLM**: OpenAI GPT-4o-mini
- **Orchestration**: LangGraph
- **Vector DB**: ChromaDB (local persistence)
- **Structured DB**: SQLite
- **Validation**: Rule-based (no LLM)

### Frontend
- **Framework**: React 18 + Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Start server
uvicorn main:app --reload
```

Backend runs on: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

Frontend runs on: `http://localhost:3000`

### Verify Setup

1. Open `http://localhost:3000`
2. Click "Upload New Text"
3. Paste educational content (100+ chars)
4. Wait for processing (~30-60 seconds)
5. Explore concepts, generate explanations & quizzes!


## APIs Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/document/create` | Upload educational text |
| GET | `/api/document/{id}` | Get document + concepts |
| GET | `/api/user/{user_id}/documents` | List user's documents |
| DELETE | `/api/document/{id}` | Delete document |
| POST | `/api/explain` | Generate explanation |
| POST | `/api/quiz` | Generate quiz |

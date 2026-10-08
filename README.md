# StudentOS AI

A unified AI student platform built with Streamlit, SQLite, Groq, RAG, and machine learning.

## Features
- Student profile persisted in SQLite
- LifeLog AI: performance analytics and anomaly detection from uploaded CSV
- Study RAG: PDF ingestion and grounded Q&A
- Text to Notes and exam-note generation
- YouTube transcript summarization when captions are available
- AI quiz generation from Study RAG content
- IntelliHire: resume analysis, PDF/DOCX/TXT parsing, resume-JD matching and skill gaps
- Goal Tracker
- AI Study Planner using profile, goals and LifeLog weak topics
- Career Readiness Dashboard
- AI Student Coach
- Downloadable reports

## Run
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# put your Groq key in .env
streamlit run app.py
```

The application intentionally starts without fake student records or sample dashboard values.

# 💚 HamDard - AI Mental Health Companion

AI-powered mental health chatbot for Pakistani students.  
Built with **Gemini LLM** + **RAG** + **Emotion Detection** + **Multilingual** (English, Urdu, Roman Urdu).

## Architecture
```
User → Emotion Detection → RAG Search → Gemini LLM → Empathetic Response
```

## Features
- Gemini 2.5 Flash LLM integration
- RAG Knowledge Base (upload PDFs, TXT, CSV)
- 9 emotions + crisis detection
- English, Urdu, Roman Urdu
- Crisis safety with helplines
- Mood tracking

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your API key to `.streamlit/secrets.toml`:
```
GEMINI_API_KEY = "your-key"
```

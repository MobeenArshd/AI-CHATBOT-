import streamlit as st
import google.generativeai as genai
import json
import os
import hashlib
from collections import Counter

# =============================================
# PAGE CONFIG
# =============================================
st.set_page_config(
    page_title="HamDard - Mental Health Companion",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================
# CUSTOM CSS
# =============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
.stApp { font-family: 'Nunito', sans-serif; }
.hamdard-header { text-align: center; padding: 1.5rem 0 1rem 0; }
.hamdard-header h1 { font-size: 2.5rem; font-weight: 800; color: #2E7D32; margin: 0; }
.hamdard-header p { font-size: 1rem; color: #666; margin: 0.25rem 0 0 0; }
.emotion-badge { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; margin: 4px 0; }
.emotion-sadness { background: #E3F2FD; color: #1565C0; }
.emotion-anxiety { background: #FFF3E0; color: #E65100; }
.emotion-stress { background: #FCE4EC; color: #C62828; }
.emotion-anger { background: #FFEBEE; color: #B71C1C; }
.emotion-loneliness { background: #E8EAF6; color: #283593; }
.emotion-frustration { background: #FFF8E1; color: #F57F17; }
.emotion-hopelessness { background: #F3E5F5; color: #6A1B9A; }
.emotion-confusion { background: #E0F7FA; color: #00695C; }
.emotion-neutral { background: #E8F5E9; color: #2E7D32; }
.emotion-crisis { background: #FFCDD2; color: #B71C1C; font-weight: 800; }
.kb-stat { background: #F1F8E9; border-radius: 10px; padding: 12px 16px; margin: 8px 0; text-align: center; }
.kb-stat h3 { margin: 0; font-size: 1.5rem; color: #2E7D32; }
.kb-stat p { margin: 0; font-size: 0.85rem; color: #555; }
.crisis-banner { background: linear-gradient(135deg, #FFCDD2, #EF9A9A); border-radius: 10px; padding: 16px; margin: 10px 0; text-align: center; border: 1px solid #E57373; }
.crisis-banner h4 { color: #B71C1C; margin: 0 0 8px 0; }
.crisis-banner p { color: #C62828; margin: 2px 0; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)


# =============================================
# EMOTION DETECTION MODULE
# =============================================

EMOTION_KEYWORDS = {
    "sadness": {
        "keywords": ["sad","unhappy","depressed","crying","tears","heartbroken","miserable","hopeless","empty","lonely","alone","lost","hurt","pain","broken","dukhi","udaas","rona","ro raha","ro rahi","dil toota","tanha","akela","akeli","takleef","dard","toot gaya","koi nahi hai","zindagi mushkil","bohat bura","dil nahi lagta"],
        "tone": "gentle, warm, validating"
    },
    "anxiety": {
        "keywords": ["anxious","worried","nervous","panic","scared","fear","overthinking","restless","uneasy","tense","cant sleep","racing thoughts","tension","ghabra","ghabrahat","dar","darr","khauf","pareshan","neend nahi","soch soch ke","kya hoga","fikar","bechaini","dil ghabrata","phat rahi hai"],
        "tone": "calming, reassuring, grounding"
    },
    "stress": {
        "keywords": ["stressed","overwhelmed","pressure","too much","cant handle","burnout","exhausted","tired","workload","deadline","exams","studies","bohat zyada","bardasht nahi","thak gaya","thak gayi","dimagh kharab","sar dard","kaam bohat","imtihan","parhai","handle nahi ho raha","pagal ho jaunga"],
        "tone": "supportive, practical, encouraging"
    },
    "anger": {
        "keywords": ["angry","furious","mad","hate","frustrated","annoyed","irritated","rage","unfair","sick of","fed up","gussa","ghussa","nafrat","tang","bezaar","chir","jal raha","insaaf nahi","tang aa gaya","tang aa gayi","sab se nafrat"],
        "tone": "validating, calm, non-judgmental"
    },
    "loneliness": {
        "keywords": ["lonely","alone","no friends","no one cares","isolated","left out","abandoned","rejected","nobody","invisible","akela","akeli","tanha","koi nahi","kisi ko parwa nahi","sab door","koi dost nahi","koi samajhta nahi","miss kar raha"],
        "tone": "warm, connecting, companionable"
    },
    "frustration": {
        "keywords": ["frustrated","stuck","nothing works","useless","pointless","why me","cant do anything","failing","failure","kuch nahi hota","bekar","fail","nakaam","kya karun","samajh nahi aata","haar gaya","haar gayi","kuch nahi ban sakta"],
        "tone": "encouraging, solution-oriented, empathetic"
    },
    "hopelessness": {
        "keywords": ["hopeless","no point","give up","cant go on","whats the point","nothing matters","no future","no hope","end it","umeed nahi","koi faida nahi","chor do","khatam","matlab nahi","aage kuch nahi","zindagi bekar","sab khatam"],
        "tone": "gentle, hopeful, crisis-aware"
    },
    "confusion": {
        "keywords": ["confused","dont know","unsure","what should i do","no idea","help me","cant decide","mixed feelings","samajh nahi","pata nahi","kya karun","confuse","faisla nahi","madad karo","kuch samajh nahi aa raha"],
        "tone": "clarifying, patient, guiding"
    }
}

CRISIS_KEYWORDS = [
    "suicide","suicidal","kill myself","want to die","end my life","self harm","self-harm",
    "cut myself","cutting","hurt myself","no reason to live","better off dead","overdose",
    "marna chahta","marna chahti","mar jaunga","mar jaungi","khudkushi","zindagi khatam",
    "jeena nahi","maut chahiye","apne aap ko hurt","suicide kar lunga","mar jana chahta",
    "life ka koi matlab nahi","sab khatam kar dunga","mujhe nahi jeena"
]

def detect_emotion(text):
    text_lower = text.lower().strip()
    for kw in CRISIS_KEYWORDS:
        if kw in text_lower:
            return {"emotion": "crisis", "confidence": 1.0, "is_crisis": True, "tone": "immediate care, provide helplines"}
    
    scores = {}
    for emotion, data in EMOTION_KEYWORDS.items():
        score = sum(1 for kw in data["keywords"] if kw in text_lower)
        if score > 0:
            scores[emotion] = score
    
    if not scores:
        return {"emotion": "neutral", "confidence": 0.5, "is_crisis": False, "tone": "friendly, warm"}
    
    best = max(scores, key=scores.get)
    return {"emotion": best, "confidence": min(scores[best]/3, 1.0), "is_crisis": False, "tone": EMOTION_KEYWORDS[best]["tone"]}

def get_mood_summary(emotions):
    meaningful = [e for e in emotions if e != "neutral"]
    if not meaningful:
        return "You seemed calm today. That's perfectly okay!"
    primary = Counter(meaningful).most_common(1)[0][0]
    summaries = {
        "sadness": "You carried some sadness today. Reaching out was brave.",
        "anxiety": "You felt anxious today. Remember to breathe — this will pass.",
        "stress": "You were stressed today. Please rest and be kind to yourself.",
        "anger": "You felt frustrated today. Your feelings are valid.",
        "loneliness": "You felt lonely today. You matter more than you know.",
        "frustration": "You felt frustrated today. Setbacks are temporary.",
        "hopelessness": "You had a tough time today. There is always hope.",
        "confusion": "You felt unsure today. Take it one step at a time.",
        "crisis": "You shared heavy feelings. Please reach out to a helpline."
    }
    return summaries.get(primary, f"You seemed {primary} today. Take care!")


# =============================================
# RAG KNOWLEDGE BASE (Lightweight JSON)
# =============================================

DEFAULT_KNOWLEDGE = [
    "Breathing Exercise - 4-7-8 Technique: Breathe in for 4 seconds, hold for 7, exhale for 8. Repeat 3-4 times. This reduces anxiety. Roman Urdu: 4 second saans lo, 7 second roko, 8 second mein bahar nikalo.",
    "Grounding - 5-4-3-2-1 Method: Notice 5 things you SEE, 4 you TOUCH, 3 you HEAR, 2 you SMELL, 1 you TASTE. Roman Urdu: 5 cheezein dekho, 4 chuo, 3 suno, 2 sungho, 1 taste karo.",
    "Journaling helps process emotions. Prompts: What am I feeling and why? 3 things I'm grateful for? What would I tell a friend? Roman Urdu: Apne khayal likhein, 3 shukr ki cheezein, dost ko kya kehte.",
    "Progressive Muscle Relaxation: Tense muscles for 5 seconds then release. Start toes to face. Roman Urdu: Muscles 5 second tight karein phir chor dein, paon se face tak.",
    "Sleep Tips: Consistent schedule, no screens 30min before bed, cool dark room, no caffeine after 2PM. Roman Urdu: Roz ek waqt soyen, phone band karein, kamra thanda rakhen.",
    "Seek Help if: Sadness over 2 weeks, can't function daily, self-harm thoughts, severe anxiety. Pakistan helplines: Umang 0311-7786264, Rozan 0800-22444, Mental Health 0800-00-009.",
    "Mindfulness: Sit comfortably, close eyes, focus on breath. When mind wanders, return to breath. Start 5 minutes daily. Roman Urdu: Aram se baithen, saans par dhyan den, 5 minute se shuru karein.",
    "Exam Stress: Create study schedule, take breaks, practice relaxation, eat well, talk to someone. Roman Urdu: Schedule banayein, breaks lein, acha khayein, kisi se baat karein."
]

def get_knowledge_base():
    if "knowledge_base" not in st.session_state:
        st.session_state.knowledge_base = list(DEFAULT_KNOWLEDGE)
    return st.session_state.knowledge_base

def add_to_kb(texts):
    kb = get_knowledge_base()
    added = 0
    for text in texts:
        if text.strip() and text.strip() not in kb:
            kb.append(text.strip())
            added += 1
    return added

def search_kb(query, n=3):
    kb = get_knowledge_base()
    if not kb:
        return []
    query_words = set(query.lower().split())
    scored = []
    for doc in kb:
        doc_words = set(doc.lower().split())
        overlap = len(query_words & doc_words)
        if overlap > 0:
            scored.append((overlap, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:n]]

def process_uploaded_file(uploaded_file):
    """Process uploaded file and return list of text chunks."""
    file_type = uploaded_file.name.split(".")[-1].lower()
    texts = []
    
    if file_type == "pdf":
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            full_text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    full_text += t + "\n"
            # Split into chunks
            words = full_text.split()
            for i in range(0, len(words), 100):
                chunk = " ".join(words[i:i+100])
                if chunk.strip():
                    texts.append(chunk)
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
    
    elif file_type == "txt":
        try:
            content = uploaded_file.read().decode("utf-8")
            words = content.split()
            for i in range(0, len(words), 100):
                chunk = " ".join(words[i:i+100])
                if chunk.strip():
                    texts.append(chunk)
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    elif file_type == "csv":
        try:
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            for _, row in df.iterrows():
                parts = [str(v) for v in row.values if str(v) != "nan"]
                if parts:
                    texts.append(" | ".join(parts))
        except Exception:
            # If pandas not available, read as plain text
            try:
                uploaded_file.seek(0)
                content = uploaded_file.read().decode("utf-8")
                for line in content.strip().split("\n")[1:]:  # skip header
                    if line.strip():
                        texts.append(line.strip())
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
    
    return texts


# =============================================
# SYSTEM PROMPT & LLM
# =============================================

SYSTEM_PROMPT = (
    "You are HamDard — a compassionate, culturally-aware AI mental health "
    "companion designed for Pakistani students and young people.\n\n"
    "CORE IDENTITY:\n"
    "- You are NOT a therapist or doctor. You are a supportive digital companion.\n"
    "- You provide emotional support, empathetic listening, and coping suggestions.\n"
    "- You are warm, gentle, non-judgmental, and patient.\n\n"
    "LANGUAGE RULES:\n"
    "- Respond in English, Urdu, or Roman Urdu — match the user's language.\n"
    "- If user writes Roman Urdu, respond in Roman Urdu mixed with English.\n\n"
    "RESPONSE GUIDELINES:\n"
    "1. ALWAYS validate the user's feelings first.\n"
    "2. Ask gentle follow-up questions.\n"
    "3. Use knowledge context naturally without mentioning its source.\n"
    "4. Keep responses concise (3-5 sentences). Don't lecture.\n"
    "5. Vary your openings — don't always start with 'I understand'.\n\n"
    "BOUNDARIES:\n"
    "- Never diagnose conditions or prescribe medication.\n"
    "- Never claim to replace professional therapy.\n"
    "- Redirect medical questions to professionals.\n"
)

CRISIS_ADDITION = (
    "\n\nCRISIS DETECTED:\n"
    "1. Express deep care.\n"
    "2. Say they are NOT alone.\n"
    "3. Give helplines: Umang 0311-7786264, Rozan 0800-22444, Mental Health 0800-00-009.\n"
    "4. Encourage talking to a trusted person.\n"
    "5. Be gentle. No clinical language.\n"
)


# =============================================
# INITIALIZATION
# =============================================

def init():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "emotions" not in st.session_state:
        st.session_state.emotions = []
    if "chat" not in st.session_state:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            st.session_state.chat = model.start_chat(history=[])
        else:
            st.session_state.chat = None
    get_knowledge_base()  # Initialize KB

init()


# =============================================
# SIDEBAR
# =============================================

with st.sidebar:
    st.markdown("## 💚 HamDard")
    st.markdown("AI mental health companion with **Gemini LLM**, **RAG**, and **Emotion Detection**.")
    st.divider()

    st.markdown("### 📚 Knowledge Base")
    kb = get_knowledge_base()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="kb-stat"><h3>{len(kb)}</h3><p>Documents</p></div>', unsafe_allow_html=True)
    with col2:
        default_count = sum(1 for d in kb if d in DEFAULT_KNOWLEDGE)
        custom_count = len(kb) - default_count
        st.markdown(f'<div class="kb-stat"><h3>{custom_count}</h3><p>Uploaded</p></div>', unsafe_allow_html=True)

    st.markdown("### 📤 Upload to Knowledge Base")
    st.caption("PDF, TXT, or CSV files")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "csv"])

    if uploaded_file and st.button("Add to Knowledge Base", type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            texts = process_uploaded_file(uploaded_file)
            if texts:
                added = add_to_kb(texts)
                st.success(f"Added {added} chunks from {uploaded_file.name}")
            else:
                st.error("Could not extract content.")

    st.divider()

    st.markdown("### 🎭 Emotion Tracking")
    if st.session_state.emotions:
        for emo in st.session_state.emotions[-5:]:
            st.markdown(f'<span class="emotion-badge emotion-{emo}">{emo.capitalize()}</span>', unsafe_allow_html=True)
    else:
        st.caption("Emotions appear here as you chat.")

    st.divider()

    st.markdown(
        '<div class="crisis-banner"><h4>Emergency Helplines</h4>'
        '<p><strong>Umang:</strong> 0311-7786264</p>'
        '<p><strong>Rozan:</strong> 0800-22444</p>'
        '<p><strong>Mental Health:</strong> 0800-00-009</p></div>',
        unsafe_allow_html=True
    )

    st.divider()
    if st.button("🔄 New Conversation", use_container_width=True):
        if st.session_state.emotions:
            st.info(get_mood_summary(st.session_state.emotions))
        st.session_state.messages = []
        st.session_state.emotions = []
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)
            st.session_state.chat = model.start_chat(history=[])
        st.rerun()


# =============================================
# MAIN CHAT
# =============================================

st.markdown(
    '<div class="hamdard-header"><h1>💚 HamDard</h1>'
    '<p>Your compassionate AI mental health companion | English • Urdu • Roman Urdu</p></div>',
    unsafe_allow_html=True
)

if not st.session_state.chat:
    st.error("Gemini API key not found. Add GEMINI_API_KEY to Streamlit secrets.")
    st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "user" and "emotion" in msg:
            emo = msg["emotion"]
            st.markdown(f'<span class="emotion-badge emotion-{emo}">Detected: {emo.capitalize()}</span>', unsafe_allow_html=True)

if not st.session_state.messages:
    welcome = (
        "Assalam-o-Alaikum! 💚 Main **HamDard** hoon, aapka digital companion.\n\n"
        "Aap mujhse **English**, **Urdu**, ya **Roman Urdu** mein baat kar sakte hain.\n\n"
        "**Aaj aap kaisa mehsoos kar rahe hain?**"
    )
    with st.chat_message("assistant"):
        st.markdown(welcome)
    st.session_state.messages.append({"role": "assistant", "content": welcome})

if user_input := st.chat_input("Apni baat yahan likhein... | Type here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Detect emotion
    emo_result = detect_emotion(user_input)
    st.session_state.emotions.append(emo_result["emotion"])
    st.session_state.messages[-1]["emotion"] = emo_result["emotion"]

    # Build enhanced prompt with RAG + emotion
    enhanced = user_input
    rag_docs = search_kb(user_input)
    if rag_docs:
        enhanced += "\n\nRELEVANT KNOWLEDGE (use naturally, don't mention source):\n"
        for doc in rag_docs:
            enhanced += f"- {doc}\n"
    enhanced += f"\n\nDETECTED EMOTION: {emo_result['emotion']} | TONE: {emo_result['tone']}"
    if emo_result["is_crisis"]:
        enhanced += CRISIS_ADDITION

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Soch raha hoon..."):
            try:
                response = st.session_state.chat.send_message(enhanced)
                reply = response.text
            except Exception as e:
                reply = (
                    "Sorry, I'm having trouble right now. If you need help:\n"
                    "- Umang: 0311-7786264\n- Rozan: 0800-22444\n- Mental Health: 0800-00-009"
                )
            st.markdown(reply)

            # Goodbye check
            goodbye_words = ["bye","goodbye","allah hafiz","khuda hafiz","alvida","good night","take care","shukriya"]
            if any(w in user_input.lower() for w in goodbye_words) and len(st.session_state.emotions) > 1:
                summary = get_mood_summary(st.session_state.emotions)
                st.markdown(f"\n---\n📊 **Mood Summary:** {summary}")
                reply += f"\n---\n📊 **Mood Summary:** {summary}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

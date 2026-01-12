import streamlit as st
import tempfile
from pathlib import Path
import time
import random
from datetime import datetime

# -------------------------
# Backend Integration
# -------------------------
try:
    from newrec import process_audio
except ImportError:
    def process_audio(path, fast=True):
        time.sleep(1) 
        return {
            "raw_text": "I think the price is too high for this service.",
            "sentiment": "pricing_objection",
            "intent": "Negotiation",
            "action": "Offer a 10% loyalty discount.",
            "recommendation": "Explain the value proposition clearly."
        }

# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(page_title="NEURAL INTENT AI", page_icon="🎙️", layout="wide")

# -------------------------
# AI Core Definitions
# -------------------------
companions = {
    "Neuro": {"img": "https://cdn-icons-png.flaticon.com/512/4712/4712109.png", "color": "#00f5ff", "greet": "Neuro Core active. Logic sequencing initiated."},
    "Bolt":  {"img": "https://cdn-icons-png.flaticon.com/512/4712/4712102.png", "color": "#ffd700", "greet": "Bolt here! Speed is my specialty. Ready?"},
    "Nova":  {"img": "https://cdn-icons-png.flaticon.com/512/4712/4712106.png", "color": "#ff007f", "greet": "Nova online. Let's find the hidden patterns."},
}

# -------------------------
# Emoji Mapping
# -------------------------
def get_sentiment_emoji(sentiment):
    sent = str(sentiment).lower()
    if "objection" in sent or "negative" in sent or "angry" in sent:
        return "🛑"
    elif "positive" in sent or "happy" in sent or "satisfied" in sent:
        return "✅"
    elif "question" in sent or "curious" in sent:
        return "❓"
    elif "pricing" in sent:
        return "💰"
    else:
        return "🧠"

# -------------------------
# UI Styling
# -------------------------
def apply_custom_style(accent_color):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&display=swap');
    * {{ font-family: 'Space Grotesk', sans-serif; }}
    .stApp {{ background: #020617; color: #f8fafc; }}
    
    .glass-card {{
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border: 1px solid {accent_color}33;
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 1rem;
    }}
    
    .glow-text {{ color: {accent_color}; text-shadow: 0 0 15px {accent_color}88; text-align: center; text-transform: uppercase; }}
    
    .sidebar-stat {{
        background: rgba(255,255,255,0.05);
        padding: 10px;
        border-radius: 8px;
        border-left: 3px solid {accent_color};
        margin-bottom: 8px;
        font-size: 0.8rem;
    }}

    .stButton>button {{
        background: {accent_color};
        color: #000 !important;
        font-weight: bold;
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 0.7rem;
    }}

    .sentiment-emoji {{
        font-size: 8rem;
        text-align: center;
        display: block;
        margin-bottom: 1rem;
        filter: drop-shadow(0 0 20px {accent_color}66);
    }}
    </style>
    """, unsafe_allow_html=True)

# -------------------------
# Session Setup
# -------------------------
if "page" not in st.session_state: st.session_state.page = "signup"
if "start_time" not in st.session_state: st.session_state.start_time = datetime.now().strftime("%H:%M")

# --- LOGIN PAGE ---
if st.session_state.page == "signup":
    core = companions["Neuro"]
    apply_custom_style(core['color'])
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br><div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.image(core['img'], width=100)
        st.markdown(f"<p style='color:{core['color']}'>\"{core['greet']}\"</p>", unsafe_allow_html=True)
        st.markdown("<h2 class='glow-text'>User Login</h2>", unsafe_allow_html=True)
        u_name = st.text_input("Enter User Name")
        if st.button("INITIALIZE"):
            if u_name:
                st.session_state.user_name = u_name
                st.session_state.page = "dashboard"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- DASHBOARD PAGE ---
elif st.session_state.page == "dashboard":
    with st.sidebar:
        selected_key = st.selectbox("Switch AI Core", list(companions.keys()))
        core = companions[selected_key]
        st.markdown(f"<div style='text-align:center;'><img src='{core['img']}' width='80'><h3 style='color:{core['color']};'>{selected_key.upper()}</h3></div>", unsafe_allow_html=True)
        
        st.markdown("### 🖥️ SYSTEM STATS")
        st.markdown(f"""
            <div class='sidebar-stat'><b>User:</b> {st.session_state.user_name}</div>
            <div class='sidebar-stat'><b>Linked Since:</b> {st.session_state.start_time}</div>
            <div class='sidebar-stat'><b>Status:</b> Neural Link Stable</div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.page = "signup"
            st.rerun()

    apply_custom_style(core['color'])
    st.markdown("<h1 class='glow-text'>🎙️ AI INTENT ANALYZER</h1>", unsafe_allow_html=True)

    # 1. Action Card
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Audio Transmission", type=["wav", "mp3", "m4a"])
    if uploaded_file:
        st.audio(uploaded_file)
        if st.button(f"🚀 EXECUTE {selected_key.upper()} ANALYSIS"):
            with st.spinner("Decoding audio..."):
                t_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix)
                t_file.write(uploaded_file.read())
                st.session_state.last_result = process_audio(t_file.name)
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. Results
    if "last_result" in st.session_state:
        res = st.session_state.last_result
        t1, t2, t3 = st.tabs(["📝 TRANSCRIPT", "🧠 INTENT & TONE", "💡 STRATEGY"])

        with t1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("Summarized Text")
            st.info(res.get("cleaned_text", res.get("raw_text", "No text detected.")))
            if "entities" in res:
                st.markdown("---")
                st.subheader("Entities Detected")
                st.write(", ".join(res.get("entities", [])))
            st.markdown("</div>", unsafe_allow_html=True)

        with t2:
            st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
            # Emoji Display
            emoji = get_sentiment_emoji(res.get("sentiment", ""))
            st.markdown(f"<div class='sentiment-emoji'>{emoji}</div>", unsafe_allow_html=True)
            
            # Tone Display
            st.markdown(f"<h1 style='color:{core['color']}'>{str(res.get('sentiment', 'Unknown')).upper()}</h1>", unsafe_allow_html=True)
            st.markdown("<p style='opacity:0.6;'>Neural pattern analysis complete.</p>", unsafe_allow_html=True)
            
            if "intent" in res:
                st.markdown(f"<h3>Primary Intent: {res.get('intent')}</h3>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with t3:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.warning(f"**Immediate Action:** {res.get('action', 'Monitor conversation.')}")
            st.success(f"**AI Recommendation:** {res.get('recommendation', 'Continue standard operations.')}")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='text-align:center; opacity:0.3; margin-top:50px;'>📡 Waiting for audio input...</p>", unsafe_allow_html=True)
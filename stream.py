import streamlit as st
import tempfile
from pathlib import Path
import time
import random
import matplotlib.pyplot as plt
import numpy as np

# Optional: WordCloud (kept for future, not used for entities visualization)
try:
    from wordcloud import WordCloud
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False

# Your audio processing function.
# Expected keys in the returned dict:
# raw_text, cleaned_text, sentiment, sentiment_confidence, sentiment_explanation,
# entities (list), action, recommendation, error (optional)
from newrec import process_audio

st.set_page_config(page_title="🎧 Audio Intent Analyzer", page_icon="🎤", layout="centered")

# -------------------------
# Session state
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "signup"
if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""
if "uploaded_path" not in st.session_state:
    st.session_state.uploaded_path = None
if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = ""

# -------------------------
# Shared assets and helpers
# -------------------------
companions = {
    "Neuro": "https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
    "Bolt":  "https://cdn-icons-png.flaticon.com/512/4712/4712102.png",
    "Nova":  "https://cdn-icons-png.flaticon.com/512/4712/4712106.png",
    "Echo":  "https://cdn-icons-png.flaticon.com/512/4712/4712110.png",
}

def glow_color_for(name):
    return "blue" if name == "Neuro" else "yellow" if name == "Bolt" else "purple" if name == "Nova" else "green"

def typewriter(text, speed=0.03):
    ph = st.empty()
    typed = ""
    for ch in text:
        typed += ch
        ph.markdown(
            f"<div style='font-family:monospace; color:#f5f5f5; text-align:center;'>{typed}</div>",
            unsafe_allow_html=True,
        )
        time.sleep(speed)

# -------------------------
# Global CSS
# -------------------------
st.markdown("""
<style>
/* Base gradient */
.stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); }

/* Signup page aesthetics */
.signup-wrap { display:flex; flex-direction:column; align-items:center; gap:20px; margin-top:60px; }
.ai-avatar { width:140px; height:140px; border-radius:50%; box-shadow:0 0 18px rgba(0,245,255,0.6); animation:pulseGlow 2s infinite; object-fit:cover; }
@keyframes pulseGlow { 0%{box-shadow:0 0 5px rgba(0,245,255,0.6);} 50%{box-shadow:0 0 20px rgba(0,245,255,0.9);} 100%{box-shadow:0 0 5px rgba(0,245,255,0.6);} }
.input-card { background:rgba(0,0,0,0.35); border-radius:12px; padding:16px; width:100%; max-width:340px; box-shadow:0 4px 10px rgba(0,0,0,0.35); }
.input-card h4 { margin:0 0 8px 0; font-size:16px; color:#f5f5f5; }

/* Sidebar companion */
.companion-img { border-radius:50%; animation:pulseGlow 2s infinite; }

/* Cards (left-aligned with consistent width) */
.card { background:linear-gradient(135deg,#232526,#414345); border-radius:12px; padding:14px; color:#f5f5f5; box-shadow:0 4px 10px rgba(0,0,0,0.35); margin-bottom:16px; max-width:640px; }
.card h3, .card h4 { margin:0 0 10px 0; font-size:18px; }

/* Ensure Streamlit default blocks don't add unexpected margins before headings */
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Page 1: Signup
# -------------------------
if st.session_state.page == "signup":
    # Animated gradient for signup page
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1f1c2c, #928dab);
        animation: gradientShift 10s ease infinite;
        background-size: 400% 400%;
    }
    @keyframes gradientShift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='signup-wrap'>", unsafe_allow_html=True)

    signup_ai = random.choice(list(companions.keys()))
    st.markdown(f"<img src='{companions[signup_ai]}' class='ai-avatar' alt='AI' />", unsafe_allow_html=True)

    # Friendly animated greeting
    typewriter("Welcome to Audio Intent Analyzer", speed=0.02)

    # Inputs
    st.markdown("<div class='input-card'><h4>📝 Your Name</h4>", unsafe_allow_html=True)
    name = st.text_input("", key="name_input", placeholder="Enter your name")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='input-card'><h4>🔒 Password</h4>", unsafe_allow_html=True)
    password = st.text_input(label= "Password", type="password",placeholder="Enter a password", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Continue ➡️"):
        if name and password:
            st.session_state.customer_name = name
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.warning("Please fill both fields.")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Page 2: Dashboard
# -------------------------
elif st.session_state.page == "dashboard":
    st.title("🎧 Audio Intent Analyzer")

    # Sidebar
    selected_companion = st.sidebar.selectbox("🧠 Choose Your AI Companion", list(companions.keys()))
    glow_color = glow_color_for(selected_companion)
    st.sidebar.markdown(
        f"<div style='--glow-color:{glow_color};'><img src='{companions[selected_companion]}' "
        f"class='companion-img' width='120' alt='Companion' /></div>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("### 🤖 Companion info")
    st.sidebar.info(f"You selected **{selected_companion}**.\nThis AI helps analyze tone and intent.")
    st.sidebar.markdown("### 💡 Quick tips")
    st.sidebar.write("- Upload clear audio\n- Use WAV/MP3 for best results\n- Check sentiment + entities")
    if st.sidebar.button("↩️ Back to Sign-Up"):
        st.session_state.page = "signup"
        st.session_state.uploaded_path = None
        st.session_state.uploaded_name = ""
        st.rerun()

    # Greetings
    typewriter(f"👋 Hello, I am {selected_companion}", speed=0.02)
    if st.session_state.customer_name:
        typewriter(f"🙌 Hello {st.session_state.customer_name}", speed=0.02)

    # Upload card (left-aligned)
    st.markdown("<div class='card'><h3>📂 Upload audio</h3>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload an audio file", type=["wav","mp3","m4a","flac","ogg"])
    if uploaded:
        audio_data = uploaded.read()
        st.audio(audio_data)
        if st.button("⬆️ Confirm upload"):
            suffix = Path(uploaded.name).suffix or ".wav"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(audio_data); tmp.flush(); tmp.close()
            st.session_state.uploaded_path = tmp.name
            st.session_state.uploaded_name = uploaded.name
            st.success(f"✅ File uploaded: {uploaded.name}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Process and results
    if st.session_state.uploaded_path:
        if st.button("🚀 Process Audio"):
            tmp_path = st.session_state.uploaded_path
            with st.spinner("⏳ Processing audio — please wait..."):
                result = process_audio(tmp_path, fast=True)

            if result.get("error"):
                st.error(f"❌ Error: {result['error']}")

            # Transcript + Cleaned Text (side-by-side, headings first, left-aligned cards)
            colA, colB = st.columns(2)
            with colA:
                st.markdown("<div class='card'><h3>📝 Transcript</h3>", unsafe_allow_html=True)
                st.write(result.get("raw_text", ""))
                st.markdown("</div>", unsafe_allow_html=True)
            with colB:
                st.markdown("<div class='card'><h3>✨ Cleaned text</h3>", unsafe_allow_html=True)
                st.write(result.get("cleaned_text", ""))
                st.markdown("</div>", unsafe_allow_html=True)

            # Entities (plain text, left-aligned)
            st.markdown("<div class='card'><h3>🔤 Entities</h3>", unsafe_allow_html=True)
            entities = result.get("entities", [])
            if entities:
                st.write(", ".join(entities))
            else:
                st.write("No entities found.")
            st.markdown("</div>", unsafe_allow_html=True)

            # Sentiment (vertical, compact left-aligned, headings first)
            st.markdown("<div class='card'><h3>📊 Sentiment</h3>", unsafe_allow_html=True)
            sentiment = (result.get("sentiment", "") or "").lower()
            confidence = float(result.get("sentiment_confidence", 0.0) or 0.0)
        

            if "positive" in sentiment:
                st.markdown("😊 **Positive**")
                score = confidence if confidence > 0 else 0.9
                color = "#21c55d"
            elif "neutral" in sentiment:
                st.markdown("😐 **Neutral**")
                score = confidence if confidence > 0 else 0.5
                color = "#f59e0b"
            elif "negative" in sentiment:
                st.markdown("😡 **Negative**")
                score = confidence if confidence > 0 else 0.1
                color = "#ef4444"
            else:
                st.markdown("❓ **Unknown**")
                score = 0.0
                color = "#9ca3af"

            st.write(f"**Confidence:** {score:.2f}")
        

            # Half-size gauge
            fig, ax = plt.subplots(figsize=(1.2, 0.6))
            ax.axis("off")
            theta = np.linspace(0, np.pi, 120)
            ax.plot(np.cos(theta), np.sin(theta), color="gray", linewidth=3)
            ax.plot([0, np.cos(score * np.pi)], [0, np.sin(score * np.pi)], color=color, linewidth=2)
            ax.text(0, -0.2, f"Score: {score:.2f}", ha="center", fontsize=8, color="white")
            st.pyplot(fig)
            st.markdown("</div>", unsafe_allow_html=True)

            # Action (below sentiment, left-aligned)
            st.markdown("<div class='card'><h3>⚡ Action</h3>", unsafe_allow_html=True)
            st.write(result.get("action", ""))
            st.markdown("</div>", unsafe_allow_html=True)

            # Recommendation (below action, left-aligned)
            st.markdown("<div class='card'><h3>💡 Recommendation</h3>", unsafe_allow_html=True)
            st.write(result.get("recommendation", ""))
            st.markdown("</div>", unsafe_allow_html=True)

            # Debug expander
            with st.expander("🔍 Raw result (debug)"):
                st.json(result)

    # Bottom: Back to Sign-Up (always available)
    if st.button("↩️ Back to Sign-Up"):
        st.session_state.page = "signup"
        st.session_state.uploaded_path = None
        st.session_state.uploaded_name = ""
        st.rerun()

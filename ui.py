import streamlit as st
import requests
import uuid
import pandas as pd
import os
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
API_URL = "http://127.0.0.1:8000"

# --- Page Config & Theme ---
st.set_page_config(
    page_title="AutoStream AI | Intelligence Terminal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS (Glassmorphism & Vibrancy) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main Background */
    .stApp {
        background: radial-gradient(circle at top left, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }

    /* Glassmorphism Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
        width: 350px !important;
    }

    /* Glass Card containers (Optional: Only applied to custom divs if needed) */
    .custom-glass-card {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
    }

    #MainMenu {visibility: hidden;}
    h1 {
        font-weight: 800 !important;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }

    /* CRM Sidebar Elements */
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 2rem;
        color: #ffffff;
    }

    /* Custom Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        transition: 0.3s all !important;
    }

    .stButton>button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 5px 15px rgba(118, 75, 162, 0.4) !important;
    }

    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Initialization ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar Logic ---
with st.sidebar:
    # Logo
    try:
        logo = Image.open("assets/logo.png")
        st.image(logo, use_container_width=True)
    except Exception:
        st.title("🤖 AutoStream AI")
    
    st.markdown('<div class="sidebar-header">🏢 CRM Admin Portal</div>', unsafe_allow_html=True)
    st.info("Direct access to the SQLite Business Intelligence Engine.")
    
    if st.button("Query Global Leads DB"):
        try:
            response = requests.get(f"{API_URL}/leads/")
            if response.status_code == 200:
                data = response.json()
                if data["leads"]:
                    df = pd.DataFrame(data["leads"])
                    df = df[['timestamp', 'name', 'email', 'platform']]
                    st.markdown("### Active Qualified Leads")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("The CRM is currently empty. Start chatting to capture leads.")
            else:
                st.error("CRM Backend Unreachable.")
        except requests.exceptions.ConnectionError:
            st.error("API link broken. Start `api.py` first.")
    
    st.divider()
    st.caption("AutoStream AI Engine v3.0 | 2026 High Availability Edition")

# --- Main Interface ---
col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.image("assets/logo.png", width=60)
with col2:
    st.title("AutoStream AI Intelligence Terminal")

st.markdown("""
<p style='color: rgba(255,255,255,0.6); font-size: 1.1rem; margin-bottom: 2rem;'>
    Secure conversational tunnel connected to Dual-Brain LLM Engine (Gemini & Groq Fallback).
</p>
""", unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input & Logic
if user_input := st.chat_input("Initiate command or inquiry..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Synchronizing with Dual-Brain Engine..."):
        try:
            response = requests.post(f"{API_URL}/chat/", json={
                "message": user_input,
                "thread_id": st.session_state.thread_id
            })
            
            if response.status_code == 200:
                bot_reply = response.json()["response"]
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
            else:
                st.error(f"Engine Latency Error ({response.status_code})")
        except requests.exceptions.ConnectionError:
            st.error("Backend Server (api.py) is offline.")

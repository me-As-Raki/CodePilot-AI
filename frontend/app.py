# app.py

import streamlit as st
import requests
import os
import json
from datetime import datetime
from streamlit_option_menu import option_menu
from styles import apply_theme_styles

st.set_page_config(page_title="RAG Code Assistant", layout="wide")

# ========== Session State ==========
st.session_state.setdefault("selected_tab", "Home")
st.session_state.setdefault("upload_successful", False)
st.session_state.setdefault("dark_mode", st.get_option("theme.base") == "dark")
st.session_state.setdefault("logs", [])
st.session_state.setdefault("uploaded_file_names", [])
st.session_state.setdefault("last_question", "")
st.session_state.setdefault("last_answer", "")

# ========== Theme Styles ==========
theme, dark_mode = apply_theme_styles()

# ========== Sidebar Theme Toggle ==========
with st.sidebar:
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = st.get_option("theme.base") == "dark"

    current_mode = st.session_state.dark_mode
    toggle_label = "🌙 Switch to Dark Mode" if not current_mode else "🌞 Switch to Light Mode"

    st.markdown("### Theme Mode")
    user_toggle = st.toggle(toggle_label, value=current_mode, key="theme_toggle")

    if user_toggle != current_mode:
        st.session_state.dark_mode = user_toggle
        st.rerun()

# ========== Sidebar ==========
with st.sidebar:
    sidebar_title_color = theme.get("accent_color", "#E91E63")
    sidebar_text_color = theme.get("text_color", "#ffffff")

    st.markdown(f"""
        <div style="padding-bottom: 1rem; line-height: 1.4;">
            <div style="font-family: 'Segoe UI', sans-serif; font-size: 1.4rem; font-weight: 700; color: {sidebar_title_color}; margin-bottom: 0.25rem;">
                🚀 RAG Code Assistant
            </div>
            <div style="font-family: 'Fira Code', monospace; font-size: 0.9rem; color: {sidebar_text_color}; font-style: italic;">
                Chat with your C/C++ files instantly
            </div>
        </div>
    """, unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=["Home", "Logs", "Diagram", "About"],
        icons=["house", "journal-text", "diagram-3", "info-circle"],
        default_index=["Home", "Logs", "Diagram", "About"].index(st.session_state.selected_tab),
        orientation="vertical"
    )

st.session_state.selected_tab = selected

# ========== Home ==========
def render_home():
    text_color = theme['text_color']
    accent_color = theme['accent_color']

    st.markdown(f"""
        <h1 style="font-size: 2.3rem; text-align: center; color: {accent_color}; margin-top: 0.2rem;">
            💬 Chat with Your C/C++ Code
        </h1>
    """, unsafe_allow_html=True)

    st.divider()

    valid_exts = {".c", ".cpp", ".h", ".hpp"}
    files_to_send = []

    st.markdown(f"<h4 style='color: {text_color};'>📤 Upload Mode</h4>", unsafe_allow_html=True)
    mode = st.radio("", ["📁 Manual Upload", "🗂 File Paths"], horizontal=True)

    if mode == "📁 Manual Upload":
        st.markdown(f"<div style='color: {text_color};'>Upload C/C++ source files</div>", unsafe_allow_html=True)
        uploaded = st.file_uploader("", type=list(valid_exts), accept_multiple_files=True)
        if uploaded:
            files_to_send = [("files", (f.name, f.read())) for f in uploaded]
            st.session_state.uploaded_file_names = [f.name for f in uploaded]
    else:
        st.markdown(f"<div style='color: {text_color};'>Enter file paths below</div>", unsafe_allow_html=True)
        raw_paths = st.text_area("", placeholder="C:\\code\\main.c\nC:\\project\\module.cpp")
        path_list = [p.strip() for p in raw_paths.strip().splitlines() if os.path.exists(p.strip())]
        files_to_send = [("files", (os.path.basename(p), open(p, "rb"))) for p in path_list]
        st.session_state.uploaded_file_names = [os.path.basename(p) for p in path_list]

    if st.button("🚀 Upload & Embed"):
        if not files_to_send:
            st.warning("⚠ Please provide at least one valid file.")
        else:
            with st.spinner("📤 Uploading and embedding files..."):
                try:
                    res = requests.post("http://localhost:9000/upload", files=files_to_send)
                    if res.status_code == 200:
                        st.success("✅ Upload successful!")
                        st.session_state.upload_successful = True
                    else:
                        st.error("❌ Upload failed from backend.")
                except Exception as e:
                    st.error(f"⚠ Upload error: {e}")

    if st.session_state.upload_successful and st.session_state.uploaded_file_names:
        st.markdown("<h4 style='margin-top: 2rem;'>✅ Uploaded Files</h4>", unsafe_allow_html=True)
        for name in st.session_state.uploaded_file_names:
            st.markdown(f"<div style='margin-bottom: 0.3rem; color: {'white' if st.session_state.dark_mode else 'black'};'>• {name}</div>", unsafe_allow_html=True)

        query = st.text_input("Ask a question:", value=st.session_state.last_question,
                              placeholder="e.g., What does the parser module do?")

        if st.button("Submit"):
            if not query.strip():
                st.warning("⚠ Please enter a question.")
            else:
                uploaded_files = st.session_state.uploaded_file_names
                if uploaded_files and len(uploaded_files) == 1:
                    filename = uploaded_files[0]
                    query_to_send = f"In {filename}, {query.strip()}"
                else:
                    query_to_send = query.strip()

                with st.spinner("🔍 Connecting to Gemini and retrieving answer..."):
                    try:
                        res = requests.post("http://localhost:9000/ask", json={"query": query_to_send})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.last_question = query
                            st.session_state.last_answer = data["answer"]

                            log_entry = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "question": query_to_send,
                                "answer": data["answer"]
                            }
                            st.session_state.logs.append(log_entry)

                            # ✅ Save to query_logs.json
                            try:
                                os.makedirs("data", exist_ok=True)
                                log_path = "data/query_logs.json"
                                existing = []

                                if os.path.exists(log_path):
                                    with open(log_path, "r", encoding="utf-8") as f:
                                        try:
                                            existing = json.load(f)
                                            if not isinstance(existing, list):
                                                existing = []
                                        except json.JSONDecodeError:
                                            st.warning("⚠ Log file is corrupted or empty. Overwriting it.")

                                existing.append(log_entry)

                                with open(log_path, "w", encoding="utf-8") as f:
                                    json.dump(existing, f, indent=2)

                            except Exception as e:
                                st.error(f"⚠ Failed to save logs: {e}")

                            st.success("✅ Answer received.")
                        else:
                            st.error("❌ Error from backend.")
                    except Exception as e:
                        st.error(f"⚠ Request failed: {e}")

        if st.session_state.last_answer:
            st.markdown("### 📝 Latest Answer")
            st.info(st.session_state.last_answer)



# ========== Logs ==========
def render_logs():
    try:
        from views import logs as logs_page
        logs_page.app(theme)
    except Exception as e:
        st.error(f"⚠ Logs page failed to load: {e}")


# ========== Diagram ==========
def render_diagram():
    try:
        from views import diagram as diagram_page
        diagram_page.app(theme)
    except Exception as e:
        st.error(f"⚠ Diagram page failed to load: {e}")


# ========== About ==========
def render_about():
    try:
        from views import about as about_page
        about_page.app(theme)
    except Exception as e:
        st.error(f"⚠ About page failed to load: {e}")


# ========== Routing ==========
if st.session_state.selected_tab == "Home":
    render_home()
elif st.session_state.selected_tab == "Logs":
    render_logs()
elif st.session_state.selected_tab == "Diagram":
    render_diagram()
elif st.session_state.selected_tab == "About":
    render_about()

# ================== 📦 Imports ==================
import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
from streamlit_option_menu import option_menu

# ================== 🎨 Theme Colors ==================
dark_theme = {
    "primary_bg": "#121212",
    "text_color": "#FFFFFF",
    "input_bg": "#1F1F1F",
    "accent_color": "#E91E63",
    "accent_soft": "#9C27B0",
    "shadow": "rgba(0,0,0,0.6)",
    "sidebar_bg": "#1A1A1A"
}

light_theme = {
    "primary_bg": "#FDFDFD",
    "text_color": "#212121",
    "input_bg": "#FFFFFF",
    "accent_color": "#3F51B5",
    "accent_soft": "#BBDEFB",
    "shadow": "rgba(0,0,0,0.1)",
    "sidebar_bg": "#FAFAFA"
}

# ================== ⚙️ Page Setup ==================
st.set_page_config(page_title="RAG Code Assistant", layout="wide")

# Track selected tab across reruns
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "Home"

# ================== 🌓 Theme Toggle in Sidebar ==================
with st.sidebar:
    st.markdown("### Theme Mode", unsafe_allow_html=True)
    
    dark_mode = st.toggle(
        label="", 
        value=st.session_state.get("dark_mode", False),
        key="dark_mode"
    )

    st.markdown(
        "🌙 <span style='font-weight: 500;'>Dark Mode</span>" if dark_mode
        else "☀ <span style='font-weight: 500;'>Light Mode</span>",
        unsafe_allow_html=True
    )

# Select active theme
theme = dark_theme if st.session_state.dark_mode else light_theme

# ================== 💅 Global Style Injection ==================
st.markdown(f"""
<style>
/* ========== App Base ========== */
.stApp {{
    background-color: {theme['primary_bg']};
    color: {theme['text_color']};
    font-family: 'Segoe UI', sans-serif;
}}

html, body, p, div, span, label {{
    color: {theme['text_color']} !important;
}}

h1, h2, h3, h4 {{
    color: {theme['accent_color']} !important;
}}

/* ========== Sidebar ========== */
.stSidebar > div:first-child {{
    background-color: {theme['sidebar_bg']};
    padding: 1rem;
    border-radius: 0 12px 12px 0;
}}

.css-1d391kg, .css-1d3w5wq {{
    position: fixed !important;
    right: 0 !important;
    left: auto !important;
    border-left: 1px solid rgba(0,0,0,0.1);
    border-right: none;
}}

.css-1outpf7 {{
    margin-left: 0 !important;
    margin-right: 300px !important;
}}

/* ========== Inputs & Text Areas ========== */
.stTextInput input, .stTextArea textarea {{
    background-color: {theme['input_bg']} !important;
    color: {theme['text_color']} !important;
    padding: 12px;
    border-radius: 10px;
    box-shadow: 2px 2px 10px {theme['shadow']};
    font-size: 16px;
}}

input[type="text"] {{
    color: {"#000000" if not dark_mode else "#FFFFFF"} !important;
}}

/* ========== Buttons ========== */
.stButton > button {{
    background-color: {theme['accent_color']} !important;
    color: white !important;
    font-weight: 600;
    padding: 10px 20px;
    border-radius: 12px;
    box-shadow: 0px 4px 20px {theme['shadow']};
}}

/* ========== Code Blocks ========== */
code, pre, .stCode, .stMarkdown code {{
    background-color: {"#2C2C2C" if dark_mode else "#EEEEEE"} !important;
    color: {theme['text_color']} !important;
    padding: 8px;
    font-family: 'Courier New', monospace;
    border-radius: 6px;
}}

/* ========== Expander & Markdown Styling ========== */
.stExpander, .stExpander > label,
.stMarkdown, .stMarkdown p, .stMarkdown span {{
    color: {theme['text_color']} !important;
}}

.stMarkdown ul li {{
    font-size: 16px;
    color: {theme['text_color']} !important;
}}

.stMarkdown .answer-block {{
    background-color: {theme['input_bg']} !important;
    color: {theme['text_color']} !important;
    padding: 1rem;
    font-size: 16px;
    line-height: 1.6;
    border-radius: 10px;
    box-shadow: 0 0 10px {theme['shadow']};
}}

/* ========== Mermaid Diagrams ========== */
.element-container svg {{
    background-color: transparent !important;
}}

.node rect, .node circle {{
    fill: {theme['input_bg']} !important;
}}

.node text {{
    fill: {theme['text_color']} !important;
}}
</style>
""", unsafe_allow_html=True)


# ===================== Sidebar Toggle State =====================
if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = True
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "Home"

# ===================== Sidebar Toggle Button =====================
toggle_label = "⬅️ Hide Sidebar" if st.session_state.show_sidebar else "➡️ Show Sidebar"
if st.button(toggle_label):
    st.session_state.show_sidebar = not st.session_state.show_sidebar

# ===================== Sidebar Content =====================
if st.session_state.show_sidebar:
    with st.sidebar:
        # Sidebar Branding
        st.markdown(f"""
            <style>
            .sidebar-title {{
                font-size: 26px;
                font-weight: 900;
                text-align: center;
                padding: 8px 0;
                background: linear-gradient(90deg, {theme['accent_color']}, {theme['accent_soft']});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .sidebar-subtitle {{
                font-size: 13px;
                color: {'#BBBBBB' if st.session_state.dark_mode else '#555555'};
                text-align: center;
                font-style: italic;
                margin-bottom: 20px;
            }}
            </style>
            <div class='sidebar-title'>🚀 RAG Code Assistant</div>
            <div class='sidebar-subtitle'>Chat with your C/C++ files instantly</div>
        """, unsafe_allow_html=True)

        # Navigation Menu
        selected = option_menu(
            menu_title=None,
            options=["Home", "Logs", "Diagram", "About"],
            default_index=["Home", "Logs", "Diagram", "About"].index(st.session_state.selected_tab),
            key="menu_selection",
            styles={
                "container": {
                    "background-color": theme["sidebar_bg"],
                    "border-radius": "16px",
                    "padding": "12px",
                    "box-shadow": "0 8px 24px rgba(0,0,0,0.2)" if st.session_state.dark_mode else "0 6px 14px rgba(0,0,0,0.05)"
                },
                "nav-link": {
                    "font-size": "15px",
                    "font-weight": "600",
                    "color": theme["text_color"],
                    "padding": "10px 16px",
                    "margin": "6px 0",
                    "border-radius": "10px",
                    "text-align": "center",
                    "transition": "all 0.3s ease"
                },
                "nav-link-hover": {
                    "background-color": "#444444" if st.session_state.dark_mode else "#EFEFEF",
                    "color": "#FFFFFF" if st.session_state.dark_mode else "#000000"
                },
                "nav-link-selected": {
                    "background-color": theme["accent_color"],
                    "color": "#FFFFFF",
                    "font-weight": "800",
                    "box-shadow": "0 4px 16px rgba(0,0,0,0.15)"
                }
            }
        )
        st.session_state.selected_tab = selected

    # Sidebar Styling
    st.markdown(f"""
        <style>
        section[data-testid="stSidebar"] {{
            background: linear-gradient(
                to bottom right,
                {theme['sidebar_bg']},
                {'#2C2C2C' if st.session_state.dark_mode else '#E8EAF6'}
            );
            padding: 2rem 1.5rem;
            border-radius: 0 24px 24px 0;
            box-shadow: 0 0 16px {theme['shadow']};
            transition: all 0.3s ease-in-out;
        }}
        section[data-testid="stSidebar"] * {{
            color: {theme['text_color']};
            font-family: 'Segoe UI', sans-serif;
        }}
        </style>
    """, unsafe_allow_html=True)
# ===================== Session State Setup =====================
if "upload_successful" not in st.session_state:
    st.session_state.upload_successful = False
if "query_submitted" not in st.session_state:
    st.session_state.query_submitted = False

# ===================== Header =====================
st.markdown("<h1 style='text-align:center;'>💬 Chat with Your C/C++ Code</h1>", unsafe_allow_html=True)
st.divider()

# ===================== Home Page =====================
if st.session_state.selected_tab == "Home":

    # --- Section Header Box ---
    st.markdown(f"""
    <div style='
        background-color: {theme['input_bg']};
        padding: 30px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 4px 16px {theme['shadow']};
        color: {theme['text_color']};
    '>
        <h3 style='color:{theme["accent_color"]}; margin-bottom: 10px;'>📤 Upload C/C++ Files or Enter File Paths</h3>
        <p style='font-size: 14px;'>Choose <strong>one</strong> method only to send files to the RAG engine.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Custom Theme Styles for Upload & Textarea ---
    st.markdown(f"""
    <style>
    .uploadedFile {{ background-color: {theme['input_bg']} !important; color: {theme['text_color']} !important; }}
    .stTextArea textarea {{
        background-color: {theme['input_bg']} !important;
        color: {theme['text_color']} !important;
        border-radius: 10px;
        padding: 12px;
        font-size: 14px;
        border: none;
        box-shadow: 0 0 10px {theme['shadow']};
    }}
    .stRadio > div {{
        background-color: {theme['input_bg']} !important;
        color: {theme['text_color']} !important;
        border-radius: 10px;
        padding: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- Upload Mode Selection ---
    mode = st.radio("Select Upload Mode:", ["📁 Manual Upload", "🗂 File Paths"], horizontal=True)
    valid_exts = {".c", ".cpp", ".h", ".hpp"}
    files_to_send = []

    # --- Manual Upload Section ---
    if mode == "📁 Manual Upload":
        uploaded_files = st.file_uploader("Upload files", type=list(valid_exts), accept_multiple_files=True)
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected.")
            with st.expander("📁 Uploaded Files", expanded=False):
                for f in uploaded_files:
                    st.markdown(f"- ✔ **{f.name}**")
            files_to_send = [("files", (f.name, f.read())) for f in uploaded_files]

    # --- File Path Section ---
    else:
        file_paths_input = st.text_area("System File Paths:", placeholder="e.g., C:\\code\\main.c\nC:\\project\\module.cpp")
        file_list = [p.strip() for p in file_paths_input.strip().splitlines() if p.strip()]
        valid_paths = [f for f in file_list if os.path.exists(f) and os.path.splitext(f)[1].lower() in valid_exts]
        invalid_paths = [f for f in file_list if f not in valid_paths]

        if file_paths_input:
            for f in invalid_paths:
                st.warning(f"❌ Invalid file: `{f}`")

            if valid_paths:
                st.success(f"✅ {len(valid_paths)} valid file(s) found.")
                with st.expander("📁 Valid Paths", expanded=False):
                    for f in valid_paths:
                        st.markdown(f"- ✔ **{f}**")
                files_to_send = [("files", (os.path.basename(p), open(p, "rb"))) for p in valid_paths]

    # --- Upload Button ---
    if st.button("🚀 Upload & Embed"):
        if not files_to_send:
            st.warning("⚠ Please upload or enter at least one valid file.")
        else:
            with st.status("Uploading...", expanded=True) as status:
                try:
                    res = requests.post("http://localhost:9000/upload", files=files_to_send)
                    if res.status_code == 200:
                        st.toast("Upload complete ✅", icon="🚀")
                        st.session_state.upload_successful = True
                        st.session_state.query_submitted = False
                        status.update(label="✅ Upload successful", state="complete")
                    else:
                        st.error("❌ Upload failed.")
                        st.code(res.text)
                        status.update(label="❌ Upload failed", state="error")
                except Exception as e:
                    st.error(f"⚠ Exception occurred: {e}")
                    status.update(label="❌ Upload exception", state="error")
if st.session_state.upload_successful:
    st.markdown(f"""
    <div style='background-color: {theme['input_bg']}; padding: 2rem;
                border-radius: 16px; box-shadow: 0 6px 20px {theme['shadow']};
                margin-top: 30px;'>
        <h3 style='color:{theme["accent_color"]}; margin-bottom: 0.5rem;'>💡 Ask a Question About Your Code</h3>
        <p style='color:{theme["text_color"]}; font-size: 15px; margin-bottom: 1rem;'>
            Enter your question below to explore the uploaded codebase.
        </p>
    """, unsafe_allow_html=True)

    # Style input box
    input_text_color = "#000000" if not dark_mode else "#FFFFFF"
    input_bg_color = theme["input_bg"]

    st.markdown(f"""
    <style>
    .custom-query-input input {{
        background-color: {input_bg_color} !important;
        color: {input_text_color} !important;
        border: none;
        padding: 14px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px {theme['shadow']};
        font-size: 16px;
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("Your question:", placeholder="e.g., What does the parser module do?",
                              key="query_input", label_visibility="collapsed")
    with col2:
        st.write("")  # vertical spacing
        submitted = st.button("Submit", use_container_width=True)

    if submitted and query.strip():
        st.session_state.query_submitted = True
        st.markdown("### 🧠 Console")
        console = st.empty()
        console.markdown("🟡 Sending query...")

        with st.status("Contacting backend...", expanded=True) as status:
            try:
                start = time.time()
                response = requests.post("http://localhost:9000/ask", json={"query": query, "top_k": 5})
                elapsed = time.time() - start

                if response.status_code == 200:
                    data = response.json()
                    status.update(label="✅ Response received.", state="complete")
                    console.markdown(f"🟢 Provider: {data.get('provider', 'Unknown')}")

                    st.markdown("### 📝 Answer")
                    st.markdown(f"<div class='answer-block'>{data['answer']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:gray;'>⏱ Time: {elapsed:.2f}s</span>", unsafe_allow_html=True)

                    if data.get("chunks_used"):
                        st.markdown("### 📦 Code Context")
                        for chunk in data["chunks_used"]:
                            with st.expander(f"{chunk['file']} — Lines {chunk['start_line']} to {chunk['end_line']}"):
                                st.code(chunk["code"], language="cpp")

                    # Log the interaction
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "query": query,
                        "response": data['answer'],
                        "elapsed": elapsed,
                        "provider": data.get("provider", "Unknown")
                    }
                    logs_path = "../data/query_logs.json"
                    logs = []
                    os.makedirs("../data", exist_ok=True)
                    if os.path.exists(logs_path):
                        with open(logs_path, "r", encoding="utf-8") as f:
                            logs = json.load(f)
                    logs.append(log_entry)
                    with open(logs_path, "w", encoding="utf-8") as f:
                        json.dump(logs, f, indent=2)
                    st.toast("Query logged.", icon="✅")
                    console.markdown("✅ Logged.")
                else:
                    status.update(label="❌ Backend error.", state="error")
                    console.markdown(f"❌ Error {response.status_code}.")
            except Exception as e:
                status.update(label=f"⚠ Failed: {e}", state="error")
                console.markdown(f"❌ Exception: {e}")

    st.markdown("</div>", unsafe_allow_html=True)  # close top section


# ===================== Logs Page =====================
elif st.session_state.selected_tab == "Logs":
    st.markdown(f"<h2 style='color:{theme['accent_color']}'>📜 Recent Query Logs</h2>", unsafe_allow_html=True)
    try:
        with open("../data/query_logs.json", "r", encoding="utf-8") as f:
            logs = json.load(f)
        for log in reversed(logs[-10:]):
            with st.expander(f"🕒 {log['timestamp']} — ⏱ {log['elapsed']:.2f}s — 🔮 {log['provider']}", expanded=False):
                st.markdown(f"🗨 Query:\ntext\n{log['query']}\n")
                st.markdown("📝 Answer:")
                st.code(log["response"], language="markdown")
    except FileNotFoundError:
        st.info("🚫 No logs yet. Start chatting!")

# ===================== Diagram Page =====================
elif st.session_state.selected_tab == "Diagram":
    st.markdown(f"<h2 style='color:{theme['accent_color']}'>🧠 RAG Pipeline Diagram</h2>", unsafe_allow_html=True)
    st.markdown("Visualize how your uploaded C/C++ files are processed to generate accurate answers:")

    # Mermaid chart (Streamlit auto-renders this)
    st.markdown("""
```mermaid
flowchart TD
    UI["🌐 Streamlit UI"] --> Upload["📁 Upload Files or Paths"]
    Upload --> API["🔗 api.py"]
    API --> Parser["🧠 parser.py (uploaded only)"]
    Parser --> Chunks["📦 chunks_uploaded/*.json"]
    Chunks --> Embedder["✨ embedder.py"]
    Embedder --> Vectors[(🧠 Vector Store)]

    UI --> Ask["❓ Ask a Question"]
    Ask --> API
    API --> Retriever["🎯 retriever.py"]
    Retriever --> Generator["🧬 generator.py"]
    Generator --> LLM["🔮 Gemini / Cohere"]
    LLM --> Answer["📤 Final Answer"]
    Answer --> UI
""", unsafe_allow_html=True)

# ===================== About Page =====================
elif st.session_state.selected_tab == "About":
    st.markdown(f"<h2 style='color:{theme['accent_color']}'>ℹ About This Assistant</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background-color:{theme['input_bg']}; padding: 1.5rem; border-radius: 12px;
                box-shadow: 0 4px 15px {theme['shadow']}; font-size: 16px; line-height: 1.7;'>
        <p>This RAG-based assistant helps you explore and understand large C/C++ codebases with precision.</p>
        <ul>
            <li>📤 Upload or path-based file ingestion</li>
            <li>📦 Chunk parsing and smart embedding</li>
            <li>🔍 Context-aware retrieval (Chroma + CodeBERT)</li>
            <li>💬 LLM-powered code Q&A (Gemini / Cohere)</li>
            <li>🌙 Light & Dark theme switching</li>
            <li>🧠 Terminal-style console logging</li>
        </ul>
        <p style='margin-top:1rem; font-style: italic;'>Crafted for developers who work with legacy and complex C/C++ projects.</p>
    </div>
    """, unsafe_allow_html=True)

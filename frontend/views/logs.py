# pages/logs.py

import streamlit as st
import os
import json
from styles import apply_theme_styles

def app(theme):
    st.markdown(f"<h2 style='color:{theme['accent_color']}'>📜 Query Logs</h2>", unsafe_allow_html=True)
    st.write("Review all past queries submitted to the RAG assistant.")

    log_file = os.path.join("data", "query_logs.json")
    session_logs = st.session_state.get("logs", [])

    combined_logs = []

    # 1. Load saved logs from disk
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                saved_logs = json.load(f)
                if isinstance(saved_logs, list):
                    combined_logs.extend(saved_logs)
        except Exception as e:
            st.error(f"❌ Failed to read saved logs: {e}")

    # 2. Add live logs from session (avoid duplicates)
    if session_logs:
        combined_logs.extend(log for log in session_logs if log not in combined_logs)

    if not combined_logs:
        st.info("🟡 No logs found yet. Ask a question on the Home tab.")
        return

    # 3. Display logs in reverse chronological order
    for entry in reversed(combined_logs):
        timestamp = entry.get("timestamp", "Unknown Time")
        question = entry.get("question", "No question recorded")
        answer = entry.get("answer", "No answer available")

        with st.expander(f"🕒 {timestamp} — {question[:60]}"):
            st.markdown(f"**🧠 Question:** `{question}`")
            st.markdown(f"**📝 Answer:**\n\n{answer}")

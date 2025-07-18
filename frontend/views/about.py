import streamlit as st
from styles import apply_theme_styles

def app(theme):
    st.markdown("## ℹ️ About CodePilot-AI", unsafe_allow_html=True)

    st.markdown("### 🚀 Project Overview")
    st.markdown("""
**CodePilot-AI** is a *Retrieval-Augmented Generation (RAG)* assistant built to understand and answer questions about C/C++ codebases.

It intelligently splits your code into semantic chunks, embeds them, and queries an LLM like **Gemini** for accurate, context-aware answers.
    """)

    st.markdown("### 🔧 Features")
    st.markdown("""
- 📁 Upload or specify C/C++ file paths  
- 🧠 Semantic chunking of functions, structs, macros, and more  
- ⚡ Vector search using FAISS for similarity-based retrieval  
- 📝 Natural language Q&A using Gemini or other LLMs  
- 📜 View full logs and visual pipeline diagrams  
    """)

    st.markdown("### 🧱 Tech Stack")
    st.markdown("""
- 💻 **Frontend**: Streamlit (with dynamic dark/light theme)  
- 🛠 **Backend**: FastAPI, Tree-sitter for parsing  
- 🧮 **Embedding**: FAISS for fast vector indexing  
- 🤖 **LLMs**: Gemini (Google), optional: Cohere, CodeBERT  
    """)

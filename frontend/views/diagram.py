import streamlit as st
import pathlib
from PIL import Image

def app(theme):
    st.markdown(f"<h2 style='color:{theme['accent_color']}; margin-bottom: 1rem;'>🧠 RAG Pipeline Diagram</h2>", unsafe_allow_html=True)

    st.markdown(f"""
        <p style='font-size: 1.05rem; line-height: 1.6;'>
        This visual guide shows how <b>CodePilot-AI</b> processes C/C++ code files using a RAG-based assistant pipeline.
        Each stage works together to convert your codebase into smart answers using advanced language models.
        </p>
    """, unsafe_allow_html=True)

    # 📁 Path to image
    diagram_path = pathlib.Path(__file__).parent / "pipeline_image.png"

    # ✅ CSS for styling and hover
    st.markdown(f"""
        <style>
            .pipeline-container {{
                display: flex;
                justify-content: center;
                margin: 1.5rem 0;
            }}
            .pipeline-img {{
                width: 300px;
                height: auto;
                border-radius: 12px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                border: 2px solid {theme['accent_color']};
                margin-top : -10px;
            }}
            .pipeline-img:hover {{
                transform: scale(1.05);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
            }}
        </style>
    """, unsafe_allow_html=True)

    # ✅ Show image using st.image (resolves loading issues)
    if diagram_path.exists():
        # Streamlit can't apply CSS to st.image directly — workaround using st.markdown + base64
        import base64
        with open(diagram_path, "rb") as f:
            data_url = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(f"""
        <div class="pipeline-container">
            <img src="data:image/png;base64,{data_url}" class="pipeline-img" alt="RAG Pipeline Diagram">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠ Diagram image not found.")
        st.info(f"Expected at: `{diagram_path}`")

    # 📘 Detailed steps
    with st.expander("📝 Detailed Pipeline Steps", expanded=False):
        st.markdown(f"""
        <div style='font-size: 0.98rem; line-height: 1.7; font-family: "Courier New", monospace; background-color: {theme['input_bg']}; padding: 1.2rem; border-radius: 8px;'>
        📥 <b>Upload:</b> Accepts <code>.c</code>, <code>.cpp</code>, <code>.h</code> files via file upload or folder path.<br><br>
        🧠 <b>Parser:</b> Extracts <i>functions</i>, <i>macros</i>, <i>typedefs</i>, <i>global variables</i> as semantic code chunks.<br><br>
        🔎 <b>Embedder:</b> Converts each chunk into embeddings using <code>Gemini</code>, <code>CodeBERT</code>, etc.<br><br>
        🗃️ <b>Vector DB (FAISS):</b> Stores embeddings for fast semantic retrieval.<br><br>
        ❓ <b>Query:</b> User question is embedded and matched with stored vectors.<br><br>
        🤖 <b>LLM Generator:</b> Uses top-k results + query to produce a response using LLMs.
        </div>
        """, unsafe_allow_html=True)

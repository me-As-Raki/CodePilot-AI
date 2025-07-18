import streamlit as st

# ================== 🎨 Theme Color Palettes ==================
dark_theme = {
    "primary_bg": "#121212",
    "text_color": "#F5F5F5",
    "input_bg": "#1E1E1E",
    "accent_color": "#E91E63",
    "accent_soft": "#9C27B0",
    "shadow": "rgba(0,0,0,0.6)",
    "sidebar_bg": "#1A1A1A",
    "header_gradient": "#ff69b4, #9b59b6"
}

light_theme = {
    "primary_bg": "#FDFDFD",
    "text_color": "#212121",
    "input_bg": "#FFFFFF",
    "accent_color": "#3F51B5",
    "accent_soft": "#BBDEFB",
    "shadow": "rgba(0,0,0,0.1)",
    "sidebar_bg": "#FAFAFA",
    "header_gradient": "#7b2ff7, #f107a3"
}

# ================== 💅 Theme Styler ==================
def apply_theme_styles():
    dark_mode = st.session_state.get("dark_mode", st.get_option("theme.base") == "dark")
    theme = dark_theme if dark_mode else light_theme

    st.markdown(f"""
        <style>
        html, body, .stApp {{
            background-color: {theme['primary_bg']};
            color: {theme['text_color']};
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
        }}

                /* Remove default top padding */
        .block-container {{
            padding-top: 1rem !important;
        }}

        /* Optional: tighten heading spacing */
        h1, h2, h3, h4, h5 {{
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
        }}

        /* Remove gap between heading and uploader */
        .element-container:nth-child(2) {{
            margin-top: 0 !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {theme['sidebar_bg']};
            color: {theme['text_color']};
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {theme['accent_color']} !important;
        }}

        /* Input fields */
        input, textarea, select, .stTextInput>div>div>input {{
            background-color: {theme['input_bg']} !important;
            color: {theme['text_color']} !important;
            border-radius: 8px;
            padding: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        /* Buttons */
        .stButton>button {{
            background-color: {theme['accent_color']} !important;
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 500;
            box-shadow: 0 4px 16px {theme['shadow']};
            transition: 0.3s ease;
        }}

        /* About section formatting */
/* About section formatting */
h2, h3 {{
    margin-top: 1.6rem;
    margin-bottom: 0.5rem;
}}

.stMarkdown {{
    background-color: {{theme['input_bg']}};
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px {{theme['shadow']}};
    color: {{theme['text_color']}};
    font-size: 1rem;
    line-height: 1.0;
}}

ul {{
    padding-left: 1.2rem;
}}

strong {{
    color: {{theme['accent_color']}};
}}

code {{
    background-color: rgba(255, 255, 255, 0.08);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.95rem;
}}
        .stButton>button:hover {{
            background-color: {theme['accent_soft']} !important;
            transform: translateY(-1px);
        }}

        /* Upload box */
        .stFileUploader>div>div {{
            background-color: {theme['input_bg']} !important;
            color: {theme['text_color']} !important;
            border-radius: 10px;
            border: 1px dashed {theme['accent_color']};
            padding: 1rem;
        }}

        /* Expanders */
        .streamlit-expanderHeader {{
            color: {theme['text_color']} !important;
            font-weight: 600;
        }}

        /* Markdown text */
        .stMarkdown, .stText, .stCodeBlock, code {{
            color: {theme['text_color']} !important;
        }}

        /* Mermaid Diagrams */
        .mermaid {{
            color: {theme['text_color']} !important;
        }}

/* Gradient Header */
.main-header {{
    font-size: 40px;
    font-weight: 800;
    text-align: center;
    letter-spacing: 1px;
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    background: linear-gradient(to right, {theme['header_gradient']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    margin-top: 0.5rem;   /* Reduced top margin */
    margin-bottom: 0.5rem; /* Reduced bottom margin */

    padding-top: 0;        /* Ensures it hugs the top */
}}

# styles.py (add inside your CSS string with double curly brackets)
    /* 🎯 Clean square image styling with hover effect */
    .pipeline-img {{
        width: 100px;
        height: 100px;
        object-fit: cover;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        display: block;
        margin: 1.5rem auto;
    }}

    .pipeline-img:hover {{
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }}

    /* Responsive tweaks for smaller screens */
    @media (max-width: 768px) {{
        .pipeline-img {{
            width: 220px;
            height: 220px;
        }}
    }}

    /* Optional caption below image */
    .stImage + div {{
        text-align: center;
        font-size: 0.9rem;
        color: {theme['text_color']};
        margin-top: -0.5rem;
    }}



        /* Links */
        a {{
            color: {theme['accent_color']} !important;
            text-decoration: none;
        }}
        a:hover {{
            color: {theme['accent_soft']} !important;
        }}

        /* ================== Radio Button Fix ================== */
        .stRadio > div {{
            background-color: {theme['input_bg']} !important;
            border-radius: 10px;
            padding: 0.5rem;
        }}

        .stRadio label, .stRadio div[data-testid="stMarkdownContainer"] p {{
            color: {theme['text_color']} !important;
            font-weight: 500;
        }}

        /* ================== File Uploader Label Fix ================== */
        label[data-testid="stFileUploaderLabel"] {{
            color: {theme['text_color']} !important;
            font-weight: 500;
        }}

        /* ================== Textarea / Input Label Fix ================== */
        label, .stTextInput label {{
            color: {theme['text_color']} !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    return theme, dark_mode

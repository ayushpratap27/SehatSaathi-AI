"""
SehatSaathi-AI — Streamlit Frontend
Landing page MVP. Full feature pages will be added in Phase 7.

Run with:
    streamlit run frontend/app.py
"""

import streamlit as st

# ---- Page configuration -------------------------------------------------- #
st.set_page_config(
    page_title="SehatSaathi-AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom CSS ---------------------------------------------------------- #
st.markdown(
    """
    <style>
        .hero-title {
            font-size: 2.8rem;
            font-weight: 800;
            color: #1a6b4a;
            line-height: 1.2;
        }
        .hero-subtitle {
            font-size: 1.15rem;
            color: #555;
            margin-top: 0.4rem;
        }
        .disclaimer-box {
            background: #fff8e1;
            border-left: 4px solid #f9a825;
            padding: 0.8rem 1rem;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #555;
        }
        .feature-card {
            background: #f4faf7;
            border: 1px solid #d0e8dc;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.5rem;
        }
        .coming-soon-badge {
            background: #e8f5e9;
            color: #2e7d32;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 12px;
            display: inline-block;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Sidebar ------------------------------------------------------------- #
with st.sidebar:
    st.image(
        "https://img.icons8.com/color/96/medical-history.png",
        width=64,
    )
    st.markdown("## SehatSaathi-AI")
    st.markdown("*Your medical report companion*")
    st.divider()

    st.markdown("### Navigation")
    st.markdown("🏠 **Home** ← you are here")
    st.markdown("📤 Upload Report *(Phase 2)*")
    st.markdown("📊 View Analysis *(Phase 3)*")
    st.markdown("💬 Chat with Report *(Phase 6)*")
    st.markdown("👤 My Account *(Phase 8)*")

    st.divider()
    st.caption("v0.1.0 — Phase 1: Foundation")

# ---- Hero section -------------------------------------------------------- #
st.markdown(
    '<p class="hero-title">🏥 SehatSaathi-AI</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="hero-subtitle">'
    "AI-powered Medical Report Understanding System — "
    "bridging the gap between complex medical reports and everyday understanding."
    "</p>",
    unsafe_allow_html=True,
)

st.divider()

# ---- Disclaimer ---------------------------------------------------------- #
st.markdown(
    '<div class="disclaimer-box">'
    "⚠️ <strong>Medical Disclaimer:</strong> SehatSaathi-AI is an informational tool only. "
    "It explains the contents of your uploaded reports but does <strong>not</strong> "
    "diagnose, prescribe, or replace professional medical advice. "
    "Always consult a qualified healthcare professional for medical decisions."
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

# ---- Upload section (placeholder) --------------------------------------- #
st.subheader("📤 Upload Your Medical Report")

upload_col, info_col = st.columns([2, 1])

with upload_col:
    st.info(
        "Document upload will be available in **Phase 2**.\n\n"
        "Supported formats will include: PDF, PNG, JPG, TIFF."
    )
    uploaded_file = st.file_uploader(
        "Select a medical report",
        type=["pdf", "png", "jpg", "jpeg", "tiff"],
        disabled=True,
        help="File upload is disabled in Phase 1.",
    )
    st.button("🚀 Analyse Report", disabled=True, use_container_width=True)

with info_col:
    st.markdown("**Max file size:** 50 MB")
    st.markdown("**Accepted formats:**")
    st.markdown("- PDF (digital & scanned)")
    st.markdown("- PNG / JPG / TIFF")

st.divider()

# ---- Feature overview ---------------------------------------------------- #
st.subheader("✨ What SehatSaathi-AI will do for you")

features = [
    ("📄 Extract Report Content", "Read both digital and scanned PDFs using OCR.", "Phase 2"),
    ("🔬 Identify Lab Values", "Detect abnormal results — High, Low, Critical.", "Phase 3"),
    ("🧬 Find Medical Entities", "Diseases, medications, procedures, and symptoms.", "Phase 3"),
    ("📝 Plain-Language Summary", "Understand your report without a medical degree.", "Phase 5"),
    ("💬 Chat with Your Report", "Ask questions and get grounded, cited answers.", "Phase 6"),
    ("🔐 Secure & Private",       "Your documents are yours — isolated by user account.", "Phase 8"),
]

col1, col2 = st.columns(2)
for i, (title, desc, phase) in enumerate(features):
    target_col = col1 if i % 2 == 0 else col2
    with target_col:
        st.markdown(
            f'<div class="feature-card">'
            f"<strong>{title}</strong> "
            f'<span class="coming-soon-badge">{phase}</span>'
            f"<br><small>{desc}</small>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.divider()

# ---- Technology stack ---------------------------------------------------- #
with st.expander("🛠️ Technology Stack"):
    tech_col1, tech_col2, tech_col3 = st.columns(3)

    with tech_col1:
        st.markdown("**Backend**")
        st.markdown("- Python 3.12")
        st.markdown("- FastAPI")
        st.markdown("- SQLAlchemy")
        st.markdown("- Alembic")

    with tech_col2:
        st.markdown("**AI / NLP**")
        st.markdown("- spaCy + SciSpaCy")
        st.markdown("- LangChain")
        st.markdown("- FAISS")
        st.markdown("- Sentence Transformers")
        st.markdown("- EasyOCR / PyMuPDF")

    with tech_col3:
        st.markdown("**Infrastructure**")
        st.markdown("- PostgreSQL")
        st.markdown("- Docker")
        st.markdown("- GitHub Actions")
        st.markdown("- Streamlit (MVP UI)")

st.divider()
st.caption(
    "SehatSaathi-AI © 2026 | Phase 1: Foundation | "
    "Features will be added incrementally across upcoming phases."
)

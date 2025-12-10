import streamlit as st

st.set_page_config(page_title="data-canary", page_icon="Canary", layout="wide")
st.title("Canary data-canary v0.0.1")
st.subheader("Upload any CSV/Parquet → AI tells you everything wrong in plain English")

uploaded_file = st.file_uploader("Drop your file here", type=["csv", "parquet"])

if uploaded_file is not None:
    st.success(f"Loaded {uploaded_file.name} – {uploaded_file.size:,} bytes")
    st.info("LLM magic scan coming in the next commit…")
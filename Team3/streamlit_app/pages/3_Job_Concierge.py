"""Wrapper page for LikHong's Job Concierge dashboard."""

import streamlit as st

st.set_page_config(
    page_title="Job Concierge — Lik Hong",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys
import os
from pathlib import Path

# Add LikHong's folder to sys.path
_likhong_dir = str(Path(__file__).parent.parent / "LikHong")
if _likhong_dir not in sys.path:
    sys.path.insert(0, _likhong_dir)

# LikHong's sgjobs.py uses a relative DB path — temporarily change CWD
# so that '../../data/raw/SGJobData.db' resolves correctly.
_original_cwd = os.getcwd()
os.chdir(_likhong_dir)

# Monkey-patch set_page_config to skip the duplicate call inside sgjobs.py
_original_spc = st.set_page_config
st.set_page_config = lambda **kwargs: None

import sgjobs  # noqa: E402 — triggers module-level CSS + DB connection

st.set_page_config = _original_spc
os.chdir(_original_cwd)

# Run the app
sgjobs.main()

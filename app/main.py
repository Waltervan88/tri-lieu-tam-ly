"""
Tri-Lieu-Tam-Ly — Entry point for Streamlit.
Routes to the appropriate page based on user role.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ─── Init DB on startup ───────────────────────────────────────────────────────

from app.data.db import init_db, seed_demo_users

init_db()
seed_demo_users()

# ─── Default page (if run directly) ──────────────────────────────────────────

# If a specific page is requested via query param, use it
# Otherwise redirect to login
st.switch_page("pages/00_Login.py")

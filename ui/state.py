"""
State Initialization: Loads permanent data from MongoDB and configures
temporary Streamlit session UI state.
"""
import streamlit as st
from database.db_manager import db

def initialize_system_state():
    # 1. TEMPORARY UI STATE (Filters, current tab, widget visibility)
    if "lang" not in st.session_state:
        st.session_state.lang = "EN"
    if "user_role" not in st.session_state:
        st.session_state.user_role = "HR USER"
    if "active_campaign" not in st.session_state:
        st.session_state.active_campaign = "Senior Backend Engineer (FastAPI/AI)"
    if "copilot_expanded" not in st.session_state:
        st.session_state.copilot_expanded = False
    if "viewing_candidate_id" not in st.session_state:
        st.session_state.viewing_candidate_id = None

    # 2. PERMANENT DATA FROM MONGODB
    # Re-synced from MongoDB so fresh changes are always reflected
    st.session_state.campaigns = db.get_campaigns()
    st.session_state.candidates = db.get_candidates()
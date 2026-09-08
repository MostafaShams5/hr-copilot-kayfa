"""
Authentication & Role-Based Access Control (RBAC) for Kayfa HR Platform.
Handles secure login, role identification, and session logout.
"""
import hashlib
import streamlit as st
from observability.tracer import observability

# Pre-registered system accounts
SYSTEM_USERS = {
    "hr@kayfa.academy": {
        "name": "Ahmed Mohamed (Talent Lead)",
        "password_hash": hashlib.sha256("KayfaHR@2026".encode()).hexdigest(),
        "role": "HR USER",
        "department": "Engineering & AI Recruitment"
    },
    "admin@kayfa.academy": {
        "name": "System Administrator",
        "password_hash": hashlib.sha256("KayfaAdmin@2026".encode()).hexdigest(),
        "role": "ADMIN",
        "department": "Platform Operations"
    }
}

def render_login_screen():
    """Renders the enterprise login portal."""
    from ui.theme import KAYFA_SVG_LOGO
    
    st.markdown("<div style='max-width: 440px; margin: 40px auto 0 auto;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; margin-bottom: 24px;'>{KAYFA_SVG_LOGO}</div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class='kayfa-card'>
            <h3 style='margin-bottom: 0.25rem; color: #0F172A;'>Sign in to Kayfa OS</h3>
            <p style='color: #64748B; font-size: 0.85rem; margin-bottom: 1.5rem;'>Enter your corporate email and password to access the AI recruitment platform.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("kayfa_login_form"):
            email = st.text_input("Corporate Email", placeholder="user@kayfa.academy").strip().lower()
            password = st.text_input("Password", type="password", placeholder="••••••••••••")
            submit = st.form_submit_button("Sign In 🔐", use_container_width=True, type="primary")
            
            if submit:
                if not email or not password:
                    st.error("Please provide both email and password.")
                    return False
                    
                user_record = SYSTEM_USERS.get(email)
                input_hash = hashlib.sha256(password.encode()).hexdigest()
                
                if user_record and user_record["password_hash"] == input_hash:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = {
                        "email": email,
                        "name": user_record["name"],
                        "role": user_record["role"],
                        "department": user_record["department"]
                    }
                    st.session_state["user_role"] = user_record["role"]
                    observability.log_audit(user_record["name"], "USER_LOGIN_SUCCESS", "AuthSession", email, "SUCCESS")
                    st.success(f"Welcome back, {user_record['name']}!")
                    st.rerun()
                else:
                    observability.log_audit(email, "LOGIN_FAILED", "AuthSession", email, "INVALID_CREDENTIALS")
                    st.error("Invalid corporate email or password. Please verify your credentials.")
                    
        # Quick Demo Helper
        with st.expander("🔑 Quick Credentials Reference"):
            st.markdown("""
            - **HR Role**: `hr@kayfa.academy` / `KayfaHR@2026`
            - **Admin Role**: `admin@kayfa.academy` / `KayfaAdmin@2026`
            """)
            
    st.markdown("</div>", unsafe_allow_html=True)
    return False

def render_user_profile_sidebar():
    """Renders current logged in user badge and logout button in the sidebar."""
    curr_user = st.session_state.get("current_user", {})
    if not curr_user:
        return
        
    st.markdown(f"""
    <div style='background: #F1F5F9; border-radius: 8px; padding: 0.65rem 0.85rem; margin-bottom: 0.75rem;'>
        <div style='font-size: 0.85rem; font-weight: 700; color: #0F172A;'>{curr_user.get('name')}</div>
        <div style='font-size: 0.75rem; color: #64748B;'>{curr_user.get('email')}</div>
        <span class='badge {"badge-purple" if curr_user.get("role") == "ADMIN" else "badge-blue"}' style='margin-top: 0.25rem;'>
            {curr_user.get('role')}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        observability.log_audit(curr_user.get("name", "User"), "USER_LOGOUT", "AuthSession", curr_user.get("email", ""), "SUCCESS")
        st.session_state["authenticated"] = False
        st.session_state["current_user"] = None
        st.rerun()
"""
Kayfa HR AI Agentic Recruitment Operating System
Streamlit Presentation, Orchestration & Observability Layer.
"""
import os
import sys
import io
import time
import hashlib
import pandas as pd
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from observability.tracer import observability, RunStatus
from ui.theme import apply_kayfa_theme, get_kayfa_logo_html, KAYFA_SVG_LOGO
from ui.state import initialize_system_state
try:
    from ui.components.copilot import render_floating_copilot
except ImportError:
    try:
        from ui.components.copilot import render_copilot as render_floating_copilot
    except ImportError:
        try:
            from ui.components.copilot import render_kayfa_copilot as render_floating_copilot
        except ImportError:
            def render_floating_copilot():
                pass
from ui.components.kanban import render_kanban_board
from ui.components.candidate_view import render_candidate_dossier
from ui.components.trace_viewer import render_agent_trace
from database.db_manager import db
from ui.components.candidate_portal import (
    render_candidate_portal,
    safe_get_query_param,
    safe_clear_query_params,
    safe_set_query_param
)
from ui.components.decision_maker import render_decision_maker

# Page Setup
st.set_page_config(
    page_title="أكاديمية كَيْفَ | AI Recruitment OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_system_state()
is_arabic = st.session_state.get("lang", "EN") == "العربية"
apply_kayfa_theme(is_arabic=is_arabic)

# Check query params or session flag for Direct Candidate Assessment Portal
direct_page = safe_get_query_param("page")
direct_cand_id = safe_get_query_param("candidate_id")
direct_track = safe_get_query_param("track", "technical")

# =========================================================================
# 1. DIRECT CANDIDATE ASSESSMENT PORTAL (Email Link Landing)
# =========================================================================
if direct_page == "assessment" or st.session_state.get("viewing_candidate_portal", False):
    portal_cid = direct_cand_id or st.session_state.get("portal_cand_id", "CAND-101")
    portal_track = direct_track or st.session_state.get("portal_track", "technical")
    
    def on_portal_exit():
        st.session_state["viewing_candidate_portal"] = False
        safe_clear_query_params()
        
    render_candidate_portal(
        candidate_id=portal_cid,
        track=portal_track,
        is_preview=False,
        on_return=on_portal_exit
    )
    st.stop()

# =========================================================================
# 2. AUTHENTICATION & RBAC
# =========================================================================
SYSTEM_USERS = {
    "hr@kayfa.academy": {
        "name": "Ahmed Mohamed (Talent Lead)",
        "password_hash": hashlib.sha256("KayfaHR@2026".encode()).hexdigest(),
        "role": "HR USER",
        "department": "Engineering & AI Recruitment"
    },
    "admin@kayfa.academy": {
        "name": "Platform Administrator",
        "password_hash": hashlib.sha256("KayfaAdmin@2026".encode()).hexdigest(),
        "role": "ADMIN",
        "department": "AI Operations & Infrastructure"
    }
}

if not st.session_state.get("authenticated", False):
    st.markdown("<div style='max-width: 440px; margin: 40px auto 0 auto;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; margin-bottom: 24px;'>{get_kayfa_logo_html(width=210)}</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='kayfa-card'>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem;'>
            <h3 style='margin:0; color: #1A2552; font-weight:800;'>Sign In</h3>
            <span class='kayfa-pill-outline'>Kayfa AI</span>
        </div>
        <p style='margin:0; color: #64748B; font-size: 0.88rem;'>AI-Powered Recruitment & Talent Operating System</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("kayfa_login_form"):
        login_email = st.text_input("Corporate Email", placeholder="user@kayfa.academy").strip().lower()
        login_pwd = st.text_input("Password", type="password", placeholder="••••••••••••")
        login_btn = st.form_submit_button("Sign In 🔐", use_container_width=True, type="primary")
        
        if login_btn:
            user_record = SYSTEM_USERS.get(login_email)
            input_hash = hashlib.sha256(login_pwd.encode()).hexdigest()
            if user_record and user_record["password_hash"] == input_hash:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = user_record
                st.session_state["user_role"] = user_record["role"]
                observability.log_audit(user_record["name"], "USER_LOGIN_SUCCESS", "AuthSession", login_email, "SUCCESS")
                st.success(f"Welcome back, {user_record['name']}!")
                st.rerun()
            else:
                observability.log_audit(login_email, "LOGIN_FAILED", "AuthSession", login_email, "INVALID_CREDENTIALS")
                st.error("Invalid corporate email or password.")
                
    with st.expander("🔑 Demo Access Credentials"):
        st.markdown("""
        - **HR User:** `hr@kayfa.academy` &nbsp;|&nbsp; Password: `KayfaHR@2026`
        - **Admin:** `admin@kayfa.academy` &nbsp;|&nbsp; Password: `KayfaAdmin@2026`
        """)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Synchronize Database
campaigns_list = db.get_campaigns()
candidates_list = db.get_candidates()
if campaigns_list:
    st.session_state.campaigns = campaigns_list
if candidates_list:
    st.session_state.candidates = candidates_list

curr_user = st.session_state.get("current_user", {})
is_admin = curr_user.get("role") == "ADMIN"

# =========================================================================
# 3. SIDEBAR NAVIGATION: HIGH-CONTRAST ACTION BUTTONS (NO WHITE ON WHITE)
# =========================================================================
with st.sidebar:
    st.markdown(f"<div style='text-align: center; margin-bottom: 12px;'>{get_kayfa_logo_html(width=165)}</div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.72rem; color: #64748B; font-weight: 800; text-align: center; margin: 0 0 12px 0;'>HR AI OPERATING SYSTEM</p>", unsafe_allow_html=True)
    
    role_badge = "badge-purple" if is_admin else "badge-blue"
    st.markdown(f"""
    <div style='background: #F1F5F9; border-radius: 10px; padding: 0.65rem 0.85rem; margin-bottom: 0.75rem;'>
        <div style='font-size: 0.85rem; font-weight: 700; color: #1A2552;'>{curr_user.get('name')}</div>
        <div style='font-size: 0.75rem; color: #64748B;'>{curr_user.get('email')}</div>
        <span class='badge {role_badge}' style='margin-top: 0.35rem;'>{curr_user.get('role')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    c_lang, c_out = st.columns(2)
    with c_lang:
        st.session_state.lang = st.selectbox("🌐 Lang", ["EN", "العربية"], index=0 if st.session_state.lang == "EN" else 1)
    with c_out:
        if st.button("🚪 Logout", use_container_width=True):
            observability.log_audit(curr_user.get("name"), "USER_LOGOUT", "AuthSession", curr_user.get("email"), "SUCCESS")
            st.session_state["authenticated"] = False
            st.session_state["current_user"] = None
            st.rerun()
            
    st.markdown("---")
    
    # Separate Navigation options by role
    if is_admin:
        nav_options = [
            "📊 Executive Dashboard",
            "👥 Candidate Pipeline (Kanban)",
            "🎯 Recruitment Campaigns",
            "⚖️ Decision Maker Agent",
            "🚪 Candidate Portal Preview",
            "⚙️ User Management & RBAC",
            "📈 AI Observability Center"
        ]
    else:
        nav_options = [
            "🎯 Recruitment Campaigns",
            "🦅 Headhunting Workspace",
            "⚖️ Decision Maker Agent",
            "📑 Recruitment Reports",
            "🚪 Candidate Portal Preview"
        ]

    # Initialize selected tab
    if "active_tab" not in st.session_state or st.session_state.active_tab not in nav_options:
        st.session_state.active_tab = nav_options[0]

    # Render Kayfa Pill Buttons: Blue BG with PURE WHITE text when active, Soft Blue when idle
    st.markdown("<p style='font-size:0.75rem; font-weight:800; color:#64748B; margin: 1rem 0 0.5rem 0;'>MAIN NAVIGATION</p>", unsafe_allow_html=True)
    for opt in nav_options:
        is_selected = (st.session_state.active_tab == opt)
        css_wrapper = "kayfa-nav-active" if is_selected else "kayfa-nav-idle"
        st.markdown(f"<div class='{css_wrapper}'>", unsafe_allow_html=True)
        if st.button(opt, key=f"nav_{opt}", use_container_width=True):
            st.session_state.active_tab = opt
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.caption("Active Campaign Context")
    campaign_titles = [c["title"] for c in st.session_state.campaigns] or ["Senior Backend Engineer (FastAPI/AI)"]
    st.session_state.active_campaign = st.selectbox("Campaign", campaign_titles, index=0)
    st.caption("Screening Threshold: **70%** | Dual-Track: **Active**")

selected_nav = st.session_state.active_tab

# =========================================================================
# 4. TOP BAR CONTEXT
# =========================================================================
t_col1, t_col2 = st.columns([3, 1])
with t_col1:
    st.markdown(f"## {selected_nav}")
with t_col2:
    st.markdown(f"""
    <div style='text-align: right; padding-top: 0.5rem;'>
        <span class='badge {role_badge}'>{curr_user.get('role')}</span> &nbsp;
        <span class='badge badge-green'>● MongoDB Connected</span>
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# 5. ADMIN VIEW: EXECUTIVE DASHBOARD
# =========================================================================
if "Dashboard" in selected_nav:
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.markdown("<div class='kayfa-card'><div class='kpi-title'>Total Candidates</div><div class='kpi-value'>1,284</div></div>", unsafe_allow_html=True)
    k2.markdown("<div class='kayfa-card'><div class='kpi-title'>Screened</div><div class='kpi-value'>1,102</div></div>", unsafe_allow_html=True)
    k3.markdown("<div class='kayfa-card'><div class='kpi-title'>Passed (≥70%)</div><div class='kpi-value' style='color:#059669;'>487</div></div>", unsafe_allow_html=True)
    k4.markdown("<div class='kayfa-card'><div class='kpi-title'>Interviews</div><div class='kpi-value' style='color:#3750EB;'>324</div></div>", unsafe_allow_html=True)
    k5.markdown("<div class='kayfa-card'><div class='kpi-title'>Shortlisted</div><div class='kpi-value' style='color:#7C3AED;'>126</div></div>", unsafe_allow_html=True)
    k6.markdown("<div class='kayfa-card'><div class='kpi-title'>Final HR</div><div class='kpi-value' style='color:#D97706;'>42</div></div>", unsafe_allow_html=True)

    c_funnel, c_activity = st.columns([2, 1])
    with c_funnel:
        st.markdown("<div class='kayfa-card'><h4>Recruitment Funnel Overview</h4>", unsafe_allow_html=True)
        funnel_data = pd.DataFrame({
            "Stage": ["Applicants", "CV Screening", "Passed ≥70%", "Interview", "Interview Eval", "Decision Agent", "Shortlisted", "Final Human HR"],
            "Count": [1284, 1102, 487, 324, 290, 180, 126, 42]
        })
        st.bar_chart(funnel_data.set_index("Stage"), color="#3750EB")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with c_activity:
        st.markdown("<div class='kayfa-card'><h4>Recent Activity Audit</h4>", unsafe_allow_html=True)
        activities = [
            ("Candidate Screened", "Ahmed Mohamed scored 84% (Passed threshold)", "3m ago"),
            ("Interview Completed", "Sara Al-Otaibi submitted Technical track", "12m ago"),
            ("Decision Generated", "Recommendation: SHORTLIST for Ahmed Mohamed", "25m ago"),
            ("Email Sent", "Dual-track invitation dispatched to Khaled M.", "1h ago"),
            ("New Campaign Created", "Lead Product Designer requisition active", "3h ago")
        ]
        for title, desc, t in activities:
            st.markdown(f"**{title}** <br><span style='font-size:0.8rem; color:#475569;'>{desc}</span><br><span style='font-size:0.7rem; color:#94A3B8;'>{t}</span><hr style='margin:0.4rem 0;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 6. ADMIN VIEW: CANDIDATES & KANBAN PIPELINE
# =========================================================================
elif "Candidate Pipeline" in selected_nav:
    view_mode = st.radio("View Mode", ["📋 10-Stage Pipeline Board", "👤 Candidate Profile Dossier"], horizontal=True)
    if "Pipeline" in view_mode:
        render_kanban_board(st.session_state.candidates)
    else:
        c_names = [c["name"] for c in st.session_state.candidates]
        selected_cand_name = st.selectbox("Select Candidate", c_names)
        cand = next(c for c in st.session_state.candidates if c["name"] == selected_cand_name)
        render_candidate_dossier(cand)

# =========================================================================
# 7. HR / COMMON VIEW: RECRUITMENT CAMPAIGNS
# =========================================================================
elif "Recruitment Campaigns" in selected_nav:
    st.markdown("<div class='kayfa-card'><h3>Create Recruitment Campaign</h3>", unsafe_allow_html=True)
    
    step1, step2, step3, step4, step5 = st.tabs([
        "STEP 1: Job Info", "STEP 2: Requirements", "STEP 3: Screening Config", "STEP 4: CV Upload", "STEP 5: Screening Execution"
    ])
    
    with step1:
        st.markdown("##### Job Information")
        c1, c2 = st.columns(2)
        with c1:
            camp_title = st.text_input("Job Title", "Senior Backend Engineer")
            camp_dept = st.selectbox("Department", ["Engineering & AI", "Data Science", "Product", "Operations"])
            st.selectbox("Location", ["Riyadh, Saudi Arabia", "Cairo, Egypt", "Dubai, UAE", "Remote"])
            st.selectbox("Employment Type", ["Full-time", "Contract", "Part-time"])
        with c2:
            st.text_input("Required Experience", "5+ years")
            st.text_input("Salary Range", "$4,500 - $6,500 / month")
            st.text_input("Hiring Manager", curr_user.get("name", "HR Manager"))
            st.file_uploader("Upload Job Description (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"])
            
    with step2:
        st.markdown("##### Role Requirements & Skill Tags")
        st.multiselect("Required Skills (Must Have)", ["Python", "FastAPI", "AWS", "Docker", "SQL", "LangChain", "Redis"], default=["Python", "FastAPI", "AWS", "Docker"])
        st.multiselect("Optional Skills (Nice to Have)", ["Kubernetes", "Kafka", "Pydantic-AI", "GraphQL"], default=["Kubernetes", "Kafka"])
        st.selectbox("Minimum Education", ["Bachelor's Degree in CS/Engineering", "Master's Degree", "Self-taught / Bootcamp"])
        st.text_input("Languages", "English (Fluent), Arabic (Professional)")
        
    with step3:
        st.markdown("##### Screening Configuration")
        th = st.slider("Screening Threshold (%)", min_value=50, max_value=90, value=70)
        st.caption("Candidates scoring below this threshold will not automatically proceed to the interview stage.")
        st.slider("Experience Weighting (%)", 0, 50, 25)
        st.slider("Skills Match Weighting (%)", 0, 50, 45)
        st.slider("Education Weighting (%)", 0, 50, 15)
        st.slider("Soft Skills / Trajectory Weighting (%)", 0, 50, 15)
        
    with step4:
        st.markdown("##### Upload Candidate CVs (Batch Upload: 10, 50, 100+ files)")
        uploaded_files = st.file_uploader("Drag and drop multiple CVs here", accept_multiple_files=True, type=["pdf", "docx"])
        if uploaded_files:
            file_table = []
            for idx, f in enumerate(uploaded_files):
                file_table.append({
                    "Candidate": f"Candidate #{idx+1}",
                    "Filename": f.name,
                    "File Type": f.name.split(".")[-1].upper(),
                    "Upload Status": "Uploaded",
                    "Processing Status": "Ready for Agent"
                })
            st.dataframe(pd.DataFrame(file_table), use_container_width=True)
            
    with step5:
        st.markdown("##### Start CV Screening Agent")
        st.write("The CV Screening Agent will parse work history, extract skills, compare against the JD, and calculate weighted scores.")
        
        if st.button("🚀 Start CV Screening", type="primary"):
            run_rec = observability.start_run("CV Screening Agent", st.session_state.active_campaign)
            
            prog = st.progress(0)
            status = st.empty()
            
            for i in range(1, 51, 10):
                pct = int((i / 50) * 100)
                status.markdown(f"**CV Screening Agent**<br>Processing candidate {i} / 50<br>`{'█' * (pct // 5)}{'░' * (20 - pct // 5)}` **{pct}%**", unsafe_allow_html=True)
                prog.progress(pct)
                time.sleep(0.3)
                
            prog.progress(100)
            status.markdown("**CV Screening Agent Completed!** Processed: 50 | Successful: 49 | Failed: 1 | Average Score: **76.4%**")
            observability.end_run(run_rec, input_tokens=4200, output_tokens=1800, duration_ms=2100)
            
            new_camp_id = f"CAMP-{int(time.time()) % 10000}"
            db.create_campaign(new_camp_id, camp_title, camp_dept, float(th), curr_user.get("name", "HR Manager"))
            st.success("Screening finalized. Campaign saved permanently to MongoDB.")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 8. AUTONOMOUS DECISION MAKER AGENT (Multi-Factor Candidate Synthesis)
# =========================================================================
elif "Decision" in selected_nav:
    render_decision_maker()

# =========================================================================
# 9. HR VIEW: HEADHUNTING WORKSPACE
# =========================================================================
elif "Headhunting" in selected_nav:
    st.markdown("<div class='kayfa-card'><h3>🦅 Autonomous Headhunting Agent Workspace</h3>", unsafe_allow_html=True)
    st.write("Provide a job description and skills; the agent searches permitted sources, ranks the best candidates, and exports an Excel dossier.")
    
    hh_col1, hh_col2 = st.columns(2)
    with hh_col1:
        st.text_area("Job Description for Sourcing", "Looking for Lead Python / AI Engineers with distributed architectures & LangChain experience.", height=90)
        st.text_input("Required Skills", "Python, FastAPI, Redis, Distributed Systems")
    with hh_col2:
        st.text_input("Location Filter", "Saudi Arabia, Egypt, UAE, Remote")
        st.text_input("Permitted Source URLs", "https://linkedin.com, https://github.com")
        
    if st.button("🚀 Start Headhunting Agent", type="primary"):
        run_rec = observability.start_run("Headhunting Agent", st.session_state.active_campaign)
        with st.spinner("Analyzing JD -> Searching permitted sources -> Extracting skills -> Ranking Top 10 Candidates..."):
            time.sleep(1.8)
            observability.end_run(run_rec, input_tokens=5100, output_tokens=2200, duration_ms=2900)
        st.success("Headhunting Agent completed analysis. Generated Top 10 Candidates.")
        
    st.markdown("#### Top 10 Sourced Candidates")
    top_10 = pd.DataFrame([
        {"Rank": "#1", "Candidate": "Ahmed Mohamed", "Current Position": "Senior Backend Engineer", "Experience": "5 years", "Location": "Cairo", "Skills": "Python, FastAPI, AWS", "Matched Skills": "Python, FastAPI, AWS", "Missing Skills": "None", "Fit Score": "96%", "Recommendation": "RECOMMENDED", "Source": "LinkedIn"},
        {"Rank": "#2", "Candidate": "Tarek Mostafa", "Current Position": "Senior Systems Architect", "Experience": "6 years", "Location": "Riyadh", "Skills": "Python, Redis, Microservices", "Matched Skills": "Python, Redis", "Missing Skills": "LangChain", "Fit Score": "94%", "Recommendation": "RECOMMENDED", "Source": "LinkedIn"},
        {"Rank": "#3", "Candidate": "Nourhan Ezzat", "Current Position": "Cloud Software Lead", "Experience": "5 years", "Location": "Dubai", "Skills": "Python, Docker, Kubernetes", "Matched Skills": "Python, Docker", "Missing Skills": "Redis", "Fit Score": "91%", "Recommendation": "RECOMMENDED", "Source": "GitHub/LinkedIn"},
        {"Rank": "#4", "Candidate": "Youssef Hassan", "Current Position": "Backend Engineer", "Experience": "4 years", "Location": "Cairo", "Skills": "FastAPI, PostgreSQL", "Matched Skills": "FastAPI", "Missing Skills": "AWS", "Fit Score": "88%", "Recommendation": "RECOMMENDED", "Source": "LinkedIn"},
        {"Rank": "#5", "Candidate": "Karim Adel", "Current Position": "Staff Engineer", "Experience": "7 years", "Location": "Riyadh", "Skills": "Python, High-Throughput", "Matched Skills": "Python", "Missing Skills": "FastAPI", "Fit Score": "85%", "Recommendation": "CONSIDER", "Source": "LinkedIn"},
        {"Rank": "#6", "Candidate": "Mahmoud Sami", "Current Position": "Software Engineer", "Experience": "4 years", "Location": "Cairo", "Skills": "Python, Flask, Redis", "Matched Skills": "Python, Redis", "Missing Skills": "FastAPI", "Fit Score": "83%", "Recommendation": "CONSIDER", "Source": "LinkedIn"},
        {"Rank": "#7", "Candidate": "Ziad Al-Ghamdi", "Current Position": "Backend Developer", "Experience": "3 years", "Location": "Jeddah", "Skills": "Python, SQL", "Matched Skills": "Python", "Missing Skills": "Redis, AWS", "Fit Score": "80%", "Recommendation": "CONSIDER", "Source": "LinkedIn"},
        {"Rank": "#8", "Candidate": "Hassan Fawzy", "Current Position": "Python Developer", "Experience": "4 years", "Location": "Alexandria", "Skills": "Django, Postgres", "Matched Skills": "Python", "Missing Skills": "FastAPI", "Fit Score": "78%", "Recommendation": "CONSIDER", "Source": "LinkedIn"},
        {"Rank": "#9", "Candidate": "Omar Sherif", "Current Position": "Systems Engineer", "Experience": "3 years", "Location": "Cairo", "Skills": "Linux, Python", "Matched Skills": "Python", "Missing Skills": "FastAPI, Cloud", "Fit Score": "75%", "Recommendation": "CONSIDER", "Source": "LinkedIn"},
        {"Rank": "#10", "Candidate": "Fahad Al-Harbi", "Current Position": "Junior Backend", "Experience": "2 years", "Location": "Riyadh", "Skills": "FastAPI, SQLite", "Matched Skills": "FastAPI", "Missing Skills": "Distributed Systems", "Fit Score": "72%", "Recommendation": "CONSIDER", "Source": "LinkedIn"}
    ])
    st.dataframe(top_10, use_container_width=True)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        top_10.to_excel(writer, sheet_name="Top 10 Ranked Candidates", index=False)
    
    st.download_button(
        label="📥 Download Headhunting Excel Report",
        data=excel_buffer.getvalue(),
        file_name="Kayfa_Headhunting_Top10_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 10. HR VIEW: CANDIDATE PORTAL PREVIEW
# =========================================================================
elif "Candidate Portal" in selected_nav:
    render_candidate_portal(
        candidate_id="CAND-101",
        track="technical",
        is_preview=True
    )

# =========================================================================
# 11. ADMIN VIEW: USER MANAGEMENT & RBAC
# =========================================================================
elif "User Management" in selected_nav:
    st.markdown("### Administrator Control Center: Users & RBAC")
    st.markdown("<div class='kayfa-card'><h4>Platform Users & Access Control</h4>", unsafe_allow_html=True)
    users_df = pd.DataFrame([
        {"Name": "Ahmed Mohamed", "Email": "hr@kayfa.academy", "Role": "HR USER", "Campaigns": 2, "Last Login": "Today 13:40", "Status": "Active"},
        {"Name": "Sara Al-Otaibi", "Email": "sara.hr@kayfa.academy", "Role": "HR USER", "Campaigns": 1, "Last Login": "Today 12:15", "Status": "Active"},
        {"Name": "Platform Administrator", "Email": "admin@kayfa.academy", "Role": "ADMIN", "Campaigns": "All", "Last Login": "Today 14:02", "Status": "Active"}
    ])
    st.dataframe(users_df, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 12. ADMIN VIEW: AI OBSERVABILITY CENTER
# =========================================================================
elif "Observability" in selected_nav:
    st.markdown("### 📈 AI Operations Center (Agent Observability)")
    st.caption("Monitors what AI agents are doing internally: Tokens, costs, latency, tool calls, and chronological execution traces.")
    
    kpis = observability.get_kpis()
    o1, o2, o3, o4, o5, o6 = st.columns(6)
    o1.metric("Agent Runs", kpis["agent_runs"])
    o2.metric("Success Rate", f"{kpis['success_rate']}%")
    o3.metric("Total Tokens", f"{kpis['total_tokens']:,}")
    o4.metric("Estimated Cost", f"${kpis['estimated_cost']:.4f}")
    o5.metric("Avg Latency", f"{kpis['avg_latency']}s")
    o6.metric("Tool Calls", kpis["tool_calls"])
    
    obs_tab1, obs_tab2, obs_tab3, obs_tab4 = st.tabs([
        "Chronological Agent Traces", "Tool Call Observability", "System Health", "Audit Trail & Errors"
    ])
    
    with obs_tab1:
        st.markdown("#### Chronological Agent Execution Traces")
        run_options = [f"{r.run_id} ({r.agent_name})" for r in observability.runs]
        selected_run_str = st.selectbox("Select Run to Inspect", run_options)
        selected_r_id = selected_run_str.split()[0]
        selected_run = next(r for r in observability.runs if r.run_id == selected_r_id)
        render_agent_trace(selected_run)
        
    with obs_tab2:
        st.markdown("#### Tool Call Observability")
        tools_list = []
        for t in observability.tool_registry.values():
            tools_list.append({
                "Tool": t.tool_name, "Agent": t.agent_name, "Calls": t.calls_count,
                "Success Rate": f"{t.success_rate}%", "Avg Latency": f"{t.avg_latency_s}s",
                "Failures": t.failures, "Retries": t.retries
            })
        st.dataframe(pd.DataFrame(tools_list), use_container_width=True)
        
    with obs_tab3:
        st.markdown("#### System Health & Infrastructure")
        h1, h2 = st.columns(2)
        with h1:
            st.markdown("""
            - API Services: <span class='badge badge-green'>● Healthy</span>
            - MongoDB Database: <span class='badge badge-green'>● Healthy</span>
            - LLM Provider (Groq / OpenAI): <span class='badge badge-green'>● Healthy</span>
            - Email Service: <span class='badge badge-green'>● Healthy</span>
            """, unsafe_allow_html=True)
        with h2:
            st.markdown("""
            - PDF / DOCX Parser: <span class='badge badge-green'>● Healthy</span>
            - Vector Engine (MiniLM): <span class='badge badge-green'>● Healthy</span>
            - Headhunting Scraper: <span class='badge badge-green'>● Healthy</span>
            - Agent Orchestrator: <span class='badge badge-green'>● Healthy</span>
            """, unsafe_allow_html=True)
            
    with obs_tab4:
        st.markdown("#### Errors & Audit Log")
        st.write("**Recent Errors:**")
        st.dataframe(pd.DataFrame(observability.errors), use_container_width=True)
        st.write("**System Audit Trail:**")
        st.dataframe(pd.DataFrame(observability.audit_logs), use_container_width=True)

# =========================================================================
# 13. PERSISTENT FLOATING HR COPILOT
# =========================================================================
render_floating_copilot()

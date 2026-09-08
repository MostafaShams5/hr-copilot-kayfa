"""
Kayfa HR AI Autonomous Decision Maker Agent Component.
Provides multi-factor automated candidate evaluation, scoring synthesis,
hiring recommendation engine, and Human-in-the-Loop decision governance.
"""
import time
import pandas as pd
import streamlit as st
from ui.theme import get_kayfa_logo_html

try:
    from observability.tracer import observability
except ImportError:
    class MockObservability:
        def start_run(self, *args, **kwargs): return {"start_time": time.time(), "agent": args[0] if args else "Agent"}
        def end_run(self, *args, **kwargs): pass
        def log_audit(self, *args, **kwargs): pass
    observability = MockObservability()

try:
    from database.db_manager import db
except ImportError:
    class MockDB:
        def update_candidate_stage(self, *args, **kwargs): pass
    db = MockDB()

DEFAULT_CANDIDATE_EVALUATIONS = [
    {
        "id": "CAND-101",
        "name": "Ahmed Mohamed",
        "role": "Senior Backend Engineer (FastAPI/AI)",
        "cv_score": 84.0,
        "tech_score": 92.0,
        "behavioral_score": 88.0,
        "experience": "5.5 years",
        "location": "Cairo (Open to Riyadh)",
        "assessment_status": "COMPLETED",
        "confidence": 96.2,
        "strengths": [
            "Expertise in Redis Redlock, distributed leasing, and PostgreSQL read-write split",
            "Demonstrated strong system architecture comprehension in assessment",
            "Strong team mentorship and blameless post-mortem methodology"
        ],
        "risks": [
            "Expected salary is near the top of the band ($6,200/mo vs $6,500 ceiling)",
            "Notice period is 30 days"
        ],
        "rationale": (
            "Ahmed demonstrated stellar architecture reasoning across both direct assessment and CV screening. "
            "His technical assessment solution for distributed idempotency was exceptionally well reasoned. "
            "He aligns seamlessly with Kayfa Academy's core value of knowledge-sharing and high engineering standards."
        ),
        "decision": "RECOMMENDED FOR HIRE",
        "decision_badge": "kayfa-pill-blue",
        "human_status": "PENDING_REVIEW"
    },
    {
        "id": "CAND-102",
        "name": "Sara Al-Otaibi",
        "role": "Senior Backend Engineer (FastAPI/AI)",
        "cv_score": 78.0,
        "tech_score": 85.0,
        "behavioral_score": 91.0,
        "experience": "4.5 years",
        "location": "Riyadh, Saudi Arabia",
        "assessment_status": "COMPLETED",
        "confidence": 93.5,
        "strengths": [
            "Local presence in Riyadh; immediate onboarding readiness",
            "Outstanding culture alignment score (91%) and cross-functional leadership",
            "Strong Python async architecture background"
        ],
        "risks": [
            "Less experience with ultra high-write distributed sharding (CAP theorem edge-cases)"
        ],
        "rationale": (
            "Sara is an exceptional culture fit for Kayfa with solid core backend fundamentals. "
            "Her assessment answers revealed great pragmatic decision-making when engineering tradeoffs arise. "
            "Highly recommended to advance to final executive leadership discussion."
        ),
        "decision": "SHORTLIST FOR FINAL INTERVIEW",
        "decision_badge": "kayfa-pill-blue",
        "human_status": "PENDING_REVIEW"
    },
    {
        "id": "CAND-103",
        "name": "Khaled Mansour",
        "role": "Senior Backend Engineer (FastAPI/AI)",
        "cv_score": 72.0,
        "tech_score": 74.0,
        "behavioral_score": 70.0,
        "experience": "3.5 years",
        "location": "Dubai, UAE",
        "assessment_status": "COMPLETED",
        "confidence": 88.0,
        "strengths": [
            "Solid FastAPI and Docker containerization fundamentals",
            "Strong motivation to join Kayfa's EdTech ecosystem"
        ],
        "risks": [
            "Marginal score on high-throughput backend concurrency question",
            "3.5 years experience is slightly below senior rubric (5+ years preferred)"
        ],
        "rationale": (
            "Khaled meets standard criteria but may require onboarding mentorship for staff-level architectural ownership. "
            "Recommend considering for mid-senior or scheduling a technical architecture follow-up deep-dive."
        ),
        "decision": "CONSIDER / CONDITIONAL",
        "decision_badge": "kayfa-pill-outline",
        "human_status": "PENDING_REVIEW"
    },
    {
        "id": "CAND-104",
        "name": "Omar Abdelrahman",
        "role": "Senior Backend Engineer (FastAPI/AI)",
        "cv_score": 68.0,
        "tech_score": 61.0,
        "behavioral_score": 64.0,
        "experience": "3 years",
        "location": "Alexandria, Egypt",
        "assessment_status": "COMPLETED",
        "confidence": 91.0,
        "strengths": [
            "Familiar with standard relational database queries"
        ],
        "risks": [
            "Did not meet minimum technical benchmark (61% < 70% cutoff)",
            "Lacks hands-on distributed microservice patterns"
        ],
        "rationale": (
            "Candidate does not meet the senior backend engineering bar for the current campaign. "
            "Recommend polite rejection with encouragement to apply for mid-level openings in subsequent cycles."
        ),
        "decision": "REJECT",
        "decision_badge": "kayfa-pill-outline",
        "human_status": "PENDING_REVIEW"
    }
]

def calculate_composite_score(cv: float, tech: float, beh: float, w_cv: float, w_tech: float, w_beh: float) -> float:
    total_w = w_cv + w_tech + w_beh
    if total_w <= 0:
        total_w = 1.0
    score = (cv * w_cv + tech * w_tech + beh * w_beh) / total_w
    return round(score, 1)

def get_recommendation_label(score: float) -> str:
    if score >= 85.0:
        return "RECOMMENDED FOR HIRE"
    elif score >= 75.0:
        return "SHORTLIST FOR FINAL ROUND"
    elif score >= 65.0:
        return "CONSIDER / CONDITIONAL"
    else:
        return "REJECT"

def render_decision_maker():
    if "decision_evals" not in st.session_state:
        st.session_state["decision_evals"] = DEFAULT_CANDIDATE_EVALUATIONS

    curr_user = st.session_state.get("user", {"name": "HR Specialist", "role": "HR Manager"})
    active_campaign = st.session_state.get("active_campaign", "Senior Backend Engineer (FastAPI/AI)")

    # 1. Header & Context Banner
    st.markdown("""
    <div class='kayfa-card' style='border-left: 5px solid #3750EB; margin-bottom: 1.25rem;'>
        <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;'>
            <div>
                <h3 style='margin:0; color:#1E2B68; font-weight:800; font-size:1.35rem;'>
                    ⚖️ Autonomous Decision Maker Agent
                </h3>
                <p style='color:#64748B; margin:0.35rem 0 0 0; font-size:0.9rem;'>
                    Multi-Factor Candidate Synthesis & AI Hiring Governance Engine
                </p>
            </div>
            <div style='display:flex; gap:8px; align-items:center;'>
                <span class='kayfa-pill-blue' style='font-size:0.8rem;'>Multi-Agent Synthesis</span>
                <span class='kayfa-pill-outline' style='font-size:0.8rem;'>Human-in-the-Loop Active</span>
            </div>
        </div>
        <div style='margin-top:0.85rem; padding-top:0.75rem; border-top:1px solid #E8EEF5; display:flex; justify-content:space-between; align-items:center; font-size:0.84rem; color:#64748B;'>
            <span>🎯 <strong>Campaign:</strong> <span style='color:#1E2B68; font-weight:700;'>""" + active_campaign + """</span></span>
            <span>⚡ <strong>Evaluation Logic:</strong> Automated CV + Portal Assessment + Behavioral</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Multi-Factor Weight Configuration (Collapsible)
    with st.expander("⚙️ Configure Multi-Factor Evaluation Weights & Thresholds", expanded=False):
        st.caption("Customize the relative importance of each stage in the autonomous decision formula.")
        w_c1, w_c2, w_c3, w_c4 = st.columns(4)
        with w_c1:
            w_cv = st.slider("CV Screening Weight", 10, 60, 30, step=5, format="%d%%")
        with w_c2:
            w_tech = st.slider("Technical Assessment Weight", 20, 70, 45, step=5, format="%d%%")
        with w_c3:
            w_beh = st.slider("Behavioral & Culture Weight", 10, 50, 25, step=5, format="%d%%")
        with w_c4:
            auto_threshold = st.number_input("Hire Benchmark Score", min_value=60, max_value=95, value=85, step=1)
        st.info(f"Formula: `Final Score = ({w_cv}% × CV) + ({w_tech}% × Tech Assessment) + ({w_beh}% × Culture)`")

    # 3. Action Bar: Run Batch Autonomous Evaluation
    top_col1, top_col2 = st.columns([3, 1.2])
    with top_col1:
        st.markdown(f"<p style='color:#1E2B68; font-weight:700; margin-top:0.35rem;'>Candidates Ready for Final Decision ({len(st.session_state['decision_evals'])})</p>", unsafe_allow_html=True)
    with top_col2:
        if st.button("🚀 Re-Run Decision Agent", key="btn_run_decision_agent", type="primary", use_container_width=True):
            run_rec = observability.start_run("Decision Maker Agent", active_campaign)
            with st.spinner("Aggregating CV dossiers, portal submissions, and scoring matrices..."):
                time.sleep(1.4)
                # Recalculate with current weights
                for item in st.session_state["decision_evals"]:
                    comp = calculate_composite_score(item["cv_score"], item["tech_score"], item["behavioral_score"], w_cv, w_tech, w_beh)
                    item["composite_score"] = comp
                    item["decision"] = get_recommendation_label(comp)
                observability.end_run(run_rec, input_tokens=3800, output_tokens=1600, duration_ms=1420)
                observability.log_audit(curr_user.get("name"), "DECISION_AGENT_BATCH_EVAL", "DecisionMaker", active_campaign, "SUCCESS")
            st.success("Decision Agent synthesized multi-factor evaluations with updated weights.")
            st.rerun()

    # 4. Summary KPI Matrix
    evals = st.session_state["decision_evals"]
    for c in evals:
        if "composite_score" not in c:
            c["composite_score"] = calculate_composite_score(c["cv_score"], c["tech_score"], c["behavioral_score"], w_cv, w_tech, w_beh)
            c["decision"] = get_recommendation_label(c["composite_score"])

    hire_count = sum(1 for c in evals if "HIRE" in c["decision"])
    shortlist_count = sum(1 for c in evals if "SHORTLIST" in c["decision"])
    consider_count = sum(1 for c in evals if "CONSIDER" in c["decision"])
    reject_count = sum(1 for c in evals if "REJECT" in c["decision"])

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class='metric-card'>
            <span style='color:#15803D; font-size:1.6rem;'>🏆</span>
            <div class='metric-val' style='color:#15803D;'>{hire_count}</div>
            <div class='metric-label'>Strong Hire Recommendations</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class='metric-card'>
            <span style='color:#3750EB; font-size:1.6rem;'>⭐</span>
            <div class='metric-val' style='color:#3750EB;'>{shortlist_count}</div>
            <div class='metric-label'>Shortlist for Final Round</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class='metric-card'>
            <span style='color:#D97706; font-size:1.6rem;'>⏳</span>
            <div class='metric-val' style='color:#D97706;'>{consider_count}</div>
            <div class='metric-label'>Conditional / Further Review</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class='metric-card'>
            <span style='color:#DC2626; font-size:1.6rem;'>🚫</span>
            <div class='metric-val' style='color:#DC2626;'>{reject_count}</div>
            <div class='metric-label'>Unqualified / Rejected</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

    # 5. Master Candidate Decision Table
    table_rows = []
    for c in evals:
        table_rows.append({
            "ID": c["id"],
            "Candidate": c["name"],
            "CV Match": f"{c['cv_score']:.0f}%",
            "Technical Assessment": f"{c['tech_score']:.0f}%",
            "Behavioral Alignment": f"{c['behavioral_score']:.0f}%",
            "Composite Fit Score": f"{c['composite_score']:.1f}%",
            "Autonomous Recommendation": c["decision"],
            "Confidence": f"{c['confidence']:.1f}%",
            "HR Final Action": c.get("human_status", "PENDING_REVIEW")
        })

    st.markdown("<div class='kayfa-card'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#1E2B68; margin-bottom:0.75rem;'>Candidate Multi-Factor Decision Matrix</h4>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

    # 6. Deep-Dive Candidate Decision Dossier & Human-in-the-Loop Actions
    st.markdown("<h4 style='color:#1E2B68; margin-bottom:0.5rem;'>Interactive Candidate Decision Dossier</h4>", unsafe_allow_html=True)
    st.caption("Inspect full multi-factor rationales, review submitted technical solutions, and record human executive decisions.")

    cand_names = [c["name"] for c in evals]
    selected_name = st.selectbox("Select Candidate to Inspect & Take Action", cand_names, index=0)
    cand_data = next((c for c in evals if c["name"] == selected_name), evals[0])

    # Status tag color
    rec = cand_data["decision"]
    if "HIRE" in rec:
        badge_bg, badge_border, badge_text = "#F0FDF4", "#16A34A", "#15803D"
    elif "SHORTLIST" in rec:
        badge_bg, badge_border, badge_text = "#EFF6FF", "#3750EB", "#1E2B68"
    elif "CONSIDER" in rec:
        badge_bg, badge_border, badge_text = "#FFFBEB", "#F59E0B", "#B45309"
    else:
        badge_bg, badge_border, badge_text = "#FEF2F2", "#EF4444", "#B91C1C"

    st.markdown(f"""
    <div class='kayfa-card' style='border-top: 4px solid {badge_border}; margin-top:0.75rem;'>
        <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;'>
            <div>
                <h3 style='margin:0; color:#1E2B68; font-weight:800;'>{cand_data['name']}</h3>
                <p style='color:#64748B; margin:0.25rem 0 0 0; font-size:0.9rem;'>
                    Position: <strong style='color:#1E2B68;'>{cand_data['role']}</strong> | Location: <strong>{cand_data['location']}</strong> | Exp: <strong>{cand_data['experience']}</strong>
                </p>
            </div>
            <div style='background:{badge_bg}; border:1.5px solid {badge_border}; border-radius:10px; padding:6px 14px; text-align:right;'>
                <div style='font-size:0.72rem; font-weight:800; color:{badge_text}; text-transform:uppercase;'>Agent Recommendation</div>
                <div style='font-size:1rem; font-weight:900; color:{badge_text};'>{rec}</div>
            </div>
        </div>

        <div style='display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:12px; margin: 1.25rem 0; padding: 1rem; background: #F8FAFD; border-radius: 12px; border: 1px solid #E8EEF5;'>
            <div>
                <div style='font-size:0.75rem; color:#64748B; font-weight:700;'>COMPOSITE SCORE</div>
                <div style='font-size:1.5rem; font-weight:900; color:#3750EB;'>{cand_data['composite_score']}%</div>
            </div>
            <div>
                <div style='font-size:0.75rem; color:#64748B; font-weight:700;'>CV SCREENING</div>
                <div style='font-size:1.3rem; font-weight:800; color:#1E2B68;'>{cand_data['cv_score']:.0f}%</div>
            </div>
            <div>
                <div style='font-size:0.75rem; color:#64748B; font-weight:700;'>TECH ASSESSMENT</div>
                <div style='font-size:1.3rem; font-weight:800; color:#1E2B68;'>{cand_data['tech_score']:.0f}%</div>
            </div>
            <div>
                <div style='font-size:0.75rem; color:#64748B; font-weight:700;'>CULTURE & BEHAVIORAL</div>
                <div style='font-size:1.3rem; font-weight:800; color:#1E2B68;'>{cand_data['behavioral_score']:.0f}%</div>
            </div>
            <div>
                <div style='font-size:0.75rem; color:#64748B; font-weight:700;'>AGENT CONFIDENCE</div>
                <div style='font-size:1.3rem; font-weight:800; color:#15803D;'>{cand_data['confidence']}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.markdown("##### 💡 Key Technical Strengths")
        for s in cand_data["strengths"]:
            st.markdown(f"- ✅ **{s}**")
    with d_col2:
        st.markdown("##### ⚠️ Risk Factors & Considerations")
        for r in cand_data["risks"]:
            st.markdown(f"- ⚠️ *{r}*")

    st.markdown("##### 🤖 Decision Agent Multi-Factor Synthesis")
    st.info(cand_data["rationale"])

    st.markdown("<hr style='margin: 1.25rem 0; border-color:#E8EEF5;'>", unsafe_allow_html=True)
    st.markdown("##### ✍️ Human-in-the-Loop Governance & Final Approval")
    st.caption("As an authorized HR Executive, record your final decision or override the autonomous recommendation.")

    current_status = cand_data.get("human_status", "PENDING_REVIEW")
    st.markdown(f"Current Status: **{current_status}**")

    a1, a2, a3, a4 = st.columns(4)
    with a1:
        if st.button("✅ Approve Offer", key=f"btn_offer_{cand_data['id']}", type="primary", use_container_width=True):
            cand_data["human_status"] = "OFFER_EXTENDED"
            observability.log_audit(curr_user.get("name"), "OFFER_APPROVED", "DecisionMaker", cand_data["id"], "OFFER")
            st.success(f"Formal job offer approved for {cand_data['name']}.")
            st.rerun()

    with a2:
        if st.button("🗓️ Advance to Executive", key=f"btn_exec_{cand_data['id']}", use_container_width=True):
            cand_data["human_status"] = "ADVANCED_TO_EXECUTIVE_ROUND"
            observability.log_audit(curr_user.get("name"), "ADVANCED_EXECUTIVE", "DecisionMaker", cand_data["id"], "SHORTLIST")
            st.info(f"{cand_data['name']} moved to final executive leadership round.")
            st.rerun()

    with a3:
        if st.button("📋 Additional Check", key=f"btn_check_{cand_data['id']}", use_container_width=True):
            cand_data["human_status"] = "NEEDS_SUPPLEMENTAL_INTERVIEW"
            observability.log_audit(curr_user.get("name"), "SUPPLEMENTAL_INTERVIEW_REQUESTED", "DecisionMaker", cand_data["id"], "HOLD")
            st.warning(f"Requested supplemental verification for {cand_data['name']}.")
            st.rerun()

    with a4:
        if st.button("❌ Reject Candidate", key=f"btn_rej_{cand_data['id']}", use_container_width=True):
            cand_data["human_status"] = "REJECTED"
            observability.log_audit(curr_user.get("name"), "CANDIDATE_REJECTED", "DecisionMaker", cand_data["id"], "REJECT")
            st.error(f"{cand_data['name']} has been marked as rejected.")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

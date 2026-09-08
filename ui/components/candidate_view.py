"""
Detailed Candidate Profile View with Human-in-the-Loop Action Controls.
"""
import streamlit as st
from observability.tracer import observability

def render_candidate_dossier(candidate: dict):
    st.session_state["viewing_candidate_name"] = candidate["name"]
    
    st.markdown(f"""
    <div class='kayfa-card'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h2 style='margin:0; color:#0F172A;'>{candidate['name']}</h2>
                <p style='margin:0.25rem 0; color:#64748B;'>{candidate['email']} • {candidate['phone']} • {candidate['location']}</p>
                <a href='{candidate['linkedin']}' target='_blank' style='font-size:0.85rem; color:#3851E0;'>LinkedIn Profile ↗</a>
            </div>
            <div style='text-align: right;'>
                <span class='badge badge-purple' style='font-size:0.9rem; padding:0.4rem 0.8rem;'>Stage: {candidate['stage']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Candidate Info & Docs
        with st.expander("📄 Candidate Information & Documents", expanded=True):
            c_info1, c_info2 = st.columns(2)
            with c_info1:
                st.write("**Experience:**", candidate["experience"])
                st.write("**Education:**", candidate["education"])
            with c_info2:
                st.write("**Skills:**", ", ".join(candidate["skills"]))
                st.button("📥 Download Uploaded CV (PDF)", key=f"cv_{candidate['id']}")

        # Screening Breakdown
        scr = candidate.get("screening", {})
        with st.expander("🔍 CV Screening Breakdown (CV Agent)", expanded=True):
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Overall Score", f"{scr.get('overall_score', 0)}%")
            m2.metric("Required Skills", f"{scr.get('required_skills', 0)}%")
            m3.metric("Experience Match", f"{scr.get('experience_score', 0)}%")
            m4.metric("Education Match", f"{scr.get('education_score', 0)}%")
            
            st.write("**Identified Strengths:**")
            for s in scr.get("strengths", []):
                st.markdown(f"- <span style='color:#059669;'>✓ {s}</span>", unsafe_allow_html=True)
                
            st.write("**Skill Gaps:**")
            for g in scr.get("gaps", []):
                st.markdown(f"- <span style='color:#DC2626;'>! {g}</span>", unsafe_allow_html=True)

        # Interview Evaluation
        int_data = candidate.get("interview")
        if int_data:
            with st.expander("🎙️ Dual-Track Interview Evaluation (Interviewer Agent)", expanded=True):
                i1, i2, i3 = st.columns(3)
                i1.metric("Technical Score", f"{int_data.get('technical_score')}%")
                i2.metric("HR / Behavioral", f"{int_data.get('hr_score')}%")
                i3.metric("Composite Score", f"{int_data.get('composite_score')}%")
                
                st.write("**Unique Candidate Links:**")
                st.code(f"Technical: {int_data['tech_url']}\nHR Track:  {int_data['hr_url']}")
                st.write(f"Email Status: **{int_data['email_status']}**")

        # Decision Agent Recommendation
        dec = candidate.get("decision")
        if dec:
            with st.expander("⚡ Decision Making Agent Recommendation", expanded=True):
                rec = dec["recommendation"]
                badge = "badge-green" if rec == "SHORTLIST" else "badge-amber" if rec == "CONSIDER" else "badge-red"
                st.markdown(f"**Recommendation:** <span class='badge {badge}' style='font-size:0.9rem;'>{rec}</span> (Confidence: {dec['confidence']}%)", unsafe_allow_html=True)
                st.markdown(f"**Reasoning:** {dec['reasoning']}")
                st.write("**Probing Questions for Hiring Manager:**")
                for q in dec.get("probing_questions", []):
                    st.markdown(f"> *{q}*")

    with col2:
        # HUMAN-IN-THE-LOOP SECTION
        st.markdown("<div class='kayfa-card' style='border-top: 4px solid #3851E0;'>", unsafe_allow_html=True)
        st.markdown("<h4>Human-in-the-Loop Final Decision</h4>", unsafe_allow_html=True)
        st.caption("AI provides recommendations. Human HR has final decision authority.")
        
        st.write(f"Current Recorded Decision: **{candidate['final_human_decision'] or 'Pending Human Review'}**")
        
        hr_notes = st.text_area("HR Manager Notes / Interview Result", placeholder="Enter notes from final human conversation...")
        
        if st.button("✅ Shortlist Candidate", use_container_width=True, type="primary"):
            candidate["stage"] = "SHORTLISTED"
            candidate["final_human_decision"] = "SHORTLISTED"
            observability.log_audit("HR User", "SHORTLIST_CANDIDATE", "Candidate", candidate["id"], "SUCCESS")
            st.success("Candidate marked SHORTLISTED.")
            st.rerun()

        if st.button("📅 Schedule Final Human HR Interview", use_container_width=True):
            candidate["stage"] = "FINAL HR"
            candidate["final_human_decision"] = "FINAL_HR_SCHEDULED"
            observability.log_audit("HR User", "SCHEDULE_FINAL_HR", "Candidate", candidate["id"], "SUCCESS")
            st.info("Moved to Final Human HR Interview.")
            st.rerun()

        if st.button("🎉 Final Decision: HIRED", use_container_width=True):
            candidate["stage"] = "HIRED"
            candidate["final_human_decision"] = "HIRED"
            observability.log_audit("HR User", "FINAL_HIRE", "Candidate", candidate["id"], "HIRED")
            st.success(f"{candidate['name']} is officially HIRED!")
            st.rerun()

        if st.button("❌ Reject Candidate", use_container_width=True):
            candidate["stage"] = "REJECTED"
            candidate["final_human_decision"] = "REJECTED"
            observability.log_audit("HR User", "REJECT_CANDIDATE", "Candidate", candidate["id"], "REJECTED")
            st.error("Candidate marked REJECTED.")
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
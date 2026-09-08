"""
10-Stage Recruitment Kanban Board.
Columns: NEW, SCREENING, SCREENING PASSED, INTERVIEW, INTERVIEW COMPLETED,
AI DECISION, SHORTLISTED, FINAL HR, HIRED, REJECTED.
"""
import streamlit as st

STAGES = [
    "NEW", "SCREENING", "SCREENING PASSED", "INTERVIEW",
    "INTERVIEW COMPLETED", "AI DECISION", "SHORTLISTED",
    "FINAL HR", "HIRED", "REJECTED"
]

def render_kanban_board(candidates: list):
    st.markdown("#### 📋 Recruitment Pipeline Kanban (10 Stages)")
    
    # 5 columns on top row, 5 columns on bottom row for balanced readability
    row1 = st.columns(5)
    row2 = st.columns(5)
    
    for idx, stage in enumerate(STAGES):
        col = row1[idx] if idx < 5 else row2[idx - 5]
        with col:
            cands_in_stage = [c for c in candidates if c.get("stage", "").upper() == stage]
            badge_color = "#3851E0" if "PASSED" in stage or "AI" in stage else "#059669" if "HIRED" in stage or "SHORTLISTED" in stage else "#DC2626" if "REJECTED" in stage else "#64748B"
            
            st.markdown(f"""
            <div style='background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid {badge_color}; border-radius: 8px; padding: 0.5rem 0.75rem; margin-bottom: 0.5rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 0.72rem; font-weight: 800; color: #334155;'>{stage}</span>
                    <span class='badge' style='background:#F1F5F9; color:#475569;'>{len(cands_in_stage)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            for c in cands_in_stage:
                score = c.get("screening", {}).get("overall_score", 0)
                st.markdown(f"""
                <div class='kayfa-card' style='padding: 0.65rem 0.75rem; margin-bottom: 0.5rem; font-size: 0.8rem;'>
                    <strong>{c['name']}</strong><br>
                    <span style='color: #64748B; font-size: 0.75rem;'>{c['experience']} • {c['location']}</span><br>
                    <span class='badge badge-blue' style='margin-top: 0.25rem;'>Score: {score}%</span>
                </div>
                """, unsafe_allow_html=True)
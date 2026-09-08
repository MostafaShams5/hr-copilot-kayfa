"""
Kayfa Academy Candidate Assessment Portal Component.
Provides:
1. Direct Candidate Portal: External landing page for candidate assessment links (?page=assessment)
2. HR/Admin Preview Mode: Interactive testing within the HR Recruitment OS
"""
import time
import streamlit as st
from ui.theme import get_kayfa_logo_html

# Standardized Assessment Question Bank
ASSESSMENT_QUESTIONS = {
    "technical": [
        {
            "id": "T1",
            "title": "System Architecture & Concurrency",
            "text": "In a distributed FastAPI microservice experiencing high concurrent write traffic, which strategy best guarantees idempotency and exactly-once processing without causing distributed deadlocks?",
            "type": "mcq",
            "options": [
                "Distributed locking with TTL leases using Redis Redlock and unique client idempotency keys",
                "Disabling database transactions across background worker threads",
                "Relying on synchronous HTTP retries with zero exponential backoff",
                "Acquiring global exclusive table-level locks on the primary database"
            ],
            "recommendation_hint": "Focus on horizontal scalability, network partition resilience, and short TTL leasing."
        },
        {
            "id": "T2",
            "title": "Database Scaling & Isolation",
            "text": "When scaling a PostgreSQL cluster with high read-to-write ratios (90% reads, 10% writes), what is the optimal pattern to eliminate read contention while preventing stale reads during critical state updates?",
            "type": "mcq",
            "options": [
                "Read replicas with asynchronous streaming replication, routing critical write-followed-by-read queries to the primary node",
                "Running all queries on a single unindexed database instance",
                "Enabling serializable isolation on read-heavy replica nodes",
                "Switching entirely to unpersisted in-memory arrays without write-ahead logging"
            ],
            "recommendation_hint": "Consider read replica lag and session consistency."
        },
        {
            "id": "T3",
            "title": "AI Pipeline & Streaming Performance",
            "text": "Explain how you would architect a resilient streaming pipeline for LLM outputs (Server-Sent Events / SSE) in Python. How would you handle connection drops, token buffering, and backpressure?",
            "type": "text",
            "placeholder": "Describe your architectural approach, protocol choice, client reconnection logic, and error recovery..."
        },
        {
            "id": "T4",
            "title": "Security & Prompt Injection Defenses",
            "text": "Which combination of safeguards provides the most robust multi-layered defense against both direct and indirect prompt injection attacks in a production RAG application?",
            "type": "mcq",
            "options": [
                "Strict input sanitization + dual-agent verification (guardrail model) + tool parameter validation schemas + least-privilege tool access",
                "Simply prepending 'Please do not hack this system' to the system prompt",
                "Allowing direct execution of raw LLM-generated shell commands without validation",
                "Disabling all logging and observability to prevent log injection"
            ],
            "recommendation_hint": "Modern LLM security requires defense in depth across inputs, execution bounds, and outputs."
        },
        {
            "id": "T5",
            "title": "System Design Tradeoffs",
            "text": "Describe a production scenario where you had to make a difficult tradeoff between system latency and data consistency. What metrics did you monitor and what was the outcome?",
            "type": "text",
            "placeholder": "Provide the business context, the technical tradeoff (e.g. CAP theorem), your decision, and key monitoring metrics..."
        }
    ],
    "hr": [
        {
            "id": "H1",
            "title": "Kayfa Mission & Values Alignment",
            "text": "Kayfa Academy is committed to empowering elite talent and accelerating career potential across the region. Why are you interested in joining Kayfa, and how does your career vision align with our mission?",
            "type": "text",
            "placeholder": "Share your motivation, resonance with our mission, and what you hope to achieve at Kayfa..."
        },
        {
            "id": "H2",
            "title": "Navigating Conflicting Priorities",
            "text": "Describe a situation where engineering excellence or architectural perfection conflicted directly with an aggressive business delivery deadline. How did you negotiate and resolve the tradeoff?",
            "type": "text",
            "placeholder": "Describe the context, the stakeholders involved, your communication strategy, and the final result..."
        },
        {
            "id": "H3",
            "title": "Leadership, Ownership & Mentorship",
            "text": "A team member introduces a bug that causes a 20-minute partial outage. As a senior teammate, how do you handle the blameless post-mortem, support the colleague, and ensure preventive safeguards are instituted?",
            "type": "text",
            "placeholder": "Explain your approach to psychological safety, root-cause analysis, and team growth..."
        },
        {
            "id": "H4",
            "title": "Handling Ambiguity",
            "text": "How do you navigate projects where initial product specifications are ambiguous or customer feedback requires an immediate pivot? Give a concrete example from your past experience.",
            "type": "text",
            "placeholder": "Detail your methodology for clarifying requirements, running rapid experiments, and keeping the team aligned..."
        }
    ]
}

def safe_get_query_param(key: str, default: str = "") -> str:
    """Helper to safely read query parameters across Streamlit versions."""
    try:
        # Streamlit 1.30+
        if hasattr(st, "query_params"):
            val = st.query_params.get(key, default)
            if isinstance(val, list):
                return str(val[0]) if val else default
            return str(val) if val is not None else default
    except Exception:
        pass
    
    try:
        # Legacy Streamlit (< 1.30)
        params = st.experimental_get_query_params()
        val = params.get(key, default)
        if isinstance(val, list):
            return str(val[0]) if val else default
        return str(val) if val is not None else default
    except Exception:
        return default

def safe_clear_query_params():
    """Helper to safely clear query parameters across Streamlit versions."""
    try:
        if hasattr(st, "query_params"):
            st.query_params.clear()
            return
    except Exception:
        pass
        
    try:
        st.experimental_set_query_params()
    except Exception:
        pass

def safe_set_query_param(**kwargs):
    """Helper to safely set query parameters across Streamlit versions."""
    try:
        if hasattr(st, "query_params"):
            for k, v in kwargs.items():
                if v is None:
                    if k in st.query_params:
                        del st.query_params[k]
                else:
                    st.query_params[k] = str(v)
            return
    except Exception:
        pass

    try:
        params = st.experimental_get_query_params()
        for k, v in kwargs.items():
            if v is None:
                params.pop(k, None)
            else:
                params[k] = [str(v)]
        st.experimental_set_query_params(**params)
    except Exception:
        pass

def find_candidate_profile(candidate_id: str):
    """Look up candidate from session state or return high-fidelity fallback."""
    candidates = st.session_state.get("candidates", [])
    for c in candidates:
        if c.get("id") == candidate_id or c.get("name") == candidate_id:
            return c
            
    # Default high-fidelity profile
    return {
        "id": candidate_id or "CAND-101",
        "name": "Ahmed Mohamed",
        "role": "Senior Backend Engineer (FastAPI/AI)",
        "email": "ahmed.mohamed@example.com",
        "screening": {"overall_score": 84},
        "interview": {"email_status": "DELIVERED", "eval_status": "PENDING"}
    }

def render_candidate_portal(candidate_id: str = None, track: str = "technical", is_preview: bool = False, on_return=None):
    """
    Renders the complete Kayfa Candidate Assessment Portal.
    Works seamlessly in both standalone candidate view and in-app HR preview mode.
    """
    # Normalize track
    current_track = track if track in ["technical", "hr"] else "technical"
    
    # State keys
    sub_key = f"portal_submitted_{candidate_id}_{current_track}"
    curr_q_key = f"portal_curr_q_{candidate_id}_{current_track}"
    answers_key = f"portal_answers_{candidate_id}_{current_track}"
    
    if curr_q_key not in st.session_state:
        st.session_state[curr_q_key] = 0
    if answers_key not in st.session_state:
        st.session_state[answers_key] = {}
        
    candidate = find_candidate_profile(candidate_id)
    cand_name = candidate.get("name", "Candidate")
    cand_id = candidate.get("id", candidate_id or "CAND-101")
    cand_role = candidate.get("role", "Senior Backend Engineer")
    
    questions = ASSESSMENT_QUESTIONS.get(current_track, ASSESSMENT_QUESTIONS["technical"])
    total_q = len(questions)
    
    # Container
    max_w = "840px" if not is_preview else "100%"
    st.markdown(f"<div style='max-width: {max_w}; margin: 0 auto;'>", unsafe_allow_html=True)
    
    # Header & Branding
    st.markdown(f"<div style='text-align: center; margin-bottom: 16px;'>{get_kayfa_logo_html(width=170)}</div>", unsafe_allow_html=True)
    
    # Preview Toolbar (If HR / Admin mode)
    if is_preview:
        st.markdown("""
        <div style='background: #EFF6FF; border: 1.5px solid #3750EB; border-radius: 12px; padding: 0.75rem 1rem; margin-bottom: 1.25rem; display: flex; align-items: center; justify-content: space-between;'>
            <div style='display:flex; align-items:center; gap:8px;'>
                <span style='font-size:1.2rem;'>👁️</span>
                <span style='font-weight:700; color:#1E2B68; font-size:0.9rem;'>Candidate Portal Live Preview Mode</span>
                <span class='kayfa-pill-blue' style='font-size:0.75rem; padding: 2px 8px;'>HR / Admin Sandbox</span>
            </div>
            <span style='color:#64748B; font-size:0.8rem;'>Internal AI metrics hidden from candidate view</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Interactive Controls for Preview Mode
        p_col1, p_col2, p_col3 = st.columns([2, 2, 1])
        with p_col1:
            all_cands = st.session_state.get("candidates", [])
            cand_names = [c.get("name", f"Candidate {i+1}") for i, c in enumerate(all_cands)] if all_cands else ["Ahmed Mohamed", "Sara Al-Otaibi", "Khaled Mansour"]
            selected_cand = st.selectbox("Candidate Profile", cand_names, index=0, key="portal_preview_cand_select")
            if all_cands:
                cand_match = next((c for c in all_cands if c.get("name") == selected_cand), None)
                if cand_match:
                    candidate = cand_match
                    cand_name = candidate.get("name", selected_cand)
                    cand_id = candidate.get("id", "CAND-101")
        with p_col2:
            track_choice = st.radio("Assessment Track", ["Technical", "HR & Behavioral"], horizontal=True, index=0 if current_track == "technical" else 1, key="portal_preview_track_select")
            new_track = "technical" if track_choice == "Technical" else "hr"
            if new_track != current_track:
                current_track = new_track
                questions = ASSESSMENT_QUESTIONS[current_track]
                total_q = len(questions)
        with p_col3:
            if st.button("🔄 Reset Test", key="btn_reset_portal_test"):
                st.session_state[sub_key] = False
                st.session_state[curr_q_key] = 0
                st.session_state[answers_key] = {}
                st.rerun()

    # Track Title Formatting
    track_title = "Technical Interview Assessment" if current_track == "technical" else "HR & Behavioral Interview Assessment"
    track_badge = "Technical Track" if current_track == "technical" else "Culture & Behavioral"

    # Candidate Dossier Card Header
    st.markdown(f"""
    <div class='kayfa-card' style='margin-bottom: 1.25rem; border-left: 5px solid #3750EB;'>
        <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;'>
            <div>
                <h3 style='margin:0; color:#1E2B68; font-weight:800;'>{track_title}</h3>
                <p style='color:#64748B; margin:0.25rem 0 0 0; font-size:0.88rem;'>
                    Position: <strong style='color:#1E2B68;'>{cand_role}</strong> | Candidate: <strong style='color:#1E2B68;'>{cand_name}</strong>
                </p>
            </div>
            <div style='display:flex; gap:8px; align-items:center;'>
                <span class='kayfa-pill-blue' style='font-size:0.75rem;'>{track_badge}</span>
                <span class='kayfa-pill-outline' style='font-size:0.75rem;'>ID: {cand_id}</span>
            </div>
        </div>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-top:0.85rem; padding-top:0.75rem; border-top:1px solid #E8EEF5; font-size:0.82rem; color:#64748B;'>
            <span>⏱️ <strong>Estimated Duration:</strong> 25 Minutes</span>
            <span>🔒 <strong>Candidate Privacy:</strong> Standardized competency assessment</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CHECK IF ALREADY SUBMITTED
    if st.session_state.get(sub_key, False):
        st.markdown(f"""
        <div style='background:#F0FDF4; border:2px solid #16A34A; border-radius:16px; padding:2rem; text-align:center; margin-bottom:1.5rem;'>
            <span style='font-size:3rem;'>🎉</span>
            <h3 style='color:#15803D; margin:0.75rem 0 0.5rem 0; font-weight:800;'>Assessment Successfully Submitted!</h3>
            <p style='color:#166534; font-size:0.95rem; max-width:550px; margin:0 auto 1.25rem auto;'>
                Thank you, <strong>{cand_name}</strong>! Your responses for the <strong>{track_title}</strong> have been securely recorded.
            </p>
            <div style='display:inline-block; background:#FFFFFF; border:1px solid #BBF7D0; border-radius:8px; padding:0.6rem 1.2rem; font-size:0.85rem; color:#1E2B68;'>
                Reference Number: <strong>KAYFA-EVAL-{cand_id}-{int(time.time()) % 10000}</strong>
            </div>
            <p style='color:#64748B; font-size:0.82rem; margin-top:1rem;'>
                Our Talent & Engineering team will review your submission and provide feedback within 48 business hours.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Summary of recorded answers
        with st.expander("📄 Review Your Submitted Answers"):
            user_answers = st.session_state.get(answers_key, {})
            for idx, q in enumerate(questions):
                st.markdown(f"**Q{idx+1}: {q['title']}**")
                ans = user_answers.get(f"q_{idx}", "*No answer provided*")
                st.info(ans)
                
        if not is_preview:
            if st.button("⬅️ Return to Kayfa Main Page", type="primary"):
                safe_clear_query_params()
                st.session_state["viewing_candidate_portal"] = False
                if on_return:
                    on_return()
                st.rerun()
        return

    # ACTIVE ASSESSMENT FLOW
    curr_idx = min(st.session_state[curr_q_key], total_q - 1)
    q_data = questions[curr_idx]
    
    # Progress Bar
    progress_val = int(((curr_idx + 1) / total_q) * 100)
    p_label1, p_label2 = st.columns([3, 1])
    with p_label1:
        st.write(f"**Question {curr_idx + 1} of {total_q}** &nbsp;·&nbsp; <span style='color:#64748B;'>{q_data['title']}</span>", unsafe_allow_html=True)
    with p_label2:
        st.markdown(f"<div style='text-align:right; font-weight:700; color:#3750EB;'>{progress_val}% Completed</div>", unsafe_allow_html=True)
    st.progress(progress_val)

    # Question Box
    st.markdown(f"""
    <div class='kayfa-card' style='margin: 1rem 0; padding: 1.5rem;'>
        <div style='font-size: 1.05rem; font-weight: 700; color: #1E2B68; margin-bottom: 0.85rem; line-height: 1.5;'>
            {q_data['text']}
        </div>
    """, unsafe_allow_html=True)
    
    answer_field_key = f"answer_{candidate_id}_{current_track}_{curr_idx}"
    saved_answer = st.session_state.get(answers_key, {}).get(f"q_{curr_idx}", "")
    
    if q_data["type"] == "mcq":
        default_index = 0
        if saved_answer in q_data["options"]:
            default_index = q_data["options"].index(saved_answer)
        selected_option = st.radio(
            "Select your solution:",
            q_data["options"],
            index=default_index,
            key=answer_field_key
        )
        st.session_state[answers_key][f"q_{curr_idx}"] = selected_option
    else:
        text_ans = st.text_area(
            "Your Detailed Response:",
            value=saved_answer,
            placeholder=q_data.get("placeholder", "Explain your approach, design tradeoffs, and rationale..."),
            height=160,
            key=answer_field_key
        )
        st.session_state[answers_key][f"q_{curr_idx}"] = text_ans

    st.markdown("</div>", unsafe_allow_html=True)

    # Navigation Controls (Previous, Next, Submit)
    c_prev, c_center, c_next = st.columns([1.5, 2, 1.5])
    
    with c_prev:
        if curr_idx > 0:
            if st.button("⬅️ Previous Question", key=f"btn_prev_{curr_idx}", use_container_width=True):
                st.session_state[curr_q_key] = curr_idx - 1
                st.rerun()
                
    with c_center:
        # Jump selector
        q_labels = [f"Q{i+1}" for i in range(total_q)]
        jump_idx = st.selectbox(
            "Jump to",
            options=range(total_q),
            format_func=lambda i: f"Question {i+1}",
            index=curr_idx,
            key=f"jump_select_{curr_idx}",
            label_visibility="collapsed"
        )
        if jump_idx != curr_idx:
            st.session_state[curr_q_key] = jump_idx
            st.rerun()

    with c_next:
        if curr_idx < total_q - 1:
            if st.button("Next Question ➡️", key=f"btn_next_{curr_idx}", type="primary", use_container_width=True):
                st.session_state[curr_q_key] = curr_idx + 1
                st.rerun()
        else:
            # Last question: Submit
            submit_btn_label = "Submit Interview (Preview)" if is_preview else "🚀 Submit Final Assessment"
            if st.button(submit_btn_label, key=f"btn_submit_{curr_idx}", type="primary", use_container_width=True):
                st.session_state[sub_key] = True
                
                # Update candidate interview evaluation status in session state
                for c in st.session_state.get("candidates", []):
                    if c.get("id") == cand_id or c.get("name") == cand_name:
                        if "interview" not in c or not isinstance(c["interview"], dict):
                            c["interview"] = {}
                        c["interview"]["eval_status"] = "COMPLETED"
                        c["interview"]["submission_time"] = time.strftime("%Y-%m-%d %H:%M")
                        
                st.rerun()

    # Footer navigation back to Kayfa OS (for external link landing)
    if not is_preview:
        st.markdown("<hr style='margin: 2rem 0 1rem 0; border-color:#E8EEF5;'>", unsafe_allow_html=True)
        r1, _ = st.columns([1.5, 3])
        with r1:
            if st.button("🏠 Return to Kayfa Recruitment Portal", key="btn_return_kayfa"):
                safe_clear_query_params()
                st.session_state["viewing_candidate_portal"] = False
                if on_return:
                    on_return()
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

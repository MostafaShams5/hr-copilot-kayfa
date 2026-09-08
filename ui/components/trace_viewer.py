"""
Chronological Step-by-Step Agent Trace Viewer.
START -> Parse CV -> Extract Skills -> Compare JD -> LLM Call -> Calculate Score -> Save Result -> END
"""
import streamlit as st
from observability.tracer import AgentRunRecord

def render_agent_trace(run: AgentRunRecord):
    st.markdown(f"""
    <div class='kayfa-card'>
        <div style='display: flex; justify-content: space-between;'>
            <strong>{run.run_id} — {run.agent_name}</strong>
            <span class='badge badge-green'>{run.status.value}</span>
        </div>
        <div style='color: #64748B; font-size: 0.8rem; margin-top: 0.25rem;'>
            Model: <code>{run.model}</code> • Tokens: {run.total_tokens:,} • Cost: ${run.estimated_cost_usd:.5f} • Latency: {run.latency_ms}ms
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("**Chronological Execution Flow:**")
    st.markdown("🟢 **START**")
    st.markdown("↓")
    
    for idx, step in enumerate(run.steps):
        st.markdown(f"""
        <div style='background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #3851E0; border-radius: 6px; padding: 0.6rem 1rem; margin: 0.4rem 0;'>
            <strong>Step {idx + 1}: {step.step_name}</strong> &nbsp;
            <span class='badge badge-blue' style='font-size:0.7rem;'>Tool: {step.tool}</span> &nbsp;
            <span style='color: #64748B; font-size:0.75rem;'>Duration: {step.duration_ms}ms</span>
            <div style='font-size: 0.78rem; color: #475569; margin-top: 0.25rem;'>
                In: <code>{step.input_meta}</code> | Out: <code>{step.output_meta}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("↓")
        
    st.markdown("🏁 **END (Result Stored in Database)**")
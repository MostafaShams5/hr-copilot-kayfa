
import re
import asyncio
import streamlit as st

try:
    from chatbot.chatbot import ask_kayfa
except ImportError:
    try:
        from chatbot import ask_kayfa
    except ImportError:
        async def ask_kayfa(user_query: str, session_id: str = "default"):
            class ChatReply:
                def __init__(self, reply):
                    self.reply = reply
            return ChatReply(reply="أهلاً بك في أكاديمية كَيْفَ!")

def render_floating_copilot():
    if "copilot_popup" not in st.session_state:
        st.session_state.copilot_popup = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": (
                    "مرحباً بك في **أكاديمية كَيْفَ**! 🎓\n"
                    "أنا مساعدك الذكي للإجابة عن:\n"
                    "• 💼 **الوظائف المتاحة حالياً وشروط التقديم**\n"
                    "• 🏢 **معلومات عن كَيْفَ ورسالتنا في تمكين الكفاءات**\n\n"
                    "كيف يمكنني مساعدتك اليوم؟"
                )
            }
        ]

    # Floating Action Trigger (Bottom Right Corner)
    st.markdown("""
    <div style="position: fixed; bottom: 24px; right: 24px; z-index: 99999;">
    """, unsafe_allow_html=True)
    
    btn_text = "❌ إغلاق المساعد" if st.session_state.copilot_popup else "🤖 وظائف ومعلومات كَيْفَ (Copilot)"
    if st.button(btn_text, key="floating_copilot_fab_trigger"):
        st.session_state.copilot_popup = not st.session_state.copilot_popup
        st.rerun()
        
    st.markdown("</div>", unsafe_allow_html=True)

    # Pop-Up Dialog Window
    if st.session_state.copilot_popup:
        st.markdown("""
        <div style="background: #FFFFFF; border: 2.5px solid #3750EB; border-radius: 20px; padding: 1.25rem; margin-top: 1rem; box-shadow: 0 12px 35px rgba(55, 80, 235, 0.2);">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1.5px solid #E8EEF5; padding-bottom:0.75rem; margin-bottom:0.75rem;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.6rem;">🎓</span>
                    <div>
                        <strong style="color:#1E2B68; font-size:1.05rem; font-weight:800;">مساعد كَيْفَ الذكي (Kayfa Copilot)</strong><br>
                        <span style="font-size:0.78rem; color:#64748B;">دليلك للوظائف المتاحة والتعريف بأكاديمية كَيْفَ</span>
                    </div>
                </div>
                <span class="kayfa-pill-blue" style="font-size:0.75rem;">Kayfa Info & Careers</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        chat_box = st.container(height=280)
        with chat_box:
            for msg in st.session_state.chat_history:
                is_ar = bool(re.search(r'[\u0600-\u06FF]', msg["content"]))
                direction = "rtl" if is_ar else "ltr"
                align = "right" if is_ar else "left"
                with st.chat_message(msg["role"]):
                    st.markdown(f"<div style='direction:{direction}; text-align:{align}; color:#1E2B68; font-size:0.92rem;'>{msg['content']}</div>", unsafe_allow_html=True)

        # Scoped input form
        with st.form("copilot_chat_form", clear_on_submit=True):
            user_msg = st.text_input("Ask about jobs or Kayfa...", placeholder="اسألني عن الوظائف المتاحة أو معلومات عن أكاديمية كيفَ...")
            c_send, _ = st.columns([1, 3])
            with c_send:
                submitted = st.form_submit_button("إرسال / Send 🚀")
                
            if submitted and user_msg:
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                with st.spinner("جاري الاستعلام..."):
                    res = asyncio.run(ask_kayfa(user_msg, session_id="user_careers_session"))
                    st.session_state.chat_history.append({"role": "assistant", "content": res.reply})
                st.rerun()

# Backward compatibility aliases
render_copilot = render_floating_copilot
render_kayfa_copilot = render_floating_copilot
render_chat_copilot = render_floating_copilot
render_copilot_widget = render_floating_copilot

__all__ = [
    "render_floating_copilot",
    "render_copilot",
    "render_kayfa_copilot",
    "render_chat_copilot",
    "render_copilot_widget"
]
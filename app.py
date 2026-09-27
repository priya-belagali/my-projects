import streamlit as st
from generator import LangChainCodeSnippetGenerator

st.set_page_config(page_title="TCS Code Generator", layout="wide")

st.title("⚡ TCS Code Snippet Generator with Memory")
st.caption("Powered by LangChain, Gemini, and SQLite Persistence")

generator = LangChainCodeSnippetGenerator()

# Sidebar: Manage Active Sessions / History
st.sidebar.title("🗂️ Session Storage")
session_id = st.sidebar.text_input("Active Session ID", value="session_1")

if st.sidebar.button("Clear Current Session History"):
    history = generator._get_session_history(session_id)
    history.clear()
    st.sidebar.success(f"Cleared memory for '{session_id}'!")

st.subheader(f"Current Session: `{session_id}`")

# Render active chat history from SQLite DB
history = generator._get_session_history(session_id)
if history.messages:
    st.markdown("### 💬 Conversation & Revision Log")
    for msg in history.messages:
        role = "👤 Requirement / Refinement" if msg.type == "human" else "🤖 Generated Output"
        with st.chat_message(msg.type):
            st.write(f"**{role}**")
            if msg.type == "ai":
                code = msg.content.replace("```python\n", "").replace("```", "").strip()
                st.code(code, language="python")
            else:
                st.write(msg.content)

st.divider()

# Input area for initial generation or follow-up edits
user_input = st.text_area(
    "Enter a requirement OR request a modification:",
    placeholder="e.g., 'Write a function to sort a list of numbers' OR 'Now update the previous function to sort in descending order.'"
)

if st.button("Submit Request", type="primary"):
    if not user_input.strip():
        st.warning("Please enter a valid request.")
    else:
        with st.spinner("Processing request and updating code..."):
            result = generator.generate(user_input, session_id=session_id)

            if result["status"] == "Success":
                st.success("Successfully generated/updated code!")
                st.rerun()
            else:
                st.error(f"Error: {result['validation']}")
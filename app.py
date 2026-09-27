import io
import contextlib
import streamlit as st
from generator import LangChainCodeSnippetGenerator

# Initialize backend engine
@st.cache_resource
def get_generator():
    return LangChainCodeSnippetGenerator()

generator = get_generator()

# Initialize session messages if not present
if "messages" not in st.session_state:
    st.session_state.messages = []

# Define the Modal Window for Testing Code
@st.dialog("🧪 Code Execution Window", width="large")
def run_code_modal(code_to_run: str):
    st.caption("Running Python snippet in isolated context...")
    
    # Display code preview inside an expander
    with st.expander("View Code Being Executed", expanded=False):
        st.code(code_to_run, language="python")

    # Execution buffers
    output_buffer = io.StringIO()
    error_buffer = io.StringIO()
    execution_scope = {}

    try:
        # Redirect stdout and stderr during exec
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(error_buffer):
            exec(code_to_run, execution_scope)
            
        output = output_buffer.getvalue()
        errors = error_buffer.getvalue()

        if output:
            st.success("Execution Completed Successfully")
            st.markdown("**Console Output (`stdout`):**")
            st.code(output, language="text")
        elif errors:
            st.warning("Executed with Warnings/Errors")
            st.code(errors, language="text")
        else:
            st.info("Code executed successfully, but produced no printed output. Ensure your script includes `print()` calls to view results.")

    except Exception as e:
        st.error(f"Runtime Exception: {type(e).__name__}")
        st.code(str(e), language="text")

# App Header
st.title("⚡ AI Code Snippet Generator")

# Render Conversation History First
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # If the message contains generated code, display the execution button
        if msg["role"] == "assistant" and "```python" in msg["content"]:
            try:
                code_snippet = msg["content"].split("```python")[1].split("```")[0].strip()
                if st.button("▶ Test Code", key=f"run_btn_{idx}"):
                    run_code_modal(code_snippet)
            except IndexError:
                pass

# Chat Input (Automatically clears text on submission)
if user_prompt := st.chat_input("Ask for a Python snippet or request modifications..."):
    # Store and render user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Generating snippet..."):
            session_id = st.session_state.get("session_id", "default_session")
            response = generator.generate(user_prompt, session_id=session_id)
            st.markdown(response)
            
            # Extract code and attach test button immediately for new response
            if "```python" in response:
                try:
                    code_snippet = response.split("```python")[1].split("```")[0].strip()
                    if st.button("▶ Test Code", key=f"run_btn_{len(st.session_state.messages)}"):
                        run_code_modal(code_snippet)
                except IndexError:
                    pass

    # Save assistant response to session state
    st.session_state.messages.append({"role": "assistant", "content": response})
              

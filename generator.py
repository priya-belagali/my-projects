import ast
import re
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI


class PythonCodeOutputParser(BaseOutputParser[str]):
    """Extracts code blocks and validates syntax using Python's AST parser."""

    def parse(self, text: str) -> str:
        pattern = r"```python\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL)
        code = match.group(1).strip() if match else text.strip()

        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error on line {e.lineno}: {e.msg}")

        return code


class LangChainCodeSnippetGenerator:
    def __init__(self, model_name: str = "gemini-2.0-flash", db_path: str = "sqlite:///history.db"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.0)
        self.db_path = db_path

        # Prompt with MessagesPlaceholder to maintain chat memory
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert Python developer.\n"
                "Convert user requirements or code modification requests into valid Python code.\n\n"
                "Rules:\n"
                "1. Provide output strictly inside standard ```python ``` markdown blocks.\n"
                "2. Do NOT wrap the response in a JSON object, dictionary, or 'status' key.\n" 
                "3. Include type annotations and brief docstrings.\n"
            )),
            MessagesPlaceholder(variable_name="history"),  # Memory store injection point
            ("human", "{input}")
        ])

        self.parser = PythonCodeOutputParser()
        self.chain = self.prompt | self.llm | self.parser

        # Session history manager linked to SQLite
        self.with_history = RunnableWithMessageHistory(
            self.chain,
            get_session_history=self._get_session_history,
            input_messages_key="input",
            history_messages_key="history"
        )

    def _get_session_history(self, session_id: str):
        """Retrieves or creates an SQL-backed chat history manager for a given session ID."""
        return SQLChatMessageHistory(
            session_id=session_id,
            connection=self.db_path
        )

    def generate(self, user_input: str, session_id: str = "default_session") -> Dict[str, Any]:
        """Generates or updates code based on stored prompt history."""
        try:
            code = self.with_history.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            return {
                "status": "Success",
                "code": code,
                "validation": "Passed Syntax Check"
            }
        except ValueError as e:
            return {
                "status": "Failed",
                "code": "Syntax validation failed.",
                "validation": str(e)
            }


from typing import List, Dict, Any, Optional
from collections import deque
import time

# In-memory session storage
SESSION_DB: Dict[str, deque] = {}

class MemoryManager:
    """
    Manages conversation history with in-memory persistence and rolling window.
    """
    def __init__(self, max_history: int = 8):
        self.max_history = max_history

    def _get_deque(self, session_id: str) -> deque:
        if session_id not in SESSION_DB:
            SESSION_DB[session_id] = deque(maxlen=self.max_history)
        return SESSION_DB[session_id]

    def save_session(self, session_id: str, memory: List[Dict[str, Any]]):
        """
        Overwrite session memory with a provided list.
        """
        d = self._get_deque(session_id)
        d.clear()
        d.extend(memory)

    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Load session memory as a list.
        """
        if session_id not in SESSION_DB:
            return []
        return list(SESSION_DB[session_id])

    def clear_session(self, session_id: str):
        """
        Clear a specific session.
        """
        if session_id in SESSION_DB:
            del SESSION_DB[session_id]

    def append_message(self, session_id: str, role: str, text: str):
        """
        Append a standard chat message (user/assistant/system).
        """
        d = self._get_deque(session_id)
        d.append({"role": role, "content": text})

    def append_tool_result(self, session_id: str, tool_name: str, tool_output: Any):
        """
        Append a tool execution result.
        """
        d = self._get_deque(session_id)
        # Format specifically for Gemini/LLM context
        # "function" role is often used for tool outputs in OpenAI-like schemas,
        # or "tool" role. We'll use "tool" as generic, or "function" if strictly following OpenAI.
        # For Gemini, it's often "function_response". We'll stick to a generic structure 
        # that the controller can adapt if needed, or use "tool" role.
        d.append({
            "role": "tool",
            "name": tool_name,
            "content": str(tool_output)
        })

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Alias for load_session to maintain compatibility.
        """
        return self.load_session(session_id)

    def get_context_string(self, session_id: str) -> str:
        """
        Get history as a formatted string (legacy support).
        """
        history = self.load_session(session_id)
        return "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])

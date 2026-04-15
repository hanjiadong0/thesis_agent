"""
Wrapper service for integrating the external research_agent submodule into
the Thesis Helper backend.

This service keeps the Git submodule largely untouched and adapts it to the
Thesis Helper configuration model, API shape, and runtime environment.
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings


class ResearchAgentService:
    """Adapter around the research_agent LangGraph-based research assistant."""

    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.research_root = self.repo_root / "research_agent"
        self.resources_dir = self.research_root / "resources"
        self.texts_dir = self.research_root / "texts"

        self._core_module = None
        self._tools_module = None
        self._models_module = None
        self._utils_module = None
        self._HumanMessage = None
        self._AIMessage = None
        self._ToolMessage = None

        self._status: Dict[str, Any] = {
            "available": False,
            "submodule_present": self.research_root.exists(),
            "error": None,
            "search_configured": False,
            "providers": {
                "gemini": bool(settings.GEMINI_API_KEY),
                "ollama": bool(settings.OLLAMA_MODEL),
            },
        }

        self._initialize()

    def _initialize(self) -> None:
        """Prepare imports, runtime directories, and configuration."""
        try:
            if not self.research_root.exists():
                raise FileNotFoundError("research_agent submodule directory not found")

            self._configure_environment()
            self._bootstrap_imports()

            self.resources_dir.mkdir(parents=True, exist_ok=True)
            self.texts_dir.mkdir(parents=True, exist_ok=True)

            # Patch the submodule's relative paths to absolute paths so it works
            # when launched from the Thesis Helper backend.
            self._utils_module.local_resource_dir = str(self.resources_dir) + os.sep
            self._utils_module.local_paper_dir = str(self.texts_dir) + os.sep

            self._status["available"] = True
            self._status["search_configured"] = bool(
                os.getenv("GOOGLE_SEARCH_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID")
            )
        except Exception as exc:  # pragma: no cover - runtime safety path
            self._status["available"] = False
            self._status["error"] = str(exc)

    def _configure_environment(self) -> None:
        """Expose Thesis Helper settings using the environment variables expected by the submodule."""
        os.environ.setdefault("MPLBACKEND", "Agg")

        gemini_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or "placeholder-key"
        os.environ["GOOGLE_API_KEY"] = gemini_key

        if settings.GOOGLE_SEARCH_API_KEY:
            os.environ["GOOGLE_SEARCH_API_KEY"] = settings.GOOGLE_SEARCH_API_KEY

        search_engine_id = settings.GOOGLE_SEARCH_ENGINE_ID or settings.GOOGLE_CSE_ID
        if search_engine_id:
            os.environ["GOOGLE_SEARCH_ENGINE_ID"] = search_engine_id
            os.environ["GOOGLE_CSE_ID"] = search_engine_id

    def _bootstrap_imports(self) -> None:
        """Import the submodule code after its runtime environment is configured."""
        research_path = str(self.research_root)
        if research_path not in sys.path:
            sys.path.insert(0, research_path)

        self._core_module = importlib.import_module("agent.core")
        self._tools_module = importlib.import_module("agent.tools")
        self._models_module = importlib.import_module("agent.models")
        self._utils_module = importlib.import_module("agent.utils")

        messages_module = importlib.import_module("langchain_core.messages")
        self._HumanMessage = getattr(messages_module, "HumanMessage")
        self._AIMessage = getattr(messages_module, "AIMessage")
        self._ToolMessage = getattr(messages_module, "ToolMessage")

    def _create_llm(self, ai_provider: Optional[str]):
        """Create an LLM compatible with the research agent tools."""
        provider = (ai_provider or settings.AI_PROVIDER or "ollama").lower()

        if provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required for Gemini research agent mode")

            from langchain.chat_models import init_chat_model

            return init_chat_model(settings.GEMINI_MODEL, model_provider="google_genai")

        if provider == "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=settings.AI_TEMPERATURE,
            )

        raise ValueError(f"Unsupported research agent AI provider: {provider}")

    def _build_agent(self, ai_provider: Optional[str]):
        """Instantiate a configured research agent."""
        llm = self._create_llm(ai_provider)

        # The submodule tools consult the shared models module dynamically, so we
        # override its model handles to align with Thesis Helper's selected provider.
        self._models_module.main_llm_model = llm
        self._models_module.llm_summary_model = llm
        self._models_module.llm_refinement_model = llm
        self._models_module.llm_explainer_model = llm
        self._models_module.llm_infer_difficulty_model = llm

        return self._core_module.Agent(llm, self._tools_module.get_all_tools())

    def get_status(self) -> Dict[str, Any]:
        return dict(self._status)

    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]],
        ai_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a single research-agent turn using stateless chat history."""
        if not self._status["available"]:
            raise RuntimeError(self._status["error"] or "Research agent is not available")

        agent = self._build_agent(ai_provider)
        langgraph_messages = self._to_langchain_messages(history, message)
        result = await asyncio.to_thread(agent.invoke, {"messages": langgraph_messages})
        return self._format_result(result)

    def _to_langchain_messages(self, history: List[Dict[str, str]], message: str):
        messages = []
        for item in history:
            role = item.get("role", "user")
            content = item.get("content", "")
            if not content:
                continue

            if role == "assistant":
                messages.append(self._AIMessage(content=content))
            else:
                messages.append(self._HumanMessage(content=content))

        messages.append(self._HumanMessage(content=message))
        return messages

    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        messages = result.get("messages", [])
        final_answer = ""
        tool_trace: List[Dict[str, Any]] = []
        pending_calls: Dict[str, Dict[str, Any]] = {}
        concept_graph_image: Optional[str] = None

        for message in messages:
            if isinstance(message, self._AIMessage):
                if getattr(message, "tool_calls", None):
                    for tool_call in message.tool_calls:
                        pending_calls[tool_call["id"]] = {
                            "name": tool_call["name"],
                            "args": tool_call.get("args", {}),
                        }
                elif message.content:
                    final_answer = message.content

            elif isinstance(message, self._ToolMessage):
                tool_info = pending_calls.get(message.tool_call_id, {})
                tool_output = str(message.content)
                tool_trace.append(
                    {
                        "name": tool_info.get("name", "tool"),
                        "args": tool_info.get("args", {}),
                        "output": tool_output,
                    }
                )

                if "CONCEPT_GRAPH" in tool_output:
                    image_path = self.resources_dir / "concept_graph_encoding.txt"
                    if image_path.exists():
                        concept_graph_image = image_path.read_text(encoding="utf-8").strip()

        if not final_answer and tool_trace:
            final_answer = tool_trace[-1]["output"]

        return {
            "success": True,
            "reply": final_answer,
            "tool_trace": tool_trace,
            "concept_graph_image": concept_graph_image,
        }

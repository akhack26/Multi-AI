"""
core/app.py

The ISHA application object. This is the single place that wires together
every subsystem described in the architecture:

    User -> ISHA -> Router -> Agent -> Orchestrator -> Backend -> GGUF Model
                                  |
                                  +--> Tool/Action Request -> Permission Layer -> Tool -> Result
                                  |
                                  +--> Memory (short-term + long-term)
                                  |
                                  +--> TTS (optional)

`process_input()` is the one method a launcher (CLI, future GUI, etc.)
needs to call per user message.
"""

from typing import Dict, Optional

from core.config import Config, load_config
from core.logger import get_logger
from ai.orchestrator import Orchestrator
from router.router import Router
from memory.memory_manager import MemoryManager
from voice.tts_engine import TTSEngine
from voice.stt_engine import STTEngine

from agents.chat_agent import ChatAgent
from agents.study_agent import StudyAgent
from agents.coding_agent import CodingAgent
from agents.reasoning_agent import ReasoningAgent
from agents.base_agent import BaseAgent

from tools.base_tool import BaseTool
from tools.file_tools import ReadFileTool, WriteFileTool, ListDirTool, DeleteFileTool
from tools.app_launcher_tool import LaunchAppTool
from tools.system_info_tool import SystemInfoTool
from tools.permission import PermissionManager

log = get_logger("app")

_AGENT_CLASSES = {
    "chat": ChatAgent,
    "study": StudyAgent,
    "coding": CodingAgent,
    "reasoning": ReasoningAgent,
}


class ISHA:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        log.info("Starting ISHA Multi AI (config: %s)", self.config.source_path)

        # --- AI stack -----------------------------------------------------
        self.orchestrator = Orchestrator(self.config)

        # --- Memory ---------------------------------------------------------
        mem_cfg = self.config.get("memory", {}) or {}
        self.memory: Optional[MemoryManager] = None
        if mem_cfg.get("enabled", True):
            self.memory = MemoryManager(
                short_term_turns=mem_cfg.get("short_term_turns", 12),
                persist_long_term=mem_cfg.get("persist_long_term", True),
                max_long_term_entries=mem_cfg.get("max_long_term_entries", 2000),
            )

        # --- Agents -----------------------------------------------------
        enabled_roles = self.config.get("agents.enabled", list(_AGENT_CLASSES.keys()))
        self.default_role = self.config.get("agents.default_agent", "chat")
        self.agents: Dict[str, BaseAgent] = {}
        for role in enabled_roles:
            cls = _AGENT_CLASSES.get(role)
            if cls:
                self.agents[role] = cls(self.orchestrator, self.memory)
        if self.default_role not in self.agents:
            # Always guarantee a working default even if config is malformed.
            self.agents[self.default_role] = ChatAgent(self.orchestrator, self.memory)

        # --- Router -------------------------------------------------------
        self.router = Router(enabled_roles=list(self.agents.keys()), default_role=self.default_role)

        # --- Tools + permission layer --------------------------------------
        tools_cfg = self.config.get("tools", {}) or {}
        self.permissions = PermissionManager(
            require_confirmation_for_dangerous=tools_cfg.get("require_confirmation_for_dangerous", True)
        )
        self.tools: Dict[str, BaseTool] = {
            "read_file": ReadFileTool(),
            "write_file": WriteFileTool(),
            "list_dir": ListDirTool(),
            "delete_file": DeleteFileTool(),
            "system_info": SystemInfoTool(),
            "launch_app": LaunchAppTool(whitelist=tools_cfg.get("app_launch_whitelist", [])),
        }

        # --- Voice ----------------------------------------------------------
        voice_cfg = self.config.get("voice", {}) or {}
        self.tts: Optional[TTSEngine] = None
        if voice_cfg.get("tts_enabled", False):
            self.tts = TTSEngine(
                rate=voice_cfg.get("tts_rate", 175),
                voice_index=voice_cfg.get("tts_voice_index", 0),
            )
        self.stt: Optional[STTEngine] = None
        if voice_cfg.get("stt_enabled", False):
            self.stt = STTEngine()

        log.info("ISHA ready. %s", self.orchestrator.backend_status())

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #
    def process_input(self, text: str, session_id: str = "default", speak: bool = False) -> str:
        """Route text to the right agent, get a reply, optionally speak it."""
        decision = self.router.classify(text)
        agent = self.agents.get(decision.role) or self.agents[self.default_role]
        log.info("-> agent '%s' (confidence=%.2f)", agent.role, decision.confidence)

        reply = agent.handle(text, session_id=session_id)

        if speak and self.tts is not None:
            self.tts.speak(reply)

        return reply

    def call_tool(self, tool_name: str, **kwargs):
        """Directly invoke a named tool through the permission layer."""
        tool = self.tools.get(tool_name)
        if tool is None:
            return f"Unknown tool: {tool_name}. Available: {list(self.tools.keys())}"
        result = self.permissions.execute(tool, **kwargs)
        return result.output if result.success else f"[tool error] {result.error}"

    def model_status(self) -> str:
        return self.orchestrator.model_manager.status_table() + "\n\n" + \
               self.orchestrator.model_manager.missing_report()

    def shutdown(self) -> None:
        self.orchestrator.shutdown()
        log.info("ISHA shut down cleanly.")

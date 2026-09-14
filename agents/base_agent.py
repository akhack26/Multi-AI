"""
agents/base_agent.py

Common base class for all ISHA agents. Each agent is essentially:
  - a role name (matches config/models.json and router/router.py roles)
  - a system prompt defining its persona/specialty
  - a handle() method that builds the message list (system prompt + memory
    context + new user input) and asks the orchestrator to generate a reply.
"""

from typing import List, Optional

from ai.orchestrator import Orchestrator, OrchestratorError
from memory.memory_manager import MemoryManager
from core.logger import get_logger


class BaseAgent:
    role: str = "base"
    system_prompt: str = "You are ISHA, a helpful local AI assistant."
    max_tokens: int = 512
    temperature: float = 0.7

    def __init__(self, orchestrator: Orchestrator, memory: Optional[MemoryManager] = None):
        self.orchestrator = orchestrator
        self.memory = memory
        self.log = get_logger(f"agent.{self.role}")

    def build_messages(self, user_input: str, session_id: str = "default") -> List[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if self.memory is not None:
            for turn in self.memory.get_short_term(session_id):
                messages.append(turn)
        messages.append({"role": "user", "content": user_input})
        return messages

    def handle(self, user_input: str, session_id: str = "default") -> str:
        messages = self.build_messages(user_input, session_id)
        try:
            reply = self.orchestrator.generate_for_role(
                self.role, messages, max_tokens=self.max_tokens, temperature=self.temperature
            )
        except OrchestratorError as e:
            reply = (
                f"[{self.role} agent unavailable]\n{e}\n\n"
                f"Tip: run ISHA's model status check to see exactly what's missing."
            )
            self.log.warning("Generation failed: %s", e)

        if self.memory is not None:
            self.memory.add_turn(session_id, "user", user_input)
            self.memory.add_turn(session_id, "assistant", reply)

        return reply

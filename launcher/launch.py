"""
launcher/launch.py

Interactive command-line entry point for ISHA Multi AI. This is what
launch.bat / launch.sh ultimately runs. Kept simple and dependency-free so
it works even before any optional package (llama-cpp-python, pyttsx3, etc.)
is installed - it will just clearly report what isn't ready yet.
"""

import sys
import os

# Ensure the project root is on sys.path regardless of the working directory
# the .bat/.sh launcher was double-clicked from.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.app import ISHA  # noqa: E402
from core.logger import get_logger  # noqa: E402

log = get_logger("launcher")

BANNER = r"""
 ___ ____  _   _   _
|_ _/ ___|| | | | / \
 | |\___ \| |_| |/ _ \
 | | ___) |  _  / ___ \
|___|____/|_| |_/_/   \_\   Multi AI - Portable Local Assistant
"""

HELP_TEXT = """
Commands:
  /help              Show this help
  /status            Show backend + model status
  /agents            List available agents
  /agent <name>      Force-route the next message to a specific agent
  /tool <name> k=v .. Directly call a tool (e.g. /tool system_info)
  /voice on|off      Toggle speaking replies aloud (requires TTS installed)
  /clear             Clear short-term memory for this session
  /exit              Quit ISHA
"""


def _parse_kv_args(tokens):
    kwargs = {}
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            kwargs[k] = v
    return kwargs


def main():
    print(BANNER)
    print("Type /help for commands. Type a message to chat.\n")

    try:
        isha = ISHA()
    except Exception as e:
        print(f"FATAL: ISHA failed to start: {e}")
        log.exception("Startup failure")
        sys.exit(1)

    print(isha.model_status())
    print()

    forced_agent = None
    speak = False
    session_id = "default"

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting ISHA. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            parts = user_input.split()
            cmd = parts[0].lower()

            if cmd == "/exit":
                break
            elif cmd == "/help":
                print(HELP_TEXT)
            elif cmd == "/status":
                print(isha.orchestrator.backend_status())
                print(isha.model_status())
            elif cmd == "/agents":
                print("Available agents:", ", ".join(isha.agents.keys()))
            elif cmd == "/agent":
                if len(parts) > 1 and parts[1] in isha.agents:
                    forced_agent = parts[1]
                    print(f"Forcing agent: {forced_agent}")
                elif len(parts) > 1 and parts[1] == "auto":
                    forced_agent = None
                    print("Back to automatic routing.")
                else:
                    print("Usage: /agent <name>  or  /agent auto")
            elif cmd == "/tool":
                if len(parts) < 2:
                    print("Usage: /tool <name> key=value ...")
                else:
                    kwargs = _parse_kv_args(parts[2:])
                    print(isha.call_tool(parts[1], **kwargs))
            elif cmd == "/voice":
                if len(parts) > 1 and parts[1] == "on":
                    speak = True
                    print("Voice replies: ON" + ("" if isha.tts and isha.tts.is_available() else
                          " (warning: TTS not available/installed)"))
                elif len(parts) > 1 and parts[1] == "off":
                    speak = False
                    print("Voice replies: OFF")
                else:
                    print("Usage: /voice on|off")
            elif cmd == "/clear":
                if isha.memory:
                    isha.memory.clear_short_term(session_id)
                print("Short-term memory cleared.")
            else:
                print(f"Unknown command: {cmd}. Type /help.")
            continue

        if forced_agent:
            agent = isha.agents[forced_agent]
            reply = agent.handle(user_input, session_id=session_id)
            if speak and isha.tts:
                isha.tts.speak(reply)
        else:
            reply = isha.process_input(user_input, session_id=session_id, speak=speak)

        print(f"ISHA: {reply}\n")

    isha.shutdown()


if __name__ == "__main__":
    main()

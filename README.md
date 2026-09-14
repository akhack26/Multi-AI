# ISHA Multi AI — Portable Local AI Assistant

A standalone, offline-first AI assistant designed to run **directly from a
64 GB USB/pendrive** on any Windows (or Linux/macOS) PC, using local GGUF
models as its brain via llama.cpp — no cloud, no fixed install location, no
hard-coded drive letter or username.

This is a fully separate project from any other "ISHA" you may have — it
was built from scratch to this specification.

```
User → ISHA → Router → Agent (Chat/Study/Coding/Reasoning)
                  ↓
             AI Orchestrator
                  ↓
            Backend Interface
          ┌───────┴────────┐
      llama.cpp          Ollama (optional)
                  ↓
             GGUF Local Models
```

Tool/action requests never bypass safety:

```
User → ISHA → Local AI → Tool/Action Request → Permission/Validation Layer
     → Windows Tool → Result → Local AI → ISHA Response → (optional) TTS
```

---

## 1. What's in this project

```
ISHA_Multi_AI/
├── launch.bat            <- double-click this on Windows
├── launch.sh              <- run this on Linux/macOS
├── main.py                 <- python entry point (launch.bat calls this)
├── core/                    <- paths, config, logging, the ISHA app class
├── ai/                       <- orchestrator + model manager
├── backends/                  <- llama.cpp backend, Ollama backend, base interface
├── agents/                     <- Study / Coding / Reasoning / Chat agents
├── router/                      <- routes user input to the right agent
├── tools/                        <- file ops, app launcher, system info, permission layer
├── memory/                        <- short-term + persisted long-term conversation memory
├── voice/                          <- offline TTS (pyttsx3) + optional STT
├── models/                         <- YOU place GGUF model files here (see models/README.md)
├── config/                         <- config.example.json, models.json (model registry)
├── logs/                           <- runtime logs (rotating)
├── data/                           <- ISHA's working data + long-term memory
├── tests/                          <- automated test suite
├── requirements/requirements.txt
└── README.md                       <- you are here
```

Every path in the codebase is computed relative to the project's own
folder (`core/paths.py`), never a fixed drive letter or a hard-coded
username. Copy the whole `ISHA_Multi_AI` folder to any drive letter, on
any PC, and it works identically.

---

## 2. Quick start

### Step 1 — Copy the project to your pendrive
Extract the ZIP anywhere on your 64 GB USB drive, e.g. `E:\ISHA_Multi_AI\`.

### Step 2 — Install Python (one-time, on each host PC)
You need Python 3.10+ on the host PC (Python itself isn't bundled, since
that would eat a large chunk of a 64GB drive and is already free/preinstalled
on most systems). Get it from https://www.python.org/downloads/ — on
Windows, tick **"Add Python to PATH"** during install.

### Step 3 — Add at least one model
See **models/README.md** or section 4 below. ISHA runs and tells you
clearly what's missing even with zero models installed, but you'll want at
least one (e.g. the `chat` model) to actually talk to it.

### Step 4 — Run it
- **Windows:** double-click `launch.bat`
- **Linux/macOS:** `./launch.sh`

First run automatically creates `config/config.json` from
`config/config.example.json` and installs missing Python packages.

### Step 5 — Talk to it
```
You: explain how photosynthesis works
ISHA: ...
You: /status
You: /exit
```
Type `/help` in the running app for the full command list.

---

## 3. How routing & agents work

ISHA classifies each message with a fast, fully offline keyword-based
router (`router/router.py`) and hands it to one of four agents:

| Agent      | Good for                                        |
|------------|--------------------------------------------------|
| chat       | General conversation (default fallback)          |
| study      | Explaining concepts, summaries, quizzes           |
| coding     | Writing/explaining/debugging code                 |
| reasoning  | Multi-step problem solving, math, planning        |

Each agent uses its **own** GGUF model (configurable in
`config/models.json`), and ISHA only keeps **one model loaded in memory at
a time**, swapping automatically as you move between topics — this is what
keeps RAM usage sane on a modest host PC even though you may have several
models sitting on the USB drive.

Force a specific agent with `/agent coding` (and `/agent auto` to return to
automatic routing).

---

## 4. Installing models

GGUF model files are **not** bundled in this ZIP (they're multiple GB each
and would blow past reasonable download/transfer sizes). Instead:

1. Run `/status` inside ISHA (or just check `config/models.json`) to see
   exactly which filename each agent expects.
2. Download a matching GGUF file — from Hugging Face, search e.g.
   `"Llama-3.2-3B-Instruct-GGUF"` and grab the **Q4_K_M** quantization.
3. Drop it straight into `models/` with the exact expected filename.
4. Restart ISHA (or it re-scans on next `/status`/agent call).

Recommended starter set (all Q4_K_M, ~2-5 GB each, comfortably fits many
copies over on a 64 GB drive):

| Role      | Suggested model                     | Size   |
|-----------|--------------------------------------|--------|
| chat      | Llama-3.2-3B-Instruct                | ~2.0GB |
| study     | Phi-3.5-mini-instruct                | ~2.4GB |
| coding    | Qwen2.5-Coder-3B-Instruct             | ~2.1GB |
| reasoning | Qwen2.5-7B-Instruct                   | ~4.7GB |

You do **not** need all four — any agent whose model is missing will tell
you clearly what to download and where to put it, while the other agents
keep working.

Want a different model? Just edit `config/models.json` — no code changes
needed.

---

## 5. The backend (swappable, replaceable)

The default backend is **llama.cpp** via the `llama-cpp-python` package,
loading GGUF files directly from `models/` — fully offline. An optional
**Ollama** backend is also included for hosts that already run a local
Ollama server; enable it in `config.json` under `backend.ollama.enabled`.

The backend is entirely abstracted behind `backends/base.py` — you can add
a third backend later (e.g. a different runtime) by implementing that
interface, without touching agents, the router, or the orchestrator.

---

## 6. Tools & the permission/safety layer

ISHA can interact with the host PC through a small set of tools:

- `read_file`, `write_file`, `list_dir` — file operations (relative paths
  resolve inside `data/`; absolute paths are allowed but flagged)
- `delete_file` — **always requires confirmation**
- `launch_app` — starts an application — **always requires confirmation**
  (optionally restrict to a whitelist via `config.json` →
  `tools.app_launch_whitelist`)
- `system_info` — read-only OS/CPU/RAM/disk report (never dangerous)

**Design rule respected throughout this project:** the LLM never directly
controls the PC. It can only *request* a tool call. Every dangerous
request passes through `tools/permission.py`, which asks for explicit
confirmation before anything destructive or system-altering happens. A
handful of obviously critical system paths (e.g. `Windows\System32`) are
blocked outright regardless of confirmation.

Call tools directly from the CLI: `/tool system_info` or
`/tool write_file path=notes.txt content=hello`.

---

## 7. Memory

- **Short-term**: the last N turns (configurable, default 12) are kept in
  RAM and fed into every prompt as context.
- **Long-term**: every turn is also appended to a JSON file per session
  under `data/memory/`, so conversation history survives a restart.
  A simple offline keyword search (`MemoryManager.search_long_term`) can
  recall older context without needing any external database.

Clear the current session's short-term memory with `/clear`.

---

## 8. Voice (optional)

- **TTS (text-to-speech)**: offline, via `pyttsx3` (uses the OS's built-in
  voices — SAPI5 on Windows, NSSpeech on macOS, espeak on Linux). Disabled
  by default; enable with `voice.tts_enabled: true` in `config.json`, or
  toggle per-session with `/voice on` / `/voice off`.
- **STT (speech-to-text)**: optional, via `SpeechRecognition` + a
  microphone. Disabled by default (`voice.stt_enabled`). Note: the default
  recognizer used by the bundled code calls Google's free web API, which
  needs internet — swap in an offline engine (e.g. Vosk) inside
  `voice/stt_engine.py` if you want STT to also be 100% offline.

---

## 9. Optional cloud API fallback

If you ever want ISHA to fall back to a cloud model instead of (or as well
as) local inference, `config.json` has an `api` section (disabled by
default) as a placeholder for wiring in a provider of your choice. This is
optional and entirely unused unless you enable and implement it.

---

## 10. Portability rules this project follows

- No absolute paths anywhere in the source — everything resolves from
  `core/paths.py`, which derives the project root from its own file
  location (`__file__`), not the current working directory.
- No hard-coded drive letters (`C:\...`) or usernames anywhere.
- `launch.bat` uses `%~dp0` (the batch file's own folder) for `cd`, so it
  works from any drive letter it's copied to.
- `config.json` (your personal settings) is generated fresh on first run
  from `config.example.json` — never assumed to already exist at a fixed
  path outside the project.
- Model loading always goes through `models/` inside the project folder.

---

## 11. Running the test suite

```bash
python tests/run_tests.py
```

This runs unit tests for path portability, the router's classification
logic, file tools + the permission/confirmation layer, and the memory
manager — all without needing a GGUF model installed.

---

## 12. Troubleshooting

**"No inference backend is currently available"**
`llama-cpp-python` isn't installed, or failed to install. Run:
```
pip install -r requirements/requirements.txt
```
If it tries to compile from source and fails, install a prebuilt wheel for
your platform — check the project's PyPI page / GitHub releases for
CPU-only or CUDA/Metal-accelerated wheel install commands matching your
Python version and OS.

**"Model for role 'X' is not installed"**
You haven't placed the expected GGUF file in `models/` yet. Run `/status`
to see exactly which filename is expected, or check `models/README.md`.

**ISHA is very slow to respond**
You're running a model larger than your host PC's CPU can handle quickly.
Try a smaller model (e.g. drop `reasoning` down to a 3B model), or if the
host PC has a capable GPU, raise `backend.llama_cpp.n_gpu_layers` in
`config.json`.

**TTS says nothing / errors on startup**
`pyttsx3` needs a working native voice engine on the host (usually present
by default on Windows/macOS; on Linux you may need `espeak` installed via
your package manager). TTS failures are non-fatal — ISHA just runs with
voice disabled.

**"Refusing to touch a protected system path"**
This is intentional — a small safety net blocking file tools from writing
to core OS folders (e.g. `Windows\System32`) even with confirmation.

**Antivirus flags `launch.bat` or the Python executable**
This is a known false-positive pattern for portable Python tools running
from removable drives. The project contains no obfuscated code — every
`.py` file is plain, readable source you're welcome to inspect.

**I moved the drive to a different PC and a different drive letter — did
anything break?**
No — that's the whole point of the portability design (see section 10).
If something did break, please check you copied the *entire*
`ISHA_Multi_AI` folder, including `config/` and `core/`.

---

## 13. Extending ISHA

- **Add a new tool**: subclass `tools/base_tool.py:BaseTool`, register it
  in `core/app.py`'s `self.tools` dict.
- **Add a new agent**: subclass `agents/base_agent.py:BaseAgent`, add a
  role entry to `config/models.json`, register the class in
  `core/app.py`'s `_AGENT_CLASSES`, and add keywords to `router/router.py`.
- **Add a new backend**: implement `backends/base.py:BackendBase`, register
  it in `ai/orchestrator.py`'s `_BACKEND_REGISTRY`.

---

## 14. License / model licensing note

This project's source code is provided for your own personal use. GGUF
models you download separately carry their own licenses set by their
respective creators (e.g. Meta's Llama license, Microsoft's Phi license,
Alibaba's Qwen license) — check each model's license page before use.

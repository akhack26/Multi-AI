# models/ folder

This folder is where you place the GGUF model files ISHA loads for local,
offline inference. It ships **empty** on purpose — GGUF files are multiple
gigabytes each and must not be bundled into the project ZIP.

## What ISHA expects here

ISHA reads `config/models.json` to know which exact filename each agent
role needs. Run ISHA and type `/status`, or just look at
`config/models.json`, to see the current list. As of this build:

| Role      | Expected filename                          | Approx size |
|-----------|---------------------------------------------|-------------|
| chat      | `llama-3.2-3b-instruct-q4_k_m.gguf`          | ~2.0 GB     |
| study     | `phi-3.5-mini-instruct-q4_k_m.gguf`          | ~2.4 GB     |
| coding    | `qwen2.5-coder-3b-instruct-q4_k_m.gguf`      | ~2.1 GB     |
| reasoning | `qwen2.5-7b-instruct-q4_k_m.gguf`            | ~4.7 GB     |

Total for all four: well under 15 GB, leaving plenty of room on a 64 GB
drive. **You do not need all four** — ISHA will simply tell you an agent's
model is missing (and where to get it) if you skip one; the other agents
keep working normally.

## How to add a model

1. Download the GGUF file (see "Where to get models" below).
2. Rename it to match the filename in the table above (or edit
   `config/models.json` to match whatever filename you downloaded).
3. Drop it directly in this folder — no subfolders needed:
   ```
   ISHA_Multi_AI/models/llama-3.2-3b-instruct-q4_k_m.gguf
   ```
4. Run ISHA. It re-scans this folder on every startup.

## Where to get models

Any GGUF-format model works, as long as it fits the role's context length
and your host PC's RAM. Good sources:

- https://huggingface.co (search for the model name + "GGUF" — e.g.
  "Llama-3.2-3B-Instruct-GGUF"). Prefer well-known repackagers such as
  `bartowski` or `QuantFactory` for reliable quantizations.
- Pick the **Q4_K_M** quantization unless you have a strong reason to use
  a different one — it's the standard balance of quality vs. size/speed
  for a portable setup like this.

## Using a different / custom model

Just edit `config/models.json`: change the `file` field for the role you
want to swap, point it at your new filename, and update the other fields
(`display_name`, `approx_size_gb`, `context_length`) to match. No code
changes required — the model manager and orchestrator read this file at
startup.

## Swapping instead of stacking

ISHA loads only **one** model into memory at a time (per active agent) and
swaps automatically when you switch agents/topics. This is intentional: it
keeps RAM usage manageable on the host PC regardless of how many GGUF files
you've collected in this folder.

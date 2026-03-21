"""
LLM wrapper for therapy sessions.
Loads expert-edited prompts + shared framework context,
then calls Gemini directly via google-genai SDK.
"""

import os
from pathlib import Path
from typing import Any, Literal

from app.data.prompt_repo import get_active_prompt
from app.state.session_machine import WStep

# ─── Gemini SDK ────────────────────────────────────────────────────────────────

try:
    import google.genai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


PROMPT_KEY_MAP = {
    "W1":  "w1_open_gate",
    "W2":  "w2_read_c",
    "W3":  "w3_read_d",
    "W4":  "w4_read_e",
    "W4b": "w4b_compare_f",
    "W5":  "w5_read_g",
    "W6":  "w6_read_h",
    "W7":  "w7_synthesize",
}


def _load_shared(prompt_key: str) -> str:
    """Load a shared prompt, falling back to file read if not in DB."""
    try:
        return get_active_prompt(prompt_key)["content"]
    except KeyError:
        # Fallback: try to read from file
        shared_dir = Path(__file__).parent.parent / "prompts" / "shared"
        filename = prompt_key.replace("shared/", "") + ".md"
        fpath = shared_dir / filename
        if fpath.exists():
            return fpath.read_text(encoding="utf-8")
        return ""


def build_therapy_system_prompt(
    w_step: WStep,
    mode: str,
    channel_context: dict | None = None,
) -> str:
    """
    Build the full system prompt for a therapy session step.

    Structure:
    [Step prompt from DB]
    ---
    ## Shared Framework Context
    [7 Kênh]
    [4 Modes]
    [6A Actions]
    [Luật 6A]
    ---
    ## Current Session Context
    [Mode label + axis]
    [Optional: channel state captured so far]
    """
    step_key = PROMPT_KEY_MAP.get(w_step.value, w_step.value.lower())

    try:
        step_prompt = get_active_prompt(step_key)["content"]
    except KeyError:
        step_prompt = f"[Prompt '{step_key}' not found in DB. Using placeholder.]"

    # Shared context
    channel_defs  = _load_shared("shared/channel_definitions")
    modes_doc    = _load_shared("shared/modes")
    six_a_doc    = _load_shared("shared/6a_actions")

    # Session context
    mode_labels = {
        "A": "Mode A — Triệu chứng / Mất điều hòa",
        "B": "Mode B — Ý nghĩa / Cấu trúc",
        "C": "Mode C — Tích hợp sâu",
        "E": "Mode E — Quan hệ / Hệ thống",
    }
    mode_context = mode_labels.get(mode, mode_labels["B"])

    # Optional channel state summary
    channel_summary = ""
    if channel_context:
        lines = ["## Session Channel State So Far"]
        for k, v in channel_context.items():
            if v and k in ("C", "D", "E", "F", "G", "H"):
                lines.append(f"- **{k}**: {str(v)[:200]}")
        channel_summary = "\n".join(lines)

    return f"""{step_prompt}

---

## Shared Framework Context

### 7 Kênh Đọc

{channel_defs}

### 4 Mode Vận Hành

{modes_doc}

### 6A — Sáu Họ Hành Động

{six_a_doc}

---

## Current Session Context

**Bước hiện tại:** {w_step.value} — {w_step.name}
**Mode:** {mode_context}

{channel_summary}
"""


def call_model_therapy(
    provider: str,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    w_step: WStep,
) -> str:
    """
    Call Gemini for a therapy session.
    Builds conversation history + system instruction, then calls Gemini directly.
    """
    if not GEMINI_AVAILABLE:
        raise RuntimeError(
            "google-genai not installed. Run: pip install google-genai"
        )

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")

    # Configure Gemini client
    client = genai.Client(api_key=api_key)

    # Build Gemini-compatible message history
    # Gemini uses: parts (text) + role (user/model)
    # System instruction is passed separately via contents=[]
    gemini_messages = []

    # System instruction as a model instruction
    system_part = {"text": system}

    # Convert message history
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_messages.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })

    # Call Gemini with system instruction
    # gemini-2.0-flash is free tier, good for Vietnamese
    model_name = model or "gemini-2.0-flash"

    response = client.models.generate_content(
        model=model_name,
        contents=gemini_messages,
        config={
            "system_instruction": {"parts": [{"text": system}]},
        },
    )

    return response.text

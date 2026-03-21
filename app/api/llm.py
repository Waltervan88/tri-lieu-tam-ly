"""
LLM wrapper for therapy sessions — OPTIMIZED for token efficiency.
Strategy:
  1. Framework context loaded ONCE per session (stored in st.session_state)
  2. Only the W-step prompt + session summary sent each request
  3. Conversation history windowed to last 4 turns max
  4. System prompt trimmed to essentials
"""

import os
from pathlib import Path

from app.data.prompt_repo import get_active_prompt
from app.state.session_machine import WStep

# ─── Gemini SDK ────────────────────────────────────────────────────────────────

try:
    from google import genai
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

# ─── Framework context (loaded ONCE per session) ───────────────────────────────

def _load_shared(prompt_key: str) -> str:
    """Load shared prompt, fallback to file."""
    try:
        return get_active_prompt(prompt_key)["content"]
    except KeyError:
        shared_dir = Path(__file__).parent.parent / "prompts" / "shared"
        filename = prompt_key.replace("shared/", "") + ".md"
        fpath = shared_dir / filename
        if fpath.exists():
            return fpath.read_text(encoding="utf-8")
        return ""


def build_framework_context() -> str:
    """
    Build the FIXED framework context (loaded once per session).
    This goes into st.session_state.framework_context — NOT sent every request.
    Only contains the ESSENTIAL framework reference.
    """
    # Load minimal reference docs
    channel_defs = _load_shared("shared/channel_definitions")
    six_a_doc    = _load_shared("shared/6a_actions")

    return f"""## 7 Kênh (Reference — nhớ khi cần)

{channel_defs}

## 6A Actions (Reference)

{six_a_doc}
"""


def build_system_prompt(w_step: WStep, mode: str,
                       channel_context: dict | None = None,
                       framework_context: str | None = None,
                       prev_summary: str | None = None,
                       user_progress: dict | None = None) -> str:
    """
    Build a MINIMAL system prompt for THIS request only.
    - Step-specific instructions (W1-W7)
    - Mode label
    - Longitudinal user context (from user_progress table)
    - Session channel state (condensed)
    - Very brief framework reference (loaded once from session)
    """
    step_key = PROMPT_KEY_MAP.get(w_step.value, w_step.value.lower())

    try:
        step_prompt = get_active_prompt(step_key)["content"]
    except KeyError:
        step_prompt = f"[Prompt '{step_key}' not found]"

    # Mode label
    mode_labels = {
        "A": "Mode A — Triệu chứng / Mất điều hòa (H→C/D→A)",
        "B": "Mode B — Ý nghĩa / Cấu trúc (F→D/E→G→A)",
        "C": "Mode C — Tích hợp sâu",
        "E": "Mode E — Quan hệ / Hệ thống",
    }
    mode_context = mode_labels.get(mode, mode_labels["B"])

    # Longitudinal user context — from user_progress table
    user_ctx = ""
    if user_progress:
        h_val = user_progress.get("h_presence", 5.0)
        channel_notes = []
        channel_labels = {
            "c_raw":       "Hiện tượng (C)",
            "d_loops":     "Dòng & Vòng lặp (D)",
            "e_layers":    "Tầng & Bậc (E)",
            "f_patterns":  "Khuôn lệch (F)",
            "g_awareness": "Tỉnh biết (G)",
        }
        for key, label in channel_labels.items():
            val = user_progress.get(key, "")
            if val:
                channel_notes.append(f"- {label}: {val[:120]}...")

        if channel_notes or h_val:
            notes_block = "\n".join(channel_notes)
            user_ctx = f"""
## Ngữ cảnh người dùng (lịch sử)
H-presence hiện tại: {h_val}/10
{notes_block}
*Thông tin trên phản ánh xu hướng chung. Đánh giá linh hoạt theo hiện tại.*
"""

    # Channel state summary (max 300 chars per channel)
    channel_summary = ""
    if channel_context:
        lines = ["## Tình trạng kênh"]
        for k, v in channel_context.items():
            if v and k in ("C", "D", "E", "F", "G", "H"):
                lines.append(f"- {k}: {str(v)[:300]}")
        channel_summary = "\n".join(lines)

    # Previous summary (what happened last few turns)
    prev = f"\n## Tóm tắt trước đó\n{prev_summary}\n" if prev_summary else ""

    return f"""{step_prompt}

## Ngữ cảnh phiên

**Bước hiện tại:** {w_step.value}
**Mode:** {mode_context}
{prev}
{channel_summary}
{user_ctx}{f"\n## Framework tham chiếu\n{framework_context}" if framework_context else ""}
"""


def call_model_therapy(
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    w_step: WStep,
) -> str:
    """
    Call Gemini with OPTIMIZED token usage:
    - System prompt is MINIMAL (per-request)
    - Messages are WINDOWED (last 4 turns only)
    """
    if not GEMINI_AVAILABLE:
        raise RuntimeError("google-genai not installed.")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")

    client = genai.Client(api_key=api_key)
    model_name = model or "gemini-2.0-flash"

    # ── Window messages: only keep last 4 turns ──────────────────────────────
    # Each "turn" = user msg + assistant response
    # Keep last 4 full turns + the new user message (if not already included)
    MAX_TURNS = 4
    windowed_msgs = _window_messages(messages, max_turns=MAX_TURNS)

    # ── Build Gemini contents ───────────────────────────────────────────────
    gemini_contents = []
    for msg in windowed_msgs:
        role = "user" if msg["role"] == "user" else "model"
        gemini_contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })

    config = genai.types.GenerateContentConfig(
        system_instruction=system,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=gemini_contents,
        config=config,
    )

    return response.text


def _window_messages(messages: list[dict], max_turns: int) -> list[dict]:
    """
    Keep only the last N complete turns (user + assistant pairs).
    If odd number, the last unpaired user msg is kept.
    """
    if len(messages) <= max_turns * 2:
        return messages

    # Take last max_turns pairs + potential unpaired last user msg
    paired   = messages[:-1]  # everything except last
    last_msg = messages[-1]

    # Keep last max_turns*2 from paired + last msg
    return paired[-(max_turns * 2):] + [last_msg]


def summarize_history(messages: list[dict], max_chars: int = 600) -> str:
    """
    Condense conversation history into a brief paragraph.
    Used as prev_summary in the system prompt for context continuity.
    """
    if not messages:
        return ""

    turns = []
    for i in range(0, len(messages) - 1, 2):
        user_txt = messages[i]["content"][:150]
        ai_txt  = messages[i + 1]["content"][:150]
        turns.append(f"User: {user_txt}... → AI: {ai_txt}...")

    # Take last 3 turns
    recent = turns[-3:]
    return f" ({len(messages)//2} turns total) " + " | ".join(recent)

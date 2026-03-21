"""
Mode Router — determines which operating mode (A/B/C/E) to use.
Mode is re-evaluated after each W-step as H may shift.
"""

from typing import Optional


def determine_mode(channel_state: dict, progress: dict) -> str:
    """
    Return 'A' | 'B' | 'C' | 'E'.

    Mode A — symptom / dysregulation (H→C/D→A axis)
      Triggers: H < 4 (low presence/containment)

    Mode E — relational / systemic (Giữa / Ngoài field)
      Triggers: language indicating relational/systemic dynamics
      (detected via channel_state['giua_ngoai'] flag set by LLM)

    Mode C — deep integration / transpersonal
      Triggers: G sufficient + F aligned + H >= 7

    Mode B — meaning / structure (F→D/E→G→A, H-anchored)
      Default fallback
    """
    h      = float(progress.get("h_presence", 5.0))
    g      = progress.get("g_awareness", "") or ""
    f_khat = int(progress.get("f_khat_chhet", 0))

    # ── Mode A: dysregulation ────────────────────────────────────────────────
    if h < 4:
        return "A"

    # ── Mode E: relational / systemic ───────────────────────────────────────
    if channel_state.get("giua_ngoai"):
        return "E"

    # ── Mode C: deep integration ────────────────────────────────────────────
    g_sufficient  = bool(g and len(g) >= 40)
    f_aligned      = f_khat == 0  # 0 = khớp
    if g_sufficient and f_aligned and h >= 7:
        return "C"

    # ── Mode B: default ──────────────────────────────────────────────────────
    return "B"


def mode_summary(mode: str) -> dict:
    """
    Return a dict with human-readable description and axis for each mode.
    Used in the therapy chat UI header.
    """
    summaries = {
        "A": {
            "label": "Mode A — Triệu chứng / Mất điều hòa",
            "axis":  "H → C/D → A",
            "note":  "Ưu tiên THÂN & NHỊP. Không đào sâu F/G.",
        },
        "B": {
            "label": "Mode B — Ý nghĩa / Cấu trúc",
            "axis":  "F → D/E → G → A (neo H)",
            "note":  "Đọc khuôn, dòng, tầng. Có neo hiện diện.",
        },
        "C": {
            "label": "Mode C — Tích hợp sâu",
            "axis":  "H + G + F đủ → đi transpersonal",
            "note":  "Chỉ khi H≥7, G đủ, F khớp. Không dùng sớm.",
        },
        "E": {
            "label": "Mode E — Quan hệ / Hệ thống",
            "axis":  "Giữa / Ngoài → D-loop → repair",
            "note":  "Thiên về mối quan hệ, ranh giới, thiết kế điều kiện.",
        },
    }
    return summaries.get(mode, summaries["B"])

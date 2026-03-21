"""
Workflow Decider — decides which W-steps run in a session.
Not all 7 steps run every time. Determined by "dữ liệu sống" (user progress).
"""

from typing import Optional

from app.state.session_machine import WStep


def decide_session_plan(
    progress: dict,
    last_w: Optional[str],
) -> list[WStep]:
    """
    Decide which W-steps to run for this session based on user progress.

    Rules:
    - W1 always runs (open gate)
    - Mode A (H < 4): dysregulated — skip deep work, go W2→W3→W6→W7
    - Mode B (default): W2 always, then D/E/F/G based on what's populated
    - W4b only when F is not aligned (kẹt or trói)
    - W5 only when G is blank or very thin
    - W6+W7 always run once C is populated
    """
    plan = [WStep.W1]  # Always open gate

    h      = float(progress.get("h_presence", 5.0))
    g_raw  = progress.get("g_awareness", "") or ""
    f_khat = int(progress.get("f_khat_chhet", 0))
    d_loops = progress.get("d_loops", "") or ""
    e_layers = progress.get("e_layers", "") or ""

    # ── Mode A: symptom / dysregulation ──────────────────────────────────────
    if h < 4:
        # Short path: W1 → W2 → W3 → W6 → W7
        # H is too low for deep work (F/G reading)
        plan.extend([WStep.W2, WStep.W3])
        plan.extend([WStep.W6, WStep.W7])
        return plan

    # ── Mode B / C / E: full path with conditional skips ───────────────────
    # W2 always runs — need fresh C data
    plan.append(WStep.W2)

    # D needs reading if never captured or was last session's focus
    if not d_loops or last_w == "W3":
        plan.append(WStep.W3)

    # E needs reading if never captured or was last session's focus
    if not e_layers or last_w == "W4":
        plan.append(WStep.W4)

    # W4b (F comparison) only when frame is misaligned
    if f_khat != 0:  # 1=kẹt or 2=trói
        plan.append(WStep.W4b)

    # G needs reading if blank or very thin
    if not g_raw or len(g_raw) < 40:
        plan.append(WStep.W5)

    # W6 + W7 always run once C is populated
    plan.extend([WStep.W6, WStep.W7])
    return plan


def estimate_session_depth(plan: list[WStep]) -> str:
    """
    Human-readable label for how deep this session is likely to go.
    Used in the UI header to set user expectations.
    """
    steps = set(s.value for s in plan)

    if WStep.W4b in steps and WStep.W5 in steps:
        return "Sâu — có đối chiếu khuôn lệch"
    elif WStep.W5 in steps:
        return "Trung bình — đọc tỉnh biết"
    elif WStep.W3 in steps:
        return "Nhẹ — đọc dòng & hiện tượng"
    elif steps == {"W1"}:
        return "Khởi đầu — mở cổng"
    else:
        return "Tổng hợp"

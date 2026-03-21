"""
W7 Synthesize — generates 6A output, homework, and session indicators.
Applies Luật 6A based on captured channel state.
"""

import json
from datetime import datetime, timedelta
from typing import List, Tuple

from app.data.db import insert_homework


def generate_6a_and_homework(
    channel_state: dict,
    mode: str,
) -> Tuple[list, list, dict]:
    """
    Generate 6A actions + homework assignments based on Luật 6A.

    Luật 6A priority:
      H thấp (<4)     → THÂN / NHỊP
      G mờ / trống   → SÁNG
      F trói (=2)    → NGHĨA + SÁNG
      D kẹt          → VIỆC + SÁNG
      Giữa rối       → GẮN + dựng H
      Mặc định       → NGHĨA + THÂN

    Returns:
      (actions_6a, homework, indicators)
    """
    h        = float(channel_state.get("H") or channel_state.get("h_presence") or 5.0)
    g        = channel_state.get("G") or channel_state.get("g_awareness") or ""
    f_khat   = int(channel_state.get("f_khat_chhet") or 0)
    d_loops  = channel_state.get("D") or channel_state.get("d_loops") or ""
    f_patterns = channel_state.get("F") or channel_state.get("f_patterns") or ""
    c_raw    = channel_state.get("C") or channel_state.get("c_raw") or ""

    actions_6a: List[Tuple[str, str, str]] = []  # (action_letter, dose, description)

    # ── Apply Luật 6A in priority order ─────────────────────────────────────

    if h < 4:
        # Mode A path: prioritise THÂN + NHỊP
        actions_6a.extend([
            ("THÂN",  "primary",
             "Kết nối thân thể — nhận biết cơ thể, hơi thở, tư thế. "
             "Đặt tay lên ngực, thở sâu 4-7-8, nhận biết cảm giác trong cơ thể."),
            ("NHỊP",  "secondary",
             "Thiết lập lại nhịp sinh học — giấc ngủ đúng giờ, bữa ăn đúng giờ, "
             "vận động nhẹ mỗi ngày. Ghi lại chu kỳ giấc ngủ và bữa ăn."),
        ])

    elif not g or len(g) < 20:
        # G mờ → SÁNG
        actions_6a.extend([
            ("SÁNG",  "primary",
             "Chiếu sáng nhận thức — dành 5 phút mỗi sáng viết lại điều vừa nhớ được "
             "từ buổi trị liệu. Đặt câu hỏi: Điều gì đang thật sự xảy ra?"),
            ("NGHĨA", "secondary",
             "Tìm ý nghĩa ẩn sau dữ liệu sống hôm nay. "
             "Ghi chú: sự kiện nào khiến bạn cảm thấy như thế nào?"),
        ])

    elif f_khat == 2:
        # F trói → NGHĨA + SÁNG
        actions_6a.extend([
            ("NGHĨA", "primary",
             f"Phá vỡ khuôn mẫu ràng buộc đang chi phối. "
             f"Nhận diện: {f_patterns[:60] if f_patterns else 'khuôn đang hoạt động'} "
             f"có đang phục vụ bạn không?"),
            ("SÁNG",  "secondary",
             "Chiếu sáng góc nhìn mới: điều gì sẽ khác nếu bạn không bị khuôn này chi phối?"),
        ])

    elif "kẹt" in d_loops.lower() or "lặp" in d_loops.lower():
        # D kẹt → VIỆC + SÁNG
        actions_6a.extend([
            ("VIỆC", "primary",
             f"Hành động nhỏ để phá vỡ vòng lặp. "
             f"Vòng lặp nhận diện: {d_loops[:60] if d_loops else 'đang chạy'}. "
             f"Làm một điều KHÁC BẤT KỲ khi vòng lặp bắt đầu."),
            ("SÁNG",  "secondary",
             "Nhận diện khi nào vòng lặp bắt đầu. Ghi lại 3 lần gần nhất nó xuất hiện."),
        ])

    else:
        # Default: NGHĨA + THÂN
        actions_6a.extend([
            ("NGHĨA", "primary",
             "Khám phá ý nghĩa từ dữ liệu buổi hôm nay. "
             "Điều gì đang lặp lại trong đời sống bạn? Nó có từ khi nào?"),
            ("THÂN",  "secondary",
             "Thực hành ý thức thân thể — scan cơ thể 5 phút/ngày, "
             "nhận biết nơi cảm xúc đang ở trong cơ thể."),
        ])

    # ── GẮN nền — always present ───────────────────────────────────────────
    actions_6a.append((
        "GẮN",
        "background",
        "Duy trì kết nối — gửi một tin nhắn hoặc gọi điện cho người thân "
        "mà bạn tin tưởng trong tuần này. Không cần nói gì sâu — chỉ cần kết nối.",
    ))

    # ── Build homework list (exclude GẮN from homework, keep as session note) ──
    homework = [
        {
            "assignment": a[2],
            "dose": a[1],
            "action_letter": a[0],
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        }
        for a in actions_6a
        if a[1] != "background"
    ]

    # ── Session indicators ──────────────────────────────────────────────────
    indicators = {
        "h_level": h,
        "g_length": len(g),
        "f_khat": f_khat,
        "mode": mode,
        "channels_read": [
            k for k, v in channel_state.items()
            if v and k in ("C", "D", "E", "F", "G", "H")
        ],
        "c_length": len(c_raw),
    }

    return actions_6a, homework, indicators


def persist_homework(
    user_id: str,
    session_id: str,
    homework: list,
) -> None:
    """Insert homework assignments into the database."""
    for hw in homework:
        insert_homework(
            user_id=user_id,
            session_id=session_id,
            assignment=hw["assignment"],
            dose=hw["dose"],
            action_letter=hw["action_letter"],
            due_date=hw.get("due_date"),
        )


def build_session_summary(
    channel_state: dict,
    mode: str,
    actions_6a: list,
    indicators: dict,
) -> str:
    """Build a one-paragraph session summary for the user."""
    h = float(channel_state.get("H") or 5.0)
    c = (channel_state.get("C") or "")[:100]
    d = (channel_state.get("D") or "")[:80]
    f_khat = int(channel_state.get("f_khat_chhet") or 0)
    f_status = {0: "khớp", 1: "kẹt", 2: "trói"}.get(f_khat, "chưa rõ")

    summary = (
        f"Buổi trị liệu kết thúc ở Mode {mode}. "
        f"Hiện tượng chính: {c or '...'}. "
        f"Dòng lặp: {d or '...'}. "
        f"Khuôn hiện trạng: {f_status}. "
        f"H-hiện-diện: {h:.1f}/10. "
        f"Hành động ưu tiên: {actions_6a[0][0] if actions_6a else '—'}."
    )
    return summary

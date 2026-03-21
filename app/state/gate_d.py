"""
Gate D — Safety layer (hard stop).
Rule-based keyword detection runs SYNCHRONOUSLY before any LLM call.
"""

from typing import Tuple

# ─── Keyword lists ────────────────────────────────────────────────────────────
# These are intentionally broad to catch variants. Expert reviews & expands.

SUICIDE_KEYWORDS = [
    "tự tử", "tự sát", "giết mình", "end my life", "kill myself",
    "muốn chết", "want to die", "wish i were dead", "bỏ cuộc đời",
    "không muốn sống nữa", "not want to live", "hết muốn sống",
    "tôi không muốn sống", "end it all", "终结", "自杀",
    "mình nên chết", "best if i die", "muốn ra đi", "đi theo cái chết",
]

HARM_KEYWORDS = [
    "tự làm đau", "self-harm", "self harm", "cut myself",
    "hurt myself", "tổn thương bản thân", "tự gây thương tích",
    "self-injury", "slashing", "cutting", "harm myself",
    "làm đau chính mình", "tự hại", "tự ngược", "tự dội",
]

VIOLENCE_KEYWORDS = [
    "giết người", "kill them", "kill him", "kill her",
    "hurt them", "hurt others", "violence", "bạo lực",
    "gây thương tích", "tấn công người", "hại người khác",
    "muốn giết", "sẽ giết", "planning to kill",
]

# ─── Safety messages ──────────────────────────────────────────────────────────

SAFETY_MESSAGE_VN = """
⚠️ **Hệ thống đã dừng lại**

Cảm ơn bạn đã chia sẻ. Những gì bạn đang trải qua rất quan trọng.

**Hành động ngay hôm nay:**

1. 📞 **Tổ chức Sức khỏe Tâm thần Quốc gia: 988** (miễn phí, 24/7)
2. ☎️ **Gọi 115** hoặc đến phòng cấp cứu gần nhất nếu bạn cảm thấy nguy hiểm ngay lập tức.
3. 💬 Nói chuyện với người bạn hoặc người thân mà bạn tin tưởng.

Bạn **không đơn độc**. Hệ thống trị liệu này sẽ không thể tiếp tục sau những dấu hiệu này.
Một chuyên gia sẽ được thông báo và liên hệ với bạn trong vòng 24 giờ.
"""

SAFETY_MESSAGE_EN = """
⚠️ **This session has been paused by the safety system.**

Thank you for sharing. What you're going through matters.

**Please take action today:**
1. 📞 **National Suicide Prevention Lifeline: 988** (free, 24/7)
2. ☎️ Call **115** or go to your nearest emergency room if you are in immediate danger.
3. 💬 Reach out to someone you trust — a friend, family member, or counselor.

You are **not alone**. A licensed professional will be notified and will reach out within 24 hours.
"""

# ─── Core check function ──────────────────────────────────────────────────────

def gate_d_check(text: str) -> Tuple[bool, str]:
    """
    Synchronous safety check.
    Returns (triggered: bool, reason: str).
    reason = '' | 'suicide' | 'self_harm' | 'violence'
    """
    if not text:
        return False, ""

    lower = text.lower()

    for kw in SUICIDE_KEYWORDS:
        if kw in lower:
            return True, "suicide"

    for kw in HARM_KEYWORDS:
        if kw in lower:
            return True, "self_harm"

    for kw in VIOLENCE_KEYWORDS:
        if kw in lower:
            return True, "violence"

    return False, ""


def format_safety_message(lang: str = "vi") -> str:
    """Return the appropriate language safety message."""
    if lang == "en":
        return SAFETY_MESSAGE_EN.strip()
    return SAFETY_MESSAGE_VN.strip()

"""
Tests for app/state/gate_d.py
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.state.gate_d import gate_d_check, SUICIDE_KEYWORDS, HARM_KEYWORDS, VIOLENCE_KEYWORDS


class TestGateD:
    # ─── Suicide keywords ───────────────────────────────────────────────────────

    def test_suicide_exact_match(self):
        for kw in SUICIDE_KEYWORDS:
            triggered, reason = gate_d_check(f"Tôi muốn {kw}")
            assert triggered, f"Should trigger on: {kw}"
            assert reason == "suicide"

    def test_suicide_case_insensitive(self):
        triggered, reason = gate_d_check("TỰ TỬ")
        assert triggered
        assert reason == "suicide"

    def test_suicide_partial_phrase(self):
        # "tôi không muốn sống nữa" should trigger
        triggered, reason = gate_d_check("không muốn sống nữa")
        assert triggered
        assert reason == "suicide"

    def test_no_trigger_on_normal_text(self):
        normal_texts = [
            "Hôm nay tôi cảm thấy buồn vì công việc",
            "Tôi muốn nghỉ ngơi một chút",
            "Cuộc sống thật mệt mỏi",
            "Tôi đang cảm thấy chán nản",
            "Tôi không thích điều này",
        ]
        for text in normal_texts:
            triggered, _ = gate_d_check(text)
            assert not triggered, f"Should NOT trigger on: {text}"

    def test_empty_text_no_trigger(self):
        triggered, reason = gate_d_check("")
        assert not triggered
        assert reason == ""

    def test_none_text_no_trigger(self):
        triggered, reason = gate_d_check(None)
        assert not triggered

    # ─── Self-harm keywords ────────────────────────────────────────────────────

    def test_self_harm_keywords(self):
        for kw in HARM_KEYWORDS:
            triggered, reason = gate_d_check(f"Tôi muốn {kw}")
            assert triggered, f"Should trigger on: {kw}"
            assert reason == "self_harm"

    # ─── Violence keywords ─────────────────────────────────────────────────────

    def test_violence_keywords(self):
        for kw in VIOLENCE_KEYWORDS:
            triggered, reason = gate_d_check(f"Tôi muốn {kw}")
            assert triggered, f"Should trigger on: {kw}"
            assert reason == "violence"

    # ─── Priority: suicide > harm > violence ───────────────────────────────────
    # Since loops run in order, suicide is checked first

    def test_suicide_takes_priority(self):
        # If a word appears in both lists, suicide should take priority
        text = "I want to end my life and hurt myself"
        triggered, reason = gate_d_check(text)
        assert triggered
        # "end my life" is in SUICIDE_KEYWORDS → suicide
        assert reason == "suicide"

    # ─── Edge cases ────────────────────────────────────────────────────────────

    def test_unicode_vietnamese(self):
        assert gate_d_check("tự tử")[0]
        assert gate_d_check("muốn chết")[0]

    def test_english_keywords(self):
        assert gate_d_check("I want to die")[0]
        assert gate_d_check("kill myself")[0]

    def test_spaces_around_keywords(self):
        # Keywords should trigger even with spaces
        triggered, reason = gate_d_check("  tự tử  ")
        assert triggered
        assert reason == "suicide"

    def test_multiple_keywords_same_category(self):
        # All three categories in one text → suicide fires first
        text = "tự tử and kill myself and hurt others"
        triggered, reason = gate_d_check(text)
        assert triggered
        assert reason == "suicide"

    def test_conversation_context_not_trigger(self):
        # Normal therapy conversation should not trigger
        safe_texts = [
            "Tôi đang cảm thấy buồn vì mất việc",
            "Tôi lo lắng về tương lai",
            "Tôi cảm thấy cô đơn gần đây",
            "Tôi muốn thay đổi cuộc sống",
            "Tôi đang trải qua giai đoạn khó khăn",
        ]
        for text in safe_texts:
            triggered, _ = gate_d_check(text)
            assert not triggered, f"Should NOT trigger on therapy content: {text}"

    def test_keyword_coverage_report(self):
        """Report how many keywords each category has (for review)."""
        assert len(SUICIDE_KEYWORDS) >= 15, "Need comprehensive suicide keyword list"
        assert len(HARM_KEYWORDS) >= 10, "Need comprehensive harm keyword list"
        assert len(VIOLENCE_KEYWORDS) >= 8, "Need comprehensive violence keyword list"

"""
Tests for app/state/workflow_decider.py and session_machine.py
"""

import pytest
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.state.session_machine import WStep
from app.state.workflow_decider import decide_session_plan


# ─── workflow_decider tests ────────────────────────────────────────────────────

class TestWorkflowDecider:
    def test_first_time_user_gets_full_session(self):
        """New user → full W1-W7 plan."""
        progress = {
            "h_presence": 5.0,
            "g_awareness": "",
            "f_khat_chhet": 0,
            "d_loops": "",
            "e_layers": "",
        }
        plan = decide_session_plan(progress, last_w=None)
        steps = [s.value for s in plan]
        assert steps[0] == "W1"
        assert steps[-1] == "W7"
        # W2 always present
        assert "W2" in steps
        # W4b skipped when F is khớp
        assert "W4b" not in steps

    def test_mode_a_when_h_low(self):
        """H < 4 → Mode A path (short, skips deep work)."""
        progress = {
            "h_presence": 3.5,
            "g_awareness": "",
            "f_khat_chhet": 0,
            "d_loops": "",
            "e_layers": "",
        }
        plan = decide_session_plan(progress, last_w=None)
        steps = [s.value for s in plan]
        # Should have W1, W2, W3, W6, W7
        assert "W1" in steps
        assert "W2" in steps
        assert "W3" in steps
        assert "W4b" not in steps  # F deep work skipped
        assert "W5" not in steps    # G skipped
        assert "W6" in steps
        assert "W7" in steps

    def test_w4b_included_when_f_khat(self):
        """F=kẹt (1) → W4b should be included."""
        progress = {
            "h_presence": 6.0,
            "g_awareness": "some awareness data here",
            "f_khat_chhet": 1,
            "d_loops": "loop data",
            "e_layers": "layer data",
        }
        plan = decide_session_plan(progress, last_w=None)
        steps = [s.value for s in plan]
        assert "W4b" in steps

    def test_w4b_included_when_f_troi(self):
        """F=trói (2) → W4b should be included."""
        progress = {
            "h_presence": 6.0,
            "g_awareness": "x" * 50,
            "f_khat_chhet": 2,
            "d_loops": "loop",
            "e_layers": "layers",
        }
        plan = decide_session_plan(progress, last_w=None)
        steps = [s.value for s in plan]
        assert "W4b" in steps

    def test_w5_skipped_when_g_sufficient(self):
        """G is long enough → W5 skipped (no need to re-read)."""
        progress = {
            "h_presence": 5.0,
            "g_awareness": "x" * 50,  # >= 40 chars
            "f_khat_chhet": 0,
            "d_loops": "loop",
            "e_layers": "layers",
        }
        plan = decide_session_plan(progress, last_w=None)
        steps = [s.value for s in plan]
        assert "W5" not in steps

    def test_w5_skipped_when_g_long_enough(self):
        """G is >= 40 chars → W5 skipped."""
        progress = {
            "h_presence": 5.0,
            "g_awareness": "A" * 45,
            "f_khat_chhet": 0,
            "d_loops": "",
            "e_layers": "",
        }
        plan = decide_session_plan(progress, last_w=None)
        assert "W5" not in [s.value for s in plan]

    def test_w3_included_if_last_session_was_w3(self):
        """If last session ended at W3 → W3 included again (D needs work)."""
        progress = {
            "h_presence": 5.0,
            "g_awareness": "x" * 50,
            "f_khat_chhet": 0,
            "d_loops": "",  # never captured
            "e_layers": "",
        }
        plan = decide_session_plan(progress, last_w="W3")
        steps = [s.value for s in plan]
        assert "W3" in steps

    def test_short_session_all_populated(self):
        """All channels populated, F=khớp → short session."""
        progress = {
            "h_presence": 7.0,
            "g_awareness": "x" * 50,
            "f_khat_chhet": 0,
            "d_loops": "some loop",
            "e_layers": "some layers",
        }
        plan = decide_session_plan(progress, last_w="W7")
        steps = [s.value for s in plan]
        # Only W1, W2, W6, W7 needed
        assert steps == ["W1", "W2", "W6", "W7"]


class TestSessionMachine:
    def test_wstep_enum_values(self):
        assert WStep.W1.value == "W1"
        assert WStep.W4b.value == "W4b"
        assert WStep.DONE.value == "DONE"

    def test_wstep_order(self):
        """Enum values should sort correctly by their string values."""
        # Sort by the .value string, not the enum itself
        steps = sorted([WStep.W4b, WStep.W3, WStep.W1, WStep.W7], key=lambda s: s.value)
        values = [s.value for s in steps]
        assert values == ["W1", "W3", "W4b", "W7"]

    def test_step_label(self):
        from app.state.session_machine import TherapySessionMachine
        import uuid
        # Patch db methods
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            os.unlink(f.name)
        # Can't fully test without DB — test step_label directly
        machine = TherapySessionMachine(session_id=str(uuid.uuid4()), user_id=str(uuid.uuid4()))
        assert "Mở cổng" in machine.step_label()

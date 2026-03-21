"""
Therapy Session State Machine.
Pure logic — no Streamlit imports. Fully unit-testable.
"""

import uuid
from enum import Enum
from typing import Optional

from app.data.db import (
    create_session,
    update_session_step,
    update_session_output,
    trigger_gate_d,
    save_message,
    save_snapshot,
    load_user_progress,
    update_user_progress,
    get_user_sessions,
)


class WStep(Enum):
    W1  = "W1"
    W2  = "W2"
    W3  = "W3"
    W4  = "W4"
    W4b = "W4b"
    W5  = "W5"
    W6  = "W6"
    W7  = "W7"
    DONE = "DONE"


class TherapySessionMachine:
    """
    Manages the lifecycle of a single therapy session.
    """

    def __init__(self, session_id: str, user_id: str, mode: str = "B"):
        self.session_id  = session_id
        self.user_id     = user_id
        self.mode        = mode
        self.current_step = WStep.W1
        self.plan: list[WStep] = []
        self.channel_state: dict = {}   # captured C, D, E, F, G, H
        self.output_6a: list = []
        self.homework: list = []
        self.indicators: dict = {}
        self._db = None   # lazy — passed at init_session time

    def init_session(self, last_w: Optional[str]) -> None:
        """Called at W1. Creates DB session row and decides workflow plan."""
        create_session(self.session_id, self.user_id)
        progress = load_user_progress(self.user_id)

        # Import here to avoid circular import
        from app.state.workflow_decider import decide_session_plan
        from app.state.mode_router import determine_mode

        self.plan = decide_session_plan(progress, last_w)
        self.mode = determine_mode(self.channel_state, progress)
        update_session_step(self.session_id, self.current_step.value, self.mode)

    def save_message(self, role: str, content: str,
                     channel: Optional[str] = None) -> None:
        """Persist a message to the DB."""
        save_message(
            self.session_id, role, content,
            channel, self.current_step.value,
        )

    def advance(self, captured: Optional[dict] = None) -> WStep:
        """
        Called after each W-step completes.
        - Saves captured channel data to DB and user_progress
        - Re-evaluates mode
        - Moves to next step in the plan
        Returns the new current step.
        """
        if captured:
            self.channel_state.update(captured)
            save_snapshot(
                self.session_id,
                self.current_step.value,
                captured,
            )
            update_user_progress(self.user_id, captured)

        # Re-evaluate mode (H may have shifted)
        progress = load_user_progress(self.user_id)
        from app.state.mode_router import determine_mode
        self.mode = determine_mode(self.channel_state, progress)

        # Advance to next step in plan
        remaining = [s for s in self.plan if s.value > self.current_step.value]
        if remaining:
            self.current_step = remaining[0]
        else:
            self.current_step = WStep.DONE

        update_session_step(
            self.session_id,
            self.current_step.value,
            self.mode,
        )
        return self.current_step

    def finish(
        self,
        session_summary: str,
        output_6a: list,
        homework: list,
        indicators: dict,
    ) -> None:
        """Called at W7 completion. Persists all outputs."""
        import json
        self.output_6a  = output_6a
        self.homework   = homework
        self.indicators = indicators

        update_session_output(
            self.session_id,
            session_summary,
            json.dumps(output_6a, ensure_ascii=False),
            json.dumps(homework, ensure_ascii=False),
            json.dumps(indicators, ensure_ascii=False),
        )

    def lock_due_to_gate_d(self) -> None:
        """Mark session as Gate D triggered."""
        trigger_gate_d(self.session_id)

    def is_done(self) -> bool:
        return self.current_step == WStep.DONE

    def current_prompt_key(self) -> str:
        """Return the DB prompt key for the current W-step."""
        return self.current_step.value.lower().replace("w4b", "w4b_compare_f")

    def step_label(self) -> str:
        """Human-readable step label."""
        labels = {
            WStep.W1:  "Mở cổng",
            WStep.W2:  "Đọc C — Hiện tượng sống",
            WStep.W3:  "Đọc D — Dòng & Vòng lặp",
            WStep.W4:  "Đọc E — Tầng & Bậc",
            WStep.W4b: "W4b — Đối chiếu Khuôn lệch",
            WStep.W5:  "Đọc G — Tỉnh biết",
            WStep.W6:  "Đọc H — Hiện diện & Quyết liều",
            WStep.W7:  "Tổng hợp — 6A & Bài tập",
            WStep.DONE: "Hoàn tất",
        }
        return labels.get(self.current_step, str(self.current_step.value))

"""
Expert Prompt Editor — chỉnh sửa system prompts trực tiếp.
Chuyên gia có quyền: expert hoặc admin.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.data.db as db
from app.auth import get_user_from_session, is_at_least
from app.data.prompt_repo import (
    get_active_prompt,
    get_prompt_versions,
    save_prompt_version,
    activate_prompt_version,
    seed_prompts_from_files,
)

st.set_page_config(page_title="Sửa Prompts — Expert", page_icon="📝")

# ─── Auth guard ───────────────────────────────────────────────────────────────

if not st.session_state.get("user"):
    st.warning("Vui lòng đăng nhập trước.")
    st.switch_page("pages/00_Login.py")

user = get_user_from_session(st.session_state.user)
if not user:
    st.error("Phiên đăng nhập đã hết hạn.")
    st.session_state.user = None
    st.rerun()

if not is_at_least(user.get("role", ""), "expert"):
    st.error("⚠️ Chỉ chuyên gia hoặc quản trị viên mới có quyền truy cập.")
    st.stop()

# ─── Seed prompts if not already seeded ────────────────────────────────────────

seeded = seed_prompts_from_files(created_by=user["id"])

# ─── Prompt registry ─────────────────────────────────────────────────────────

PROMPT_LIST = [
    ("w1_open_gate",   "W1 — Mở Cổng"),
    ("w2_read_c",      "W2 — Đọc C (Hiện Tượng)"),
    ("w3_read_d",       "W3 — Đọc D (Dòng & Vòng Lặp)"),
    ("w4_read_e",      "W4 — Đọc E (Tầng & Bậc)"),
    ("w4b_compare_f",  "W4b — Đối Chiếu Khuôn Lệch (F)"),
    ("w5_read_g",      "W5 — Đọc G (Tỉnh Biết)"),
    ("w6_read_h",      "W6 — Đọc H & Quyết Liều"),
    ("w7_synthesize",  "W7 — Tổng Hợp (6A & Bài Tập)"),
]

SHARED_PROMPTS = [
    ("shared/channel_definitions", "Shared — 7 Kênh"),
    ("shared/modes",              "Shared — 4 Modes"),
    ("shared/6a_actions",         "Shared — 6A Actions"),
]

ALL_PROMPTS = PROMPT_LIST + SHARED_PROMPTS

# ─── Sidebar: prompt list + version history ────────────────────────────────────

with st.sidebar:
    st.markdown("### 📝 Prompts")
    prompt_labels = [label for _, label in ALL_PROMPTS]
    selected_label = st.selectbox("Chọn prompt:", prompt_labels)

    # Map label back to key
    selected_key = next(k for k, l in ALL_PROMPTS if l == selected_label)

    st.markdown("---")
    st.markdown("**Lịch sử phiên bản:**")

    try:
        versions = get_prompt_versions(selected_key)
        for v in versions:
            label = f"v{v['version']} · {v.get('created_by_name', 'system')} · {v['created_at'][:10]}"
            if v.get("is_active"):
                st.markdown(f"✅ **{label}** *(đang dùng)*")
            else:
                if st.button(f"↩ Rollback v{v['version']}", key=f"rb_{v['version']}"):
                    activate_prompt_version(selected_key, v["version"], user["id"])
                    st.success(f"Đã rollback v{v['version']}.")
                    st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi tải lịch sử: {e}")

    st.markdown("---")
    if st.button("📋 Tất cả buổi trị liệu"):
        st.switch_page("pages/01_Therapy_Chat.py")
    if st.button("📊 Dashboard"):
        st.switch_page("pages/04_Stakeholder_Dashboard.py")
    if st.button("🚪 Đăng xuất"):
        st.session_state.user = None
        st.switch_page("pages/00_Login.py")

# ─── Main: editor ─────────────────────────────────────────────────────────────

st.markdown(f"## {selected_label}")
st.markdown(f"**Prompt key:** `{selected_key}`")

# Load current active content
try:
    active = get_active_prompt(selected_key)
    current_content = active["content"]
    current_version = active["version"]
except KeyError:
    current_content = "[Prompt chưa được seed. Hãy liên hệ admin.]"
    current_version = 0

# Draft management
draft_key = f"draft_{selected_key}"
if draft_key not in st.session_state:
    st.session_state[draft_key] = current_content

editor_content = st.text_area(
    "Nội dung prompt:",
    value=st.session_state[draft_key],
    height=500,
    key="prompt_editor",
)

# Update draft on edit
st.session_state[draft_key] = editor_content

col_preview, col_save = st.columns([1, 1])

with col_save:
    note = st.text_area(
        "Ghi chú thay đổi (tùy chọn):",
        placeholder="VD: Thêm câu hỏi mẫu cho W2",
        height=80,
        key="change_note",
    )
    if st.button("💾 Lưu phiên bản mới", type="primary", use_container_width=True):
        new_version = save_prompt_version(selected_key, editor_content, user["id"])
        st.session_state[draft_key] = editor_content
        st.success(f"✅ Đã lưu v{new_version}. Prompt sẽ có hiệu lực ngay cho phiên tiếp theo.")
        st.rerun()

with col_preview:
    st.markdown("**Preview (markdown):**")
    st.markdown(editor_content)

st.markdown("---")
st.info(
    "💡 **Lưu ý:** Mỗi lần lưu tạo phiên bản mới. Phiên bản cũ vẫn còn trong lịch sử "
    "— có thể rollback bất cứ lúc nào từ sidebar."
)

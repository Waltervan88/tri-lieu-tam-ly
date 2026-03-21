"""
Versioned expert prompt storage.
Each save creates a new row; only the active row is used by the LLM.
"""

import uuid
import os
from pathlib import Path
from typing import Optional

from app.data.db import get_db


# ─── DB operations ───────────────────────────────────────────────────────────

def get_active_prompt(prompt_key: str) -> dict:
    """
    Return the active version of a prompt key.
    Raises KeyError if no active version found.
    """
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM expert_prompts WHERE prompt_key=? AND is_active=1 "
        "ORDER BY version DESC LIMIT 1",
        (prompt_key,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise KeyError(f"No active prompt found for key: {prompt_key}")
    return dict(row)


def get_prompt_versions(prompt_key: str) -> list[dict]:
    """Return all versions of a prompt key, newest first."""
    conn = get_db()
    cur = conn.execute(
        "SELECT p.*, u.name as created_by_name "
        "FROM expert_prompts p "
        "LEFT JOIN users u ON p.created_by=u.id "
        "WHERE prompt_key=? ORDER BY version DESC",
        (prompt_key,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_prompt_version(prompt_key: str, content: str, created_by: str) -> int:
    """
    Save a new version of a prompt.
    Deactivates all previous versions for this key.
    Returns the new version number.
    """
    conn = get_db()

    # Deactivate all previous versions
    conn.execute(
        "UPDATE expert_prompts SET is_active=0 WHERE prompt_key=?",
        (prompt_key,),
    )

    # Get next version number
    cur = conn.execute(
        "SELECT MAX(version) as max_v FROM expert_prompts WHERE prompt_key=?",
        (prompt_key,),
    )
    max_v = cur.fetchone()["max_v"] or 0
    new_version = max_v + 1

    # Insert new row
    conn.execute(
        """INSERT INTO expert_prompts
           (id,prompt_key,version,content,created_by,is_active)
           VALUES (?,?,?,?,?,1)""",
        (str(uuid.uuid4()), prompt_key, new_version, content, created_by),
    )
    conn.commit()
    conn.close()
    return new_version


def activate_prompt_version(prompt_key: str, version: int, activated_by: str) -> None:
    """
    Roll back to a specific version: deactivate current, activate target.
    """
    conn = get_db()
    conn.execute(
        "UPDATE expert_prompts SET is_active=0 WHERE prompt_key=?",
        (prompt_key,),
    )
    conn.execute(
        "UPDATE expert_prompts SET is_active=1 WHERE prompt_key=? AND version=?",
        (prompt_key, version),
    )
    conn.commit()
    conn.close()


def seed_prompts_from_files(prompts_dir: Optional[Path] = None,
                             created_by: str = "system") -> int:
    """
    Seed prompts into DB from .md files in prompts_dir.
    Creates new version rows (or updates if already seeded).
    Returns number of prompts seeded.
    """
    if prompts_dir is None:
        prompts_dir = Path(__file__).parent.parent / "prompts"

    count = 0
    for md_file in sorted(prompts_dir.rglob("*.md")):
        # Build prompt_key from relative path: e.g. "w2_read_c" or "shared/channel_defs"
        rel = md_file.relative_to(prompts_dir)
        # Use folder.name for shared files, filename stem for others
        if rel.parts[0] == "shared":
            prompt_key = f"shared/{rel.stem}"
        else:
            prompt_key = rel.stem

        content = md_file.read_text(encoding="utf-8")

        # Check if already seeded (any version exists)
        conn = get_db()
        cur = conn.execute(
            "SELECT 1 FROM expert_prompts WHERE prompt_key=? LIMIT 1",
            (prompt_key,),
        )
        exists = cur.fetchone() is not None
        conn.close()

        if not exists:
            # First seed — save as v1, active
            save_prompt_version(prompt_key, content, created_by)
            count += 1

    return count

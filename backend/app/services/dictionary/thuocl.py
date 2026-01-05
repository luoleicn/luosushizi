"""THUOCL dictionary lookup."""

from __future__ import annotations

from typing import List

from app.core.db import get_connection


def get_common_words(db_path: str, hanzi: str, limit: int) -> List[dict]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT cw.word, cw.frequency
            FROM character_word_index cwi
            JOIN common_words cw ON cw.id = cwi.word_id
            WHERE cwi.hanzi = ?
            ORDER BY cw.frequency DESC
            LIMIT ?
            """,
            (hanzi, limit),
        ).fetchall()
        return [{"word": row["word"], "frequency": row["frequency"]} for row in rows]
    finally:
        conn.close()

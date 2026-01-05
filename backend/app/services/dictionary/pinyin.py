"""Pinyin utilities (offline)."""

from __future__ import annotations

from pypinyin import Style, pinyin


def get_pinyin(hanzi: str) -> str:
    result = pinyin(hanzi, style=Style.TONE3, strict=False)
    return " ".join(item[0] for item in result)

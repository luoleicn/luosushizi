"""SM-2 scheduling algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class ReviewResult:
    ease_factor: float
    interval: int
    repetitions: int
    next_review_at: datetime


def apply_sm2(
    *,
    ease_factor: float,
    interval: int,
    repetitions: int,
    rating: int,
    reviewed_at: datetime | None = None,
) -> ReviewResult:
    # Rating should be 0-5. Use 0-2 for unknown, 3-5 for known.
    if reviewed_at is None:
        reviewed_at = datetime.now(timezone.utc)

    if rating < 3:
        repetitions = 0
        interval = 1
    else:
        repetitions += 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 6
        else:
            interval = int(round(interval * ease_factor))

    # Adjust ease factor
    ease_factor = ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
    if ease_factor < 1.3:
        ease_factor = 1.3

    next_review_at = reviewed_at + timedelta(days=interval)
    return ReviewResult(
        ease_factor=ease_factor,
        interval=interval,
        repetitions=repetitions,
        next_review_at=next_review_at,
    )

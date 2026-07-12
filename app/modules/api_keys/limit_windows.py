from __future__ import annotations

from datetime import datetime, timedelta

from app.db.models import LimitWindow

LIFETIME_RESET_AT = datetime.max


def next_limit_reset(now: datetime, window: LimitWindow) -> datetime:
    if window == LimitWindow.LIFETIME:
        return LIFETIME_RESET_AT
    return now + limit_window_delta(window)


def advance_limit_reset(reset_at: datetime, now: datetime, window: LimitWindow) -> datetime:
    if window == LimitWindow.LIFETIME:
        return LIFETIME_RESET_AT
    delta = limit_window_delta(window)
    next_reset = reset_at
    while next_reset <= now:
        next_reset += delta
    return next_reset


def limit_window_delta(window: LimitWindow) -> timedelta:
    if window == LimitWindow.LIFETIME:
        raise ValueError("lifetime limits do not have a reset interval")
    if window == LimitWindow.ONE_HOUR:
        return timedelta(hours=1)
    if window == LimitWindow.FIVE_HOURS:
        return timedelta(hours=5)
    if window == LimitWindow.SEVEN_DAYS:
        return timedelta(days=7)
    if window == LimitWindow.DAILY:
        return timedelta(days=1)
    if window == LimitWindow.WEEKLY:
        return timedelta(days=7)
    if window == LimitWindow.MONTHLY:
        return timedelta(days=30)
    return timedelta(days=7)

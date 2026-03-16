"""
Date and timezone utilities for Indian market context.

NSE market hours: 09:15 – 15:30 IST, Monday to Friday.
Timezone: Asia/Kolkata (IST = UTC+5:30).

Functions:
  is_market_open() -> bool
      True if current IST time is within NSE session on a weekday.

  get_last_trading_day() -> date
      Returns most recent NSE trading day (excludes weekends and holidays
      listed in data/market_holidays.csv).

  to_ist(dt: datetime) -> datetime
      Converts any datetime to IST timezone-aware datetime.

  trading_days_between(start: date, end: date) -> int
      Count of NSE trading days (excl. weekends and holidays).

  get_market_status() -> dict
      Returns is_open, reason (if closed), and last_close date.
"""

import csv
import os
from datetime import date, datetime, time, timedelta

import pytz

_IST = pytz.timezone("Asia/Kolkata")
MARKET_OPEN_IST  = time(9, 15)
MARKET_CLOSE_IST = time(15, 30)

# Module-level caches — loaded once per process
_HOLIDAYS: set | None = None
_HOLIDAY_NAMES: dict | None = None

_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "market_holidays.csv")


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_holidays() -> tuple[set, dict]:
    """Load holidays from CSV once; return (dates_set, name_map)."""
    global _HOLIDAYS, _HOLIDAY_NAMES
    if _HOLIDAYS is not None:
        return _HOLIDAYS, _HOLIDAY_NAMES

    _HOLIDAYS = set()
    _HOLIDAY_NAMES = {}
    try:
        with open(_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = (row.get("Date") or "").strip()
                description = (row.get("Description") or "").strip()
                if date_str:
                    d = date.fromisoformat(date_str)
                    _HOLIDAYS.add(d)
                    if description:
                        _HOLIDAY_NAMES[d] = description
    except FileNotFoundError:
        pass

    return _HOLIDAYS, _HOLIDAY_NAMES


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def to_ist(dt: datetime) -> datetime:
    """Convert any datetime to IST timezone-aware datetime."""
    if dt.tzinfo is None:
        return _IST.localize(dt)
    return dt.astimezone(_IST)


def is_trading_day(d: date | None = None) -> bool:
    """True if d is a weekday that is not an NSE market holiday."""
    if d is None:
        d = datetime.now(_IST).date()
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    holidays, _ = _load_holidays()
    return d not in holidays


def is_market_open() -> bool:
    """True if current IST time is within the NSE trading session."""
    now_ist = datetime.now(_IST)
    if not is_trading_day(now_ist.date()):
        return False
    t = now_ist.time()
    return MARKET_OPEN_IST <= t <= MARKET_CLOSE_IST


def get_last_trading_day() -> date:
    """Return the most recent completed NSE trading day."""
    d = datetime.now(_IST).date()
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def get_market_status() -> dict:
    """
    Describe the current NSE market state.

    Returns:
        is_open     — bool
        reason      — str | None  (human-readable reason if closed)
        last_close  — date        (most recently completed trading session)
    """
    now_ist = datetime.now(_IST)
    today = now_ist.date()
    holidays, holiday_names = _load_holidays()

    weekday = today.weekday()
    t = now_ist.time()

    if weekday == 5:
        reason = "Weekend — Saturday"
    elif weekday == 6:
        reason = "Weekend — Sunday"
    elif today in holidays:
        name = holiday_names.get(today, "Market Holiday")
        reason = f"Public Holiday — {name}"
    elif t < MARKET_OPEN_IST:
        reason = "Pre-market (opens 09:15 IST)"
    elif t > MARKET_CLOSE_IST:
        reason = "After-hours (closed at 15:30 IST)"
    else:
        reason = None  # market is live right now

    # Compute last *completed* session date
    if reason is None or "Pre-market" in (reason or ""):
        # Either live now or pre-market — last completed session was yesterday
        ref = today - timedelta(days=1)
    else:
        # Weekend / holiday / after-hours — last session is today or earlier
        ref = today

    while not is_trading_day(ref):
        ref -= timedelta(days=1)

    return {
        "is_open":    reason is None,
        "reason":     reason,
        "last_close": ref,
    }


def trading_days_between(start: date, end: date) -> int:
    """Count NSE trading days between start (inclusive) and end (inclusive)."""
    count = 0
    d = start
    while d <= end:
        if is_trading_day(d):
            count += 1
        d += timedelta(days=1)
    return count

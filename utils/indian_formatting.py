"""
Formatting helpers for Indian financial conventions.

All monetary display goes through these functions — never format INR
values inline in pages or components.

Functions:
  to_crore(raw_inr: float) -> float
      Converts raw INR value (as returned by yfinance) to Crore.
      1 Crore = 10,000,000 (10^7).

  format_inr_crore(value: float) -> str
      e.g. 1234567.89 Cr → "₹12,34,567.89 Cr"
      Uses Indian number grouping (xx,xx,xxx).

  format_volume(value: float) -> str
      e.g. 1234567 → "12.35 L" (Lakh) or "1.23 Cr"

  format_percentage(value: float, sign: bool = True) -> str
      e.g. 3.421 → "+3.42%" | -1.2 → "-1.20%"

  format_price(value: float) -> str
      e.g. 1234.56 → "₹1,234.56"
"""

import math


def to_crore(raw_inr: float) -> float | None:
    """Convert raw INR value (as returned by yfinance) to Crore. 1 Crore = 10,000,000."""
    if raw_inr is None:
        return None
    return raw_inr / 1e7


def _indian_int(n: int) -> str:
    """Format integer part with Indian grouping: 12345678 → '1,23,45,678'."""
    s = str(abs(n))
    if len(s) <= 3:
        return ("-" if n < 0 else "") + s
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return ("-" if n < 0 else "") + result


def format_inr_crore(value: float) -> str:
    """e.g. 1234567.89 Cr → "₹12,34,567.89 Cr" — Indian number grouping."""
    if value is None or math.isnan(float(value)):
        return "—"
    int_part = int(value)
    frac = round(abs(float(value)) - abs(int_part), 2)
    frac_str = f"{frac:.2f}"[1:]  # ".89"
    return f"₹{_indian_int(int_part)}{frac_str} Cr"


def format_volume(value: float) -> str:
    """e.g. 1234567 → '12.35 L' (Lakh) or '1.23 Cr'."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(v):
        return "—"
    if v >= 1e7:
        return f"{v / 1e7:.2f} Cr"
    if v >= 1e5:
        return f"{v / 1e5:.2f} L"
    return f"{int(v):,}"


def format_percentage(value: float, sign: bool = True) -> str:
    """e.g. 3.421 → '+3.42%' | -1.2 → '-1.20%'."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(v):
        return "—"
    prefix = "+" if sign and v >= 0 else ""
    return f"{prefix}{v:.2f}%"


def format_price(value: float) -> str:
    """e.g. 1234.56 → '₹1,234.56'."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(v):
        return "—"
    return f"₹{v:,.2f}"

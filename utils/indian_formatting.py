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

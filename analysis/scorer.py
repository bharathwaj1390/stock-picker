import pandas as pd


# ---------------------------------------------------------------------------
# Null check helper
# ---------------------------------------------------------------------------

def _missing(val) -> bool:
    """True for Python None, np.nan, pd.NA, or pd.NaT."""
    try:
        return val is None or pd.isna(val)
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Individual metric scoring functions  (return int 1–10)
# Missing / unavailable data always returns the neutral score of 5.
# ---------------------------------------------------------------------------

def _score_pe(pe) -> int:
    """Lower P/E = cheaper relative to earnings = higher score."""
    if _missing(pe):  return 5
    if pe <= 0:       return 2   # loss-making company
    if pe < 10:       return 10
    if pe < 15:       return 8
    if pe < 20:       return 6
    if pe < 30:       return 4
    return 2


def _score_pb(pb) -> int:
    """Lower P/B = cheaper relative to book value. Below 1 = undervalued."""
    if _missing(pb):  return 5
    if pb <= 0:       return 2   # negative book value — red flag
    if pb < 1:        return 10
    if pb < 2:        return 8
    if pb < 3:        return 6
    if pb < 5:        return 4
    return 2


def _score_roe(roe) -> int:
    """Higher ROE = better capital efficiency. Input already in % (e.g. 15.43)."""
    if _missing(roe): return 5
    if roe > 25:      return 10
    if roe > 20:      return 8
    if roe > 15:      return 6
    if roe > 10:      return 4
    return 2   # includes zero and negative ROE (loss-making)


def _score_de(de) -> int:
    """Lower D/E = less leveraged = safer. Input is the ratio (e.g. 0.45)."""
    if _missing(de):  return 5
    if de < 0:        return 2   # negative equity — structural red flag
    if de < 0.5:      return 10
    if de < 1.0:      return 8
    if de < 1.5:      return 6
    if de < 2.0:      return 4
    return 2


def _score_growth(growth) -> int:
    """Higher revenue growth = better momentum. Input already in % (e.g. 12.34)."""
    if _missing(growth): return 5
    if growth > 20:      return 10
    if growth > 15:      return 8
    if growth > 10:      return 6
    if growth > 5:       return 4
    return 2   # includes zero and negative growth (shrinking revenue)


def _score_week52(current, high, low) -> float:
    """
    Score based on position within the 52-week price range.

    Rationale: a price closer to its 52-week low offers a more
    attractive entry point from a value perspective.

        position = (current - low) / (high - low)
            0.0  →  at 52-week low   →  score 10  (best entry)
            1.0  →  at 52-week high  →  score  1  (worst entry)

    Linear interpolation:  score = 10 − 9 × position
    """
    if _missing(current) or _missing(high) or _missing(low):
        return 5.0

    price_range = high - low
    if price_range <= 0:
        return 5.0

    position = (current - low) / price_range
    position = max(0.0, min(1.0, position))   # clamp — handles price outside range
    return round(10.0 - 9.0 * position, 1)


# ---------------------------------------------------------------------------
# Rating label
# ---------------------------------------------------------------------------

def _rating(value_score: float) -> str:
    if value_score >= 8.0: return "Strong Buy"
    if value_score >= 6.0: return "Buy"
    if value_score >= 5.0: return "Watch"
    if value_score >= 4.0: return "Hold"
    if value_score >= 2.0: return "Avoid"
    return "Strong Avoid"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_SCORE_COLS = [
    "pe_score",
    "pb_score",
    "roe_score",
    "de_score",
    "growth_score",
    "week52_score",
]


def score_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score and rank stocks across six fundamental factors.

    Each factor is scored 1–10 (5 = data unavailable / neutral).
    An equal-weighted average produces the composite value_score.

    New columns added:
        pe_score       P/E ratio score          (1–10)
        pb_score       P/B ratio score          (1–10)
        roe_score      Return on Equity score   (1–10)
        de_score       Debt/Equity score        (1–10)
        growth_score   Revenue Growth score     (1–10)
        week52_score   52-week position score   (1–10)
        value_score    Equal-weighted average   (float, 2 d.p.)
        rating         "Strong Buy" | "Buy" | "Watch" | "Hold" | "Avoid" | "Strong Avoid"

    Args:
        df: DataFrame from fetcher.fetch_stock_data()

    Returns:
        Enriched DataFrame sorted by value_score descending, index reset.
    """
    out = df.copy()

    # --- per-factor scores ---
    out["pe_score"]     = out["PE Ratio"].apply(_score_pe)
    out["pb_score"]     = out["PB Ratio"].apply(_score_pb)
    out["roe_score"]    = out["ROE (%)"].apply(_score_roe)
    out["de_score"]     = out["Debt/Equity"].apply(_score_de)
    out["growth_score"] = out["Revenue Growth (%)"].apply(_score_growth)
    out["week52_score"] = out.apply(
        lambda r: _score_week52(r["Current Price"], r["52W High"], r["52W Low"]),
        axis=1,
    )

    # --- composite score (equal weights = simple mean) ---
    out["value_score"] = out[_SCORE_COLS].mean(axis=1).round(2)

    # --- qualitative rating ---
    out["rating"] = out["value_score"].apply(_rating)

    return out.sort_values("value_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Quick test — run directly: python analysis/scorer.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Make `data/` importable regardless of working directory
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from data.fetcher import fetch_stock_data  # noqa: E402

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 140)
    pd.set_option("display.float_format", "{:.2f}".format)

    test_symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]

    print("=" * 70)
    print(f"Scorer test — {len(test_symbols)} symbols")
    print("=" * 70)

    raw_df    = fetch_stock_data(test_symbols)
    scored_df = score_stocks(raw_df)

    display_cols = [
        "Symbol", "Company",
        "pe_score", "pb_score", "roe_score",
        "de_score", "growth_score", "week52_score",
        "value_score", "rating",
    ]
    print("\n--- Scores ---")
    print(scored_df[display_cols].to_string(index=False))

    print("\n--- Raw fundamentals ---")
    raw_cols = [
        "Symbol", "PE Ratio", "PB Ratio", "ROE (%)",
        "Debt/Equity", "Revenue Growth (%)",
        "Current Price", "52W High", "52W Low",
    ]
    print(scored_df[raw_cols].to_string(index=False))

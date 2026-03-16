import time

import streamlit as st
import yfinance as yf
import pandas as pd


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _empty_row(symbol: str) -> dict:
    """Return a row dict with all fields set to None."""
    return {
        "Symbol":              symbol,
        "Company":             None,
        "Sector":              None,
        "Current Price":       None,
        "PE Ratio":            None,
        "PB Ratio":            None,
        "ROE (%)":             None,
        "Debt/Equity":         None,
        "Revenue Growth (%)":  None,
        "52W High":            None,
        "52W Low":             None,
    }


def _has_price(info: dict) -> bool:
    """
    Return True if yfinance returned usable price data.

    On weekends and market holidays, currentPrice / regularMarketPrice are
    None because there is no live session.  previousClose and
    regularMarketPreviousClose are always populated and are used as fallback
    so the screener keeps working when markets are closed.
    """
    return bool(info) and (
        info.get("currentPrice")               is not None
        or info.get("regularMarketPrice")      is not None
        or info.get("previousClose")           is not None
        or info.get("regularMarketPreviousClose") is not None
    )


def _extract(symbol: str, info: dict) -> dict:
    """Pull every required field out of a raw yfinance info dict."""

    # --- ROE: yfinance returns decimal  (0.1543 → 15.43%) ---
    roe_raw = info.get("returnOnEquity")
    roe = round(roe_raw * 100, 2) if roe_raw is not None else None

    # --- Revenue growth: decimal (0.12 → 12%) ---
    rg_raw = info.get("revenueGrowth")
    rev_growth = round(rg_raw * 100, 2) if rg_raw is not None else None

    # --- Debt/Equity: yfinance returns ratio × 100 (45.5 → 0.455 D/E) ---
    de_raw = info.get("debtToEquity")
    de = round(de_raw / 100, 3) if de_raw is not None else None

    return {
        "Symbol":             symbol,
        "Company":            info.get("shortName") or info.get("longName"),
        "Sector":             info.get("sector"),
        "Current Price":      (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or info.get("regularMarketPreviousClose")
        ),
        "PE Ratio":           info.get("trailingPE"),
        "PB Ratio":           info.get("priceToBook"),
        "ROE (%)":            roe,
        "Debt/Equity":        de,
        "Revenue Growth (%)": rev_growth,
        "52W High":           info.get("fiftyTwoWeekHigh"),
        "52W Low":            info.get("fiftyTwoWeekLow"),
    }


# ---------------------------------------------------------------------------
# Per-symbol cached fetch
# Caching per symbol means:
#   - Each stock is cached independently for 1 hour.
#   - time.sleep() only runs on a cache MISS, never on a cache hit.
#   - Fetching 50 stocks = 50 separate cache entries.
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_one(symbol: str) -> dict:
    """
    Fetch and cache fundamental data for a single symbol.

    The 300 ms sleep acts as rate-limiting — it only executes when the
    cache entry is cold (first fetch or post-expiry re-fetch).
    """
    time.sleep(0.3)  # polite delay — runs only on cache miss
    row = _empty_row(symbol)

    try:
        info = yf.Ticker(symbol).info

        if _has_price(info):
            row = _extract(symbol, info)
        else:
            print(f"  └─ {symbol}: No market data — symbol may be invalid or delisted")

    except Exception as exc:
        print(f"  └─ {symbol}: Error — {exc}")

    return row


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def clear_cache() -> None:
    """Clear all per-symbol cached data, forcing a fresh fetch next time."""
    _fetch_one.clear()


def fetch_stock_data(
    symbols: list,
    progress_callback=None,
) -> pd.DataFrame:
    """
    Fetch fundamental data for a list of NSE .NS symbols.

    - Results cached per symbol for 1 hour via @st.cache_data(ttl=3600).
    - Processes symbols in batches of 10 to avoid overwhelming yfinance.
    - Calls progress_callback(fraction: float) after each symbol if provided.
    - Any unavailable field for any stock is returned as None — never crashes.

    Args:
        symbols:           List of NSE tickers, e.g. ["RELIANCE.NS", "TCS.NS"]
        progress_callback: Optional callable(float) — receives 0.0 → 1.0 as
                           each symbol completes.  Drives an st.progress bar
                           in the caller without coupling this module to st.*

    Returns:
        DataFrame — one row per stock, columns:
        Symbol | Company | Sector | Current Price | PE Ratio | PB Ratio |
        ROE (%) | Debt/Equity | Revenue Growth (%) | 52W High | 52W Low
    """
    rows = []
    total = len(symbols)
    batch_size = 10

    for batch_start in range(0, total, batch_size):
        batch = symbols[batch_start : batch_start + batch_size]

        for symbol in batch:
            print(f"Fetching {symbol}...")
            row = _fetch_one(symbol)
            rows.append(row)

            if progress_callback is not None:
                progress_callback(len(rows) / total)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Quick test — run directly: python data/fetcher.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)
    pd.set_option("display.float_format", "{:.2f}".format)

    test_symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]

    print("=" * 60)
    print(f"Test fetch — {len(test_symbols)} symbols")
    print("=" * 60)

    fetched = 0

    def _print_progress(frac: float) -> None:
        global fetched
        fetched += 1
        print(f"  Progress: {frac:.0%}  ({fetched}/{len(test_symbols)})")

    df = fetch_stock_data(test_symbols, progress_callback=_print_progress)

    print("\n--- Result ---")
    print(df.to_string(index=False))
    print(f"\nShape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"Null counts:\n{df.isnull().sum().to_string()}")

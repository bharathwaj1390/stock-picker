# NSE stock symbol lists with .NS suffix for yfinance.
# Constituents are accurate as of early 2025.
# NSE rebalances indices quarterly — verify at https://www.nseindia.com if needed.

NIFTY_50 = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS",
    "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS",
    "BEL.NS", "BHARTIARTL.NS", "BPCL.NS", "BRITANNIA.NS",
    "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS", "EICHERMOT.NS",
    "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
    "INDUSINDBK.NS", "INFY.NS", "ITC.NS", "JSWSTEEL.NS",
    "KOTAKBANK.NS", "LT.NS", "M&M.NS", "MARUTI.NS",
    "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS",
    "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SHRIRAMFIN.NS",
    "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TCS.NS", "TECHM.NS", "TITAN.NS", "TRENT.NS",
    "ULTRACEMCO.NS", "WIPRO.NS",
]

NIFTY_MIDCAP_50 = [
    "ABB.NS", "ABCAPITAL.NS", "ALKEM.NS", "ASHOKLEY.NS",
    "ASTRAL.NS", "AUBANK.NS", "BALKRISIND.NS", "BANDHANBNK.NS",
    "BHARATFORG.NS", "BHEL.NS", "BIOCON.NS", "CANBK.NS",
    "CHOLAFIN.NS", "COFORGE.NS", "CONCOR.NS", "CUMMINSIND.NS",
    "DALBHARAT.NS", "DEEPAKNTR.NS", "DIXON.NS", "ESCORTS.NS",
    "FEDERALBNK.NS", "GLENMARK.NS", "GMRINFRA.NS", "GODREJCP.NS",
    "GODREJPROP.NS", "HINDPETRO.NS", "IDFCFIRSTB.NS", "INDHOTEL.NS",
    "INDIAMART.NS", "IRCTC.NS", "JUBLFOOD.NS", "KPITTECH.NS",
    "LICHSGFIN.NS", "LUPIN.NS", "MFSL.NS", "MPHASIS.NS",
    "NAUKRI.NS", "OBEROIRLTY.NS", "PAGEIND.NS", "PERSISTENT.NS",
    "PIIND.NS", "POLYCAB.NS", "RECLTD.NS", "SAIL.NS",
    "SOLARINDS.NS", "SUPREMEIND.NS", "TATACOMM.NS", "TORNTPHARM.NS",
    "VOLTAS.NS", "ZYDUSLIFE.NS",
]

NIFTY_SMALLCAP_50 = [
    "AARTIIND.NS", "ANGELONE.NS", "APTUS.NS", "BAJAJELEC.NS",
    "BSE.NS", "CANFINHOME.NS", "CDSL.NS", "CENTURYPLY.NS",
    "CLEAN.NS", "CREDITACC.NS", "DCBBANK.NS", "ELECON.NS",
    "FINPIPE.NS", "GMMPFAUDLR.NS", "GRINDWELL.NS", "HAPPSTMNDS.NS",
    "HFCL.NS", "HOMEFIRST.NS", "IEX.NS", "IIFL.NS",
    "JINDALSAW.NS", "JKCEMENT.NS", "JKPAPER.NS", "JSWENERGY.NS",
    "KFINTECH.NS", "KNRCON.NS", "KRBL.NS", "LATENTVIEW.NS",
    "MANAPPURAM.NS", "MAHINDCIE.NS", "MARKSANS.NS", "METROPOLIS.NS",
    "NAVINFLUOR.NS", "OLECTRA.NS", "ORIENTELEC.NS", "PNBHOUSING.NS",
    "POLICYBZR.NS", "RATNAMANI.NS", "RKFORGE.NS", "SAFARI.NS",
    "SBFC.NS", "SHYAMMETL.NS", "SONACOMS.NS", "STLTECH.NS",
    "SURYAROSNI.NS", "TATAINVEST.NS", "VGUARD.NS", "WELCORP.NS",
    "CRAFTSMAN.NS", "HAPPYFRG.NS",
]

_INDEX_MAP = {
    "Large Cap (Nifty 50)":        NIFTY_50,
    "Mid Cap (Nifty Midcap 50)":   NIFTY_MIDCAP_50,
    "Small Cap (Nifty Smallcap 50)": NIFTY_SMALLCAP_50,
}


def get_symbols(cap_type: str) -> list[str]:
    """Return the symbol list for the given index label.

    Args:
        cap_type: One of "Large Cap (Nifty 50)",
                  "Mid Cap (Nifty Midcap 50)",
                  "Small Cap (Nifty Smallcap 50)"

    Returns:
        List of NSE ticker strings with .NS suffix.

    Raises:
        ValueError: if cap_type is not one of the three known strings.
    """
    if cap_type not in _INDEX_MAP:
        raise ValueError(
            f"Unknown index '{cap_type}'. "
            f"Expected one of: {list(_INDEX_MAP.keys())}"
        )
    return _INDEX_MAP[cap_type]

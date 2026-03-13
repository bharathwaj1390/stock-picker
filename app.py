import streamlit as st
import pandas as pd
from datetime import datetime

from data.stocks import get_symbols
from data.fetcher import fetch_stock_data, clear_cache
from analysis.scorer import score_stocks

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset ── */
footer { visibility: hidden; }
.block-container { padding: 1.2rem 2rem 3rem !important; max-width: 1400px; }

/* ── Full-page background: deep navy + subtle candlestick SVG tile + grid lines + depth glows ── */
.stApp {
    background-color: #0a1628;
    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='100'%3E%3Cline x1='20' y1='10' x2='20' y2='90' stroke='%2300d4aa' stroke-width='1.5' stroke-opacity='0.13'/%3E%3Crect x='14' y='30' width='12' height='40' fill='%2300d4aa' fill-opacity='0.06' stroke='%2300d4aa' stroke-width='1' stroke-opacity='0.16' rx='1'/%3E%3Cline x1='55' y1='15' x2='55' y2='85' stroke='%23ef5350' stroke-width='1.5' stroke-opacity='0.13'/%3E%3Crect x='49' y='20' width='12' height='45' fill='%23ef5350' fill-opacity='0.06' stroke='%23ef5350' stroke-width='1' stroke-opacity='0.16' rx='1'/%3E%3Cline x1='90' y1='20' x2='90' y2='80' stroke='%2300d4aa' stroke-width='1.5' stroke-opacity='0.13'/%3E%3Crect x='84' y='32' width='12' height='30' fill='%2300d4aa' fill-opacity='0.06' stroke='%2300d4aa' stroke-width='1' stroke-opacity='0.16' rx='1'/%3E%3Cline x1='130' y1='12' x2='130' y2='75' stroke='%2300d4aa' stroke-width='1.5' stroke-opacity='0.13'/%3E%3Crect x='124' y='25' width='12' height='35' fill='%2300d4aa' fill-opacity='0.06' stroke='%2300d4aa' stroke-width='1' stroke-opacity='0.16' rx='1'/%3E%3Cpolyline points='5,65 38,52 70,44 105,38 148,28' fill='none' stroke='%23f0b429' stroke-width='1.5' stroke-opacity='0.13'/%3E%3C/svg%3E"),
        repeating-linear-gradient(0deg, transparent, transparent 59px, rgba(0,212,170,0.025) 60px),
        radial-gradient(ellipse 80% 55% at 0% 0%, rgba(0,160,120,0.12) 0%, transparent 65%),
        radial-gradient(ellipse 60% 70% at 100% 100%, rgba(0,50,130,0.14) 0%, transparent 65%),
        linear-gradient(155deg, #0d1b2e 0%, #07101e 55%, #040b17 100%);
    background-size: 160px 100px, auto, auto, auto, auto;
    background-attachment: fixed;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(185deg, #05091a 0%, #030712 100%);
    border-right: 1px solid #0d2035;
    box-shadow: 3px 0 20px rgba(0,0,0,0.6);
}

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, rgba(0,55,40,0.35) 0%, rgba(0,30,65,0.28) 55%, rgba(5,15,30,0.2) 100%);
    border: 1px solid rgba(0,212,170,0.2);
    border-radius: 18px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.3rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    overflow: hidden;
    position: relative;
    box-shadow: 0 8px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(0,212,170,0.08);
}
.hero-banner::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse 60% 80% at 0% 50%, rgba(0,212,170,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.hero-eyebrow {
    font-size: .65rem; text-transform: uppercase; letter-spacing: 2px;
    color: #00d4aa; font-weight: 700; margin-bottom: .55rem;
    display: flex; align-items: center; gap: 8px;
}
.hero-dot {
    width: 7px; height: 7px; background: #00d4aa; border-radius: 50%;
    box-shadow: 0 0 8px #00d4aa;
    animation: blink 2s ease-in-out infinite;
}
@keyframes blink { 0%,100% { opacity:1; box-shadow: 0 0 8px #00d4aa; } 50% { opacity:.2; box-shadow: none; } }
.page-title {
    font-size: 2.6rem; font-weight: 900; line-height: 1.1; letter-spacing: -.6px; margin: 0;
    background: linear-gradient(100deg, #ffffff 20%, #b2f0e0 55%, #00d4aa 85%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.page-subtitle { font-size: .76rem; color: #ff6b6b; font-weight: 600; margin: .4rem 0 0; opacity: .88; }
.hero-chart { opacity: .2; flex-shrink: 0; margin-left: 2rem; }

/* ── Stat cards ── */
.stat-card {
    background: linear-gradient(145deg, rgba(10,20,38,0.92) 0%, rgba(6,12,26,0.96) 100%);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.055);
    border-radius: 13px;
    padding: 1rem 1.1rem;
    text-align: center;
    border-top: 3px solid transparent;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
    transition: transform .2s, box-shadow .2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.6); }
.stat-card.c-total { border-top-color: #00d4aa; }
.stat-card.c-sbuy  { border-top-color: #00e676; }
.stat-card.c-buy   { border-top-color: #26c97a; }
.stat-card.c-hold  { border-top-color: #f0b429; }
.stat-card.c-avoid { border-top-color: #ff5252; }
.stat-card.c-gap   { border-top-color: #3d5a6e; }
.s-val { font-size: 2.1rem; font-weight: 900; line-height: 1; margin-bottom: .2rem; }
.c-total .s-val { color: #00d4aa; text-shadow: 0 0 22px rgba(0,212,170,0.45); }
.c-sbuy  .s-val { color: #00e676; text-shadow: 0 0 22px rgba(0,230,118,0.4); }
.c-buy   .s-val { color: #26c97a; }
.c-hold  .s-val { color: #f0b429; text-shadow: 0 0 22px rgba(240,180,41,0.35); }
.c-avoid .s-val { color: #ff5252; text-shadow: 0 0 22px rgba(255,82,82,0.35); }
.c-gap   .s-val { color: #6a9ab5; }
.s-lbl { font-size: .62rem; text-transform: uppercase; letter-spacing: .9px; color: #6a8fa5; font-weight: 700; }

/* ── Pick cards ── */
.pick-card {
    background: linear-gradient(145deg, rgba(9,18,36,0.96) 0%, rgba(5,11,22,0.98) 100%);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.2rem 1.1rem 1.1rem;
    height: 100%;
    position: relative;
    overflow: hidden;
    transition: border-color .25s, transform .25s, box-shadow .25s;
    box-shadow: 0 8px 32px rgba(0,0,0,0.55);
}
.pick-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #00d4aa 0%, rgba(0,212,170,0.25) 60%, transparent 100%);
}
.pick-card:hover {
    border-color: rgba(0,212,170,0.35);
    transform: translateY(-4px);
    box-shadow: 0 16px 45px rgba(0,0,0,0.65), 0 0 25px rgba(0,212,170,0.08);
}
.pick-rank  { font-size: .6rem; font-weight: 700; color: #5a8099; text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: .3rem; }
.pick-sym   { font-size: 1.18rem; font-weight: 800; color: #eaf4fc; line-height: 1.15; }
.pick-co    { font-size: .7rem; color: #7a9ab5; margin: .1rem 0 .5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pick-score { font-size: 2.9rem; font-weight: 900; color: #e0f0fa; line-height: 1; text-shadow: 0 0 28px rgba(0,212,170,0.18); }
.pick-score small { font-size: .85rem; font-weight: 400; color: #5a8099; }
.pick-badge { display: inline-block; font-size: .62rem; font-weight: 800; text-transform: uppercase; letter-spacing: .7px; padding: .23rem .75rem; border-radius: 5px; margin: .35rem 0 .6rem; }
.b-sb { background: rgba(0,90,45,0.5); color: #00e676; border: 1px solid rgba(0,230,118,0.3); }
.b-b  { background: rgba(0,65,32,0.5); color: #26c97a; border: 1px solid rgba(38,201,122,0.25); }
.b-h  { background: rgba(90,55,0,0.5); color: #f0b429; border: 1px solid rgba(240,180,41,0.3); }
.b-av { background: rgba(90,0,0,0.5); color: #ff5252; border: 1px solid rgba(255,82,82,0.3); }
.pick-mets  { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: .6rem; }
.pm { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: .14rem .45rem; font-size: .64rem; color: #8aafc5; }
.pm b { color: #c5dce8; font-weight: 700; }
.pick-sep   { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: .55rem 0; }
.pick-reason { font-size: .7rem; color: #8aafc5; line-height: 1.5; }

/* ── Section headers ── */
.sec-head {
    font-size: .78rem; font-weight: 800; color: #7ab8d0;
    text-transform: uppercase; letter-spacing: 1.2px;
    display: flex; align-items: center; gap: 8px; margin: 1.5rem 0 .75rem;
}
.sec-head::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(0,212,170,0.15) 0%, transparent 60%); margin-left: 4px; }

/* ── Legend ── */
.legend-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: .75rem; }
.lc { display: inline-flex; align-items: center; gap: 5px; padding: .2rem .65rem; border-radius: 4px; font-size: .7rem; font-weight: 600; }
.lc-g { background: rgba(27,94,32,0.4); color: #81c784; border: 1px solid rgba(46,125,50,0.3); }
.lc-y { background: rgba(123,79,0,0.4); color: #ffd54f; border: 1px solid rgba(249,168,37,0.3); }
.lc-r { background: rgba(123,0,0,0.4); color: #e57373; border: 1px solid rgba(198,40,40,0.3); }

/* ── Column guide grid ── */
.col-guide { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin: .5rem 0 1rem; }
.cg-card {
    background: rgba(8,16,32,0.85); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: .8rem .75rem;
    border-top: 2px solid rgba(0,212,170,0.3);
}
.cg-abbr { font-size: .9rem; font-weight: 800; color: #c8e4f0; margin-bottom: .12rem; }
.cg-full { font-size: .6rem; color: #00d4aa; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; margin-bottom: .4rem; }
.cg-desc { font-size: .66rem; color: #9abccc; line-height: 1.45; margin-bottom: .5rem; min-height: 2.6rem; }
.cg-tiers { display: flex; flex-direction: column; gap: 3px; }
.cg-t { font-size: .61rem; font-weight: 600; padding: .12rem .4rem; border-radius: 3px; }
.cg-tg { background: rgba(27,94,32,0.45); color: #81c784; }
.cg-ty { background: rgba(110,70,0,0.45); color: #ffd54f; }
.cg-tr { background: rgba(110,0,0,0.45); color: #e57373; }

/* ── Sidebar ── */
.sb-brand { padding: .6rem 0 .9rem; border-bottom: 1px solid rgba(0,212,170,0.12); margin-bottom: .9rem; }
.sb-title { font-size: 1rem; font-weight: 800; color: #e0f0fa; line-height: 1.2; }
.sb-tagline { font-size: .65rem; color: #00d4aa; text-transform: uppercase; letter-spacing: .8px; font-weight: 600; margin-top: .2rem; }
.sb-step { display: flex; gap: 9px; align-items: flex-start; margin-bottom: .6rem; }
.sb-num {
    background: rgba(0,212,170,0.1); color: #00d4aa; border: 1px solid rgba(0,212,170,0.28);
    border-radius: 50%; width: 20px; height: 20px; min-width: 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: .62rem; font-weight: 800; margin-top: 1px;
}
.sb-text { font-size: .76rem; color: #8aafc5; line-height: 1.45; }
.info-pill {
    background: rgba(0,212,170,0.04); border: 1px solid rgba(0,212,170,0.1);
    border-radius: 10px; padding: .7rem .9rem; font-size: .71rem; color: #8aafc5; line-height: 1.6; margin-top: .5rem;
}

/* ── Stock Insights panel ── */
.insight-wrap {
    background: linear-gradient(145deg, rgba(8,16,32,0.97) 0%, rgba(5,10,22,0.99) 100%);
    border: 1px solid rgba(0,212,170,0.22);
    border-radius: 16px; padding: 1.5rem 1.8rem; margin-top: .5rem;
    box-shadow: 0 8px 36px rgba(0,0,0,0.55);
}
.insight-hdr {
    display: flex; justify-content: space-between; align-items: flex-start;
    padding-bottom: 1.1rem; margin-bottom: 1.1rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.insight-sym  { font-size: 1.7rem; font-weight: 900; color: #eaf4fc; line-height: 1; }
.insight-co   { font-size: .8rem;  color: #7a9ab5; margin-top: .25rem; }
.insight-right { text-align: right; }
.insight-big  { font-size: 2.5rem; font-weight: 900; color: #e0f0fa; line-height: 1; }
.insight-big small { font-size: .9rem; font-weight: 400; color: #5a8099; }
.factor-row {
    display: grid; grid-template-columns: 130px 1fr 52px;
    align-items: center; gap: 10px; margin-bottom: .85rem;
}
.factor-name  { font-size: .74rem; font-weight: 700; color: #9abccc; }
.factor-track { background: rgba(255,255,255,0.06); border-radius: 4px; height: 7px; overflow: hidden; }
.factor-fill  { height: 100%; border-radius: 4px; }
.factor-pts   { font-size: .72rem; font-weight: 700; color: #c5dde8; text-align: right; white-space: nowrap; }
.factor-why   {
    font-size: .68rem; color: #7a9ab5; grid-column: 2 / 4;
    margin-top: -.4rem; padding-left: 2px; line-height: 1.45;
}
.insight-summary {
    margin-top: .9rem; padding-top: .9rem;
    border-top: 1px solid rgba(255,255,255,0.07);
    font-size: .79rem; color: #9abccc; line-height: 1.7;
}

/* ── Responsive grids (replaces st.columns for stats + picks) ── */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 10px;
    margin: 1rem 0 1.5rem;
}
.picks-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 1rem;
}

/* ── Breakpoint: large tablet (≤ 1100px) ── */
@media (max-width: 1100px) {
    .picks-grid { grid-template-columns: repeat(3, 1fr); }
}

/* ── Breakpoint: tablet (≤ 900px) ── */
@media (max-width: 900px) {
    .stats-grid { grid-template-columns: repeat(3, 1fr); }
    .col-guide  { grid-template-columns: repeat(4, 1fr); }
}

/* ── Breakpoint: small tablet / large phone (≤ 768px) ── */
@media (max-width: 768px) {
    .block-container { padding: 0.8rem 0.8rem 2rem !important; }
    .hero-chart  { display: none; }
    .hero-banner { padding: 1.1rem 1.2rem; border-radius: 12px; }
    .page-title  { font-size: 1.65rem; letter-spacing: -.3px; }
    .hero-eyebrow { font-size: .6rem; letter-spacing: 1.2px; }
    .col-guide   { grid-template-columns: repeat(3, 1fr); }
    .cg-desc     { min-height: unset; }
    .insight-wrap { padding: 1rem 1.1rem; }
    .factor-row  { grid-template-columns: 100px 1fr 44px; gap: 8px; }
}

/* ── Breakpoint: phone landscape (≤ 640px) ── */
@media (max-width: 640px) {
    .picks-grid { grid-template-columns: repeat(2, 1fr); }
}

/* ── Breakpoint: phone portrait (≤ 480px) ── */
@media (max-width: 480px) {
    .block-container { padding: 0.5rem 0.5rem 2rem !important; }
    .hero-banner { padding: .9rem 1rem; border-radius: 10px; }
    .page-title  { font-size: 1.3rem; letter-spacing: -.2px; }
    .hero-eyebrow { font-size: .55rem; letter-spacing: 1px; }
    .page-subtitle { font-size: .7rem; }
    .stats-grid  { grid-template-columns: repeat(2, 1fr); }
    .picks-grid  { grid-template-columns: repeat(2, 1fr); }
    .col-guide   { grid-template-columns: repeat(2, 1fr); }
    .pick-score  { font-size: 2.2rem; }
    .factor-row  { grid-template-columns: 82px 1fr 40px; gap: 7px; }
    .factor-name { font-size: .65rem; }
    .insight-wrap { padding: .85rem .9rem; }
    .insight-sym  { font-size: 1.4rem; }
    .insight-big  { font-size: 2rem; }
    .sec-head    { font-size: .7rem; }
    .s-val       { font-size: 1.7rem; }
}

/* ── Scrollable stocks table — sticky left columns ── */
.table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}
.stocks-table {
    width: 100%;
    border-collapse: collapse;
    font-size: .8rem;
}
.stocks-table th {
    background: rgba(5,12,28,0.99);
    color: #7ab8d0;
    font-size: .64rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .6px;
    padding: .72rem .6rem;
    box-shadow: 0 2px 0 rgba(0,212,170,0.18);
    white-space: nowrap;
    text-align: right;
    position: sticky;
    top: 0;
    z-index: 3;
}
.stocks-table th:nth-child(-n+3) { text-align: left; }
/* CSS variable drives row background — inherited by every td including sticky ones */
.stocks-table tbody tr          { --rbg: #080f1e; }
.stocks-table tbody tr:nth-child(even) { --rbg: #0b1425; }
.stocks-table tbody tr:hover    { --rbg: rgba(0,212,170,0.07); }
.stocks-table td {
    padding: .55rem .6rem;
    white-space: nowrap;
    text-align: right;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    background: var(--rbg);
    color: #c5dce8;
}
.stocks-table td:nth-child(-n+3) { text-align: left; }
/* Sticky columns — left offsets match min-widths below */
.sc-rank {
    position: sticky; left: 0; z-index: 2;
    min-width: 34px; width: 34px;
    text-align: center !important;
    color: #5a8099; font-size: .72rem;
}
.sc-sym {
    position: sticky; left: 34px; z-index: 2;
    min-width: 62px; width: 62px;
    font-weight: 700; color: #eaf4fc !important;
}
.sc-co {
    position: sticky; left: 96px; z-index: 2;
    min-width: 118px; width: 118px;
    max-width: 118px; overflow: hidden; text-overflow: ellipsis;
    color: #9abccc !important;
    border-right: 1px solid rgba(0,212,170,0.14) !important;
    font-size: .76rem;
}
/* Header sticky cells need higher z-index and explicit bg */
.stocks-table thead .sc-rank,
.stocks-table thead .sc-sym,
.stocks-table thead .sc-co {
    z-index: 4;
    background: rgba(5,12,28,0.99) !important;
}

/* ── Score guide (expander) ── */
.sg-intro { font-size: .75rem; color: #9abccc; line-height: 1.6; margin-bottom: .9rem; }
.sg-grid  {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px; margin-bottom: .85rem;
}
.sg-item  {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 9px; padding: .7rem .75rem;
}
.sg-name  { font-size: .78rem; font-weight: 800; color: #c8e4f0; margin-bottom: .18rem; }
.sg-desc  { font-size: .64rem; color: #7a9ab5; margin-bottom: .42rem; line-height: 1.45; min-height: 2.5rem; }
.sg-tiers { display: flex; flex-direction: column; gap: 3px; }
.sgt-g, .sgt-y, .sgt-r {
    font-size: .62rem; font-weight: 600;
    padding: .1rem .4rem; border-radius: 3px; display: inline-block;
}
.sgt-g { background: rgba(27,94,32,0.45); color: #81c784; }
.sgt-y { background: rgba(110,70,0,0.45); color: #ffd54f; }
.sgt-r { background: rgba(110,0,0,0.45); color: #e57373; }
.sg-ratings {
    display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
    padding-top: .75rem; border-top: 1px solid rgba(255,255,255,0.07);
    font-size: .72rem;
}
.sg-ratings b { color: #9abccc; margin-right: 2px; }
.sgr-sb, .sgr-b, .sgr-h, .sgr-av {
    padding: .16rem .6rem; border-radius: 4px;
    font-size: .68rem; font-weight: 700;
}
.sgr-sb, .sgr-b { color: #00e676; background: rgba(0,80,40,0.4); }
.sgr-h  { color: #f0b429; background: rgba(90,55,0,0.4); }
.sgr-av { color: #ff5252; background: rgba(80,0,0,0.4); }
@media (max-width: 768px) {
    .sg-grid { grid-template-columns: repeat(2, 1fr); }
    .sg-desc { min-height: unset; }
}
@media (max-width: 420px) {
    .sg-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
_GREEN  = "background-color: #1B5E20; color: #a5d6a7"
_YELLOW = "background-color: #7B4F00; color: #ffe082"
_RED    = "background-color: #7B0000; color: #ef9a9a"

_BADGE_CLASS = {
    "Strong Buy": "b-sb",
    "Buy":        "b-b",
    "Hold":       "b-h",
    "Avoid":      "b-av",
}


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div style="font-size:1.8rem; margin-bottom:.3rem;">📈</div>
      <div class="sb-title">NSE Stock Screener</div>
      <div class="sb-tagline">Fundamental Value Analyser</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**How to use**", help=None)
    steps = [
        ("1", "Choose an index — Large, Mid, or Small Cap."),
        ("2", "Click <b>Analyse</b> to fetch live data from Yahoo Finance."),
        ("3", "Review the <b>Top 5 Picks</b> and the full sortable table below."),
        ("4", "Click any <b>column header</b> in the table to sort."),
        ("5", "Use <b>Refresh Data</b> to clear the 1-hour cache and re-fetch."),
    ]
    for num, text in steps:
        st.markdown(
            f'<div class="sb-step"><div class="sb-num">{num}</div>'
            f'<div class="sb-text">{text}</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    if st.button("🔄 Refresh Data", use_container_width=True, type="secondary"):
        clear_cache()
        for key in ("scored_df", "last_refreshed", "index_label", "skipped_count"):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()

    st.markdown(
        '<div class="info-pill">'
        "📡 Data sourced from <b>Yahoo Finance</b> via yfinance.<br>"
        "Results are cached for <b>1 hour</b>.<br><br>"
        "⚠️ Not financial advice — for educational purposes only."
        "</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Hero banner
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <div class="hero-left">
    <div class="hero-eyebrow">
      <span class="hero-dot"></span>
      Live Market Data &nbsp;·&nbsp; NSE India
    </div>
    <h1 class="page-title">NSE Stock Screener</h1>
    <p class="page-subtitle">⚠️ Not financial advice — for educational purposes only</p>
  </div>
  <div class="hero-chart">
    <svg viewBox="0 0 300 90" width="260" height="72">
      <defs>
        <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#00d4aa" stop-opacity="0.5"/>
          <stop offset="100%" stop-color="#00d4aa" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <!-- candles -->
      <line x1="20"  y1="15" x2="20"  y2="80" stroke="#00d4aa" stroke-width="1"/>
      <rect x="14"  y="30" width="12" height="35" fill="#00d4aa" rx="1"/>
      <line x1="55"  y1="20" x2="55"  y2="75" stroke="#ef5350" stroke-width="1"/>
      <rect x="49"  y="22" width="12" height="40" fill="#ef5350" rx="1"/>
      <line x1="90"  y1="25" x2="90"  y2="70" stroke="#00d4aa" stroke-width="1"/>
      <rect x="84"  y="34" width="12" height="25" fill="#00d4aa" rx="1"/>
      <line x1="125" y1="18" x2="125" y2="65" stroke="#00d4aa" stroke-width="1"/>
      <rect x="119" y="26" width="12" height="30" fill="#00d4aa" rx="1"/>
      <line x1="160" y1="12" x2="160" y2="60" stroke="#ef5350" stroke-width="1"/>
      <rect x="154" y="14" width="12" height="32" fill="#ef5350" rx="1"/>
      <line x1="195" y1="8"  x2="195" y2="55" stroke="#00d4aa" stroke-width="1"/>
      <rect x="189" y="12" width="12" height="28" fill="#00d4aa" rx="1"/>
      <line x1="230" y1="5"  x2="230" y2="50" stroke="#00d4aa" stroke-width="1"/>
      <rect x="224" y="9"  width="12" height="24" fill="#00d4aa" rx="1"/>
      <line x1="265" y1="2"  x2="265" y2="46" stroke="#00d4aa" stroke-width="1"/>
      <rect x="259" y="5"  width="12" height="22" fill="#00d4aa" rx="1"/>
      <!-- trend line + fill -->
      <polyline points="0,82 35,70 70,62 105,55 140,46 175,38 210,28 245,20 285,10"
                fill="none" stroke="#00d4aa" stroke-width="2"/>
      <polygon  points="0,82 35,70 70,62 105,55 140,46 175,38 210,28 245,20 285,10 285,90 0,90"
                fill="url(#cg)"/>
    </svg>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Controls
# ─────────────────────────────────────────────────────────────────────────────
col_sel, col_btn = st.columns([4, 1])

with col_sel:
    index_choice = st.selectbox(
        "Select Index",
        options=[
            "Large Cap (Nifty 50)",
            "Mid Cap (Nifty Midcap 50)",
            "Small Cap (Nifty Smallcap 50)",
        ],
        label_visibility="visible",
    )

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)  # vertical align with label
    analyse = st.button("⚡ Analyse", type="primary", use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _color(score) -> str:
    try:
        s = float(score)
    except (TypeError, ValueError):
        return ""
    if s >= 7: return _GREEN
    if s >= 4: return _YELLOW
    return _RED


def _reason(row: pd.Series) -> str:
    candidates = []
    pe,  pe_s  = row.get("PE Ratio"),           row.get("pe_score",     5)
    pb,  pb_s  = row.get("PB Ratio"),            row.get("pb_score",     5)
    roe, roe_s = row.get("ROE (%)"),             row.get("roe_score",    5)
    de,  de_s  = row.get("Debt/Equity"),         row.get("de_score",     5)
    gr,  gr_s  = row.get("Revenue Growth (%)"),  row.get("growth_score", 5)
    w52_s      = row.get("week52_score", 5)

    if pe_s  >= 8 and pd.notna(pe):
        candidates.append((pe_s,  f"low P/E of {pe:.1f}"))
    if pb_s  >= 8 and pd.notna(pb):
        txt = "trades below book value" if pb < 1 else f"attractive P/B of {pb:.1f}"
        candidates.append((pb_s,  txt))
    if roe_s >= 8 and pd.notna(roe):
        candidates.append((roe_s, f"strong ROE of {roe:.1f}%"))
    if de_s  >= 8 and pd.notna(de):
        candidates.append((de_s,  f"low debt (D/E {de:.2f})"))
    if gr_s  >= 8 and pd.notna(gr):
        candidates.append((gr_s,  f"revenue growth of {gr:.1f}%"))
    if w52_s >= 8:
        candidates.append((w52_s, "trading near its 52-week low"))

    candidates.sort(reverse=True)
    phrases = [p for _, p in candidates][:2]

    if not phrases:
        return f"Solid overall score of {row.get('value_score', 5):.1f}/10 across all six factors."
    if len(phrases) == 1:
        return f"{phrases[0].capitalize()} makes this an attractive pick."
    return f"{phrases[0].capitalize()} combined with {phrases[1]}."


def _fmt(val, fmt: str) -> str:
    return fmt.format(val) if pd.notna(val) else "—"


def _render_stats(scored_df: pd.DataFrame, skipped: int) -> None:
    n_sb  = int((scored_df["rating"] == "Strong Buy").sum())
    n_b   = int((scored_df["rating"] == "Buy").sum())
    n_h   = int((scored_df["rating"] == "Hold").sum())
    n_av  = int((scored_df["rating"] == "Avoid").sum())
    n_tot = len(scored_df)

    items = [
        ("c-total", n_tot,  "Stocks Analysed"),
        ("c-sbuy",  n_sb,   "Strong Buy"),
        ("c-buy",   n_b,    "Buy"),
        ("c-hold",  n_h,    "Hold"),
        ("c-avoid", n_av,   "Avoid"),
        ("c-gap",   skipped,"Data N/A"),
    ]
    cards = "".join(
        f'<div class="stat-card {css}">'
        f'<div class="s-val">{val}</div>'
        f'<div class="s-lbl">{lbl}</div>'
        f'</div>'
        for css, val, lbl in items
    )
    st.markdown(f'<div class="stats-grid">{cards}</div>', unsafe_allow_html=True)


def _render_top5(scored_df: pd.DataFrame) -> None:
    top5  = scored_df.head(5)
    cards = ""

    for i, (_, row) in enumerate(top5.iterrows()):
        rating  = row.get("rating", "Hold")
        bcls    = _BADGE_CLASS.get(rating, "b-h")
        symbol  = str(row["Symbol"]).replace(".NS", "")
        company = (row.get("Company") or "")[:30]

        pe_s  = _fmt(row.get("PE Ratio"),           "{:.1f}")
        roe_s = _fmt(row.get("ROE (%)"),             "{:.1f}%")
        de_s  = _fmt(row.get("Debt/Equity"),         "{:.2f}")
        gr_s  = _fmt(row.get("Revenue Growth (%)"),  "{:.1f}%")

        cards += (
            f'<div class="pick-card">'
            f'<div class="pick-rank">#{i + 1} &nbsp;·&nbsp; Top Pick</div>'
            f'<div class="pick-sym">{symbol}</div>'
            f'<div class="pick-co">{company or "&nbsp;"}</div>'
            f'<div class="pick-score">{row["value_score"]:.1f}<small> / 10</small></div>'
            f'<span class="pick-badge {bcls}">{rating}</span>'
            f'<div class="pick-mets">'
            f'<span class="pm"><b>P/E</b>&nbsp;{pe_s}</span>'
            f'<span class="pm"><b>ROE</b>&nbsp;{roe_s}</span>'
            f'<span class="pm"><b>D/E</b>&nbsp;{de_s}</span>'
            f'<span class="pm"><b>Rev&nbsp;Gr</b>&nbsp;{gr_s}</span>'
            f'</div>'
            f'<hr class="pick-sep">'
            f'<div class="pick-reason">{_reason(row)}</div>'
            f'</div>'
        )

    st.markdown(f'<div class="picks-grid">{cards}</div>', unsafe_allow_html=True)


def _build_table(scored_df: pd.DataFrame):
    df = scored_df.copy()

    def _52w_pos(r):
        cur, hi, lo = r["Current Price"], r["52W High"], r["52W Low"]
        if any(pd.isna(v) for v in (cur, hi, lo)):
            return None
        rng = hi - lo
        return round((cur - lo) / rng * 100, 1) if rng > 0 else None

    df["52W Pos %"] = df.apply(_52w_pos, axis=1)

    # Capture score arrays BEFORE building display — never add them to the DataFrame
    _scores = {
        "P/E":          df["pe_score"].to_numpy(),
        "P/B":          df["pb_score"].to_numpy(),
        "ROE (%)":      df["roe_score"].to_numpy(),
        "D/E":          df["de_score"].to_numpy(),
        "Rev Growth %": df["growth_score"].to_numpy(),
        "52W Pos %":    df["week52_score"].to_numpy(),
        "Value Score":  df["value_score"].to_numpy(),
    }

    _emoji = {"Strong Buy": "🟢 ", "Buy": "🟢 ", "Hold": "🟡 ", "Avoid": "🔴 "}

    # Display DataFrame — only the columns users see
    display = pd.DataFrame({
        "Rank":          range(1, len(df) + 1),
        "Symbol":        df["Symbol"].str.replace(".NS", "", regex=False),
        "Company":       df["Company"].fillna("").str.slice(0, 26),
        "P/E":           df["PE Ratio"],
        "P/B":           df["PB Ratio"],
        "ROE (%)":       df["ROE (%)"],
        "D/E":           df["Debt/Equity"],
        "Rev Growth %":  df["Revenue Growth (%)"],
        "52W Pos %":     df["52W Pos %"],
        "Value Score":   df["value_score"],
        "Rating":        df["rating"].map(lambda r: f"{_emoji.get(r, '')}{r}"),
    })

    def _apply_colors(data: pd.DataFrame) -> pd.DataFrame:
        styles = pd.DataFrame("", index=data.index, columns=data.columns)
        for col, vals in _scores.items():
            if col in styles.columns:
                styles[col] = [_color(s) for s in vals]
        return styles

    fmt = {
        "P/E":          lambda x: f"{x:.1f}"  if pd.notna(x) else "—",
        "P/B":          lambda x: f"{x:.2f}"  if pd.notna(x) else "—",
        "ROE (%)":      lambda x: f"{x:.1f}%" if pd.notna(x) else "—",
        "D/E":          lambda x: f"{x:.2f}"  if pd.notna(x) else "—",
        "Rev Growth %": lambda x: f"{x:.1f}%" if pd.notna(x) else "—",
        "52W Pos %":    lambda x: f"{x:.1f}%" if pd.notna(x) else "—",
        "Value Score":  lambda x: f"{x:.2f}",
    }

    return display.style.apply(_apply_colors, axis=None).format(fmt, na_rep="—")


def _render_table_html(scored_df: pd.DataFrame) -> str:
    """
    Build a fully custom HTML table with:
    - Sticky Rank + Symbol + Company columns (always visible on horizontal scroll)
    - Compact, content-appropriate column widths
    - Green / amber / red cell colouring matching score thresholds
    """
    df = scored_df.copy()

    def _cell(score: float) -> str:
        try:
            s = float(score)
        except (TypeError, ValueError):
            return ""
        if s >= 7: return "background:#1B5E20;color:#a5d6a7"
        if s >= 4: return "background:#7B4F00;color:#ffe082"
        return "background:#7B0000;color:#ef9a9a"

    def _f(val, fmt_str: str) -> str:
        return fmt_str.format(val) if pd.notna(val) else "—"

    _r_style = {
        "Strong Buy": "color:#00e676;font-weight:800",
        "Buy":        "color:#26c97a;font-weight:800",
        "Hold":       "color:#f0b429;font-weight:700",
        "Avoid":      "color:#ff5252;font-weight:700",
    }
    _r_emoji = {"Strong Buy": "🟢", "Buy": "🟢", "Hold": "🟡", "Avoid": "🔴"}

    rows_html = ""
    for i, (_, row) in enumerate(df.iterrows()):
        symbol  = str(row["Symbol"]).replace(".NS", "")
        company = str(row.get("Company") or "")[:22]
        rating  = str(row.get("rating", "Hold"))
        w52pos  = _52w_pct(row)

        pe  = _f(row.get("PE Ratio"),           "{:.1f}")
        pb  = _f(row.get("PB Ratio"),            "{:.2f}")
        roe = _f(row.get("ROE (%)"),             "{:.1f}%")
        de  = _f(row.get("Debt/Equity"),         "{:.2f}")
        gr  = _f(row.get("Revenue Growth (%)"),  "{:.1f}%")
        w52 = _f(w52pos,                         "{:.0f}%")
        vs  = f"{row.get('value_score', 0):.2f}"

        rows_html += (
            f'<tr>'
            f'<td class="sc-rank">{i + 1}</td>'
            f'<td class="sc-sym">{symbol}</td>'
            f'<td class="sc-co" title="{company}">{company}</td>'
            f'<td style="{_cell(row.get("pe_score", 5))}">{pe}</td>'
            f'<td style="{_cell(row.get("pb_score", 5))}">{pb}</td>'
            f'<td style="{_cell(row.get("roe_score", 5))}">{roe}</td>'
            f'<td style="{_cell(row.get("de_score", 5))}">{de}</td>'
            f'<td style="{_cell(row.get("growth_score", 5))}">{gr}</td>'
            f'<td style="{_cell(row.get("week52_score", 5))}">{w52}</td>'
            f'<td style="{_cell(row.get("value_score", 5))};font-weight:800">{vs}</td>'
            f'<td style="{_r_style.get(rating, "")}">'
            f'{_r_emoji.get(rating, "")} {rating}</td>'
            f'</tr>'
        )

    return (
        '<div class="table-wrapper">'
        '<table class="stocks-table">'
        '<thead><tr>'
        '<th class="sc-rank">#</th>'
        '<th class="sc-sym">Symbol</th>'
        '<th class="sc-co">Company</th>'
        '<th>P/E</th>'
        '<th>P/B</th>'
        '<th>ROE %</th>'
        '<th>D/E</th>'
        '<th>Rev Gr%</th>'
        '<th>52W Pos</th>'
        '<th>Score</th>'
        '<th>Rating</th>'
        '</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
        '</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Insight helpers
# ─────────────────────────────────────────────────────────────────────────────
def _52w_pct(row: pd.Series):
    cur, hi, lo = row.get("Current Price"), row.get("52W High"), row.get("52W Low")
    if any(pd.isna(v) for v in [cur, hi, lo]):
        return None
    rng = hi - lo
    return round((cur - lo) / rng * 100, 1) if rng > 0 else None


def _factor_explain_text(factor: str, val, score: float) -> str:
    """One-line plain-English explanation for a single scored factor."""
    na = pd.isna(val) if factor != "w52" else val is None
    if na:
        return "Data unavailable — neutral score (5/10) applied."
    if factor == "pe":
        if val <= 0:   return "Loss-making company (negative earnings) — significant concern."
        if score >= 8: return f"P/E of {val:.1f} — you pay very little per ₹1 of profit. Undervalued on earnings."
        if score >= 6: return f"P/E of {val:.1f} — fairly priced relative to earnings."
        if score >= 4: return f"P/E of {val:.1f} — earnings multiple is elevated; market is pricing in growth."
        return f"P/E of {val:.1f} — expensive multiple; limited margin of safety."
    if factor == "pb":
        if val <= 0:   return "Negative book value — structural red flag."
        if val < 1:    return f"P/B of {val:.2f} — trading below book value. Strong asset backing."
        if score >= 8: return f"P/B of {val:.2f} — modest premium to assets; reasonable valuation."
        if score >= 6: return f"P/B of {val:.2f} — fair premium to book value."
        if score >= 4: return f"P/B of {val:.2f} — elevated premium; limited downside protection from assets."
        return f"P/B of {val:.2f} — very expensive relative to assets."
    if factor == "roe":
        if score >= 8: return f"ROE of {val:.1f}% — exceptional. Management generates outstanding returns on your capital."
        if score >= 6: return f"ROE of {val:.1f}% — solid capital efficiency; above-average management quality."
        if score >= 4: return f"ROE of {val:.1f}% — average returns on shareholder equity."
        if val > 0:    return f"ROE of {val:.1f}% — below-average efficiency. Profit generation is weak."
        return f"Negative ROE ({val:.1f}%) — company is eroding shareholder value."
    if factor == "de":
        if val < 0:    return "Negative equity — indicates deep financial stress."
        if score >= 8: return f"D/E of {val:.2f} — very low debt. Robust balance sheet, resilient in downturns."
        if score >= 6: return f"D/E of {val:.2f} — moderate leverage; comfortably manageable."
        if score >= 4: return f"D/E of {val:.2f} — above-average debt; watch interest rate sensitivity."
        return f"D/E of {val:.2f} — heavily leveraged. Elevated financial risk."
    if factor == "gr":
        if score >= 8: return f"Revenue grew {val:.1f}% — rapid business expansion."
        if score >= 6: return f"Revenue grew {val:.1f}% — solid, healthy growth trajectory."
        if score >= 4: return f"Revenue grew {val:.1f}% — modest but stable growth."
        if val > 0:    return f"Revenue grew only {val:.1f}% — near-stagnant; limited business momentum."
        return f"Revenue fell {abs(val):.1f}% — business is contracting. Significant concern."
    if factor == "w52":
        if score >= 8: return f"At {val:.0f}% of its 52-week range — close to the year's low. Attractive entry window."
        if score >= 6: return f"At {val:.0f}% of its 52-week range — well below the yearly high. Decent entry."
        if score >= 4: return f"At {val:.0f}% of its 52-week range — mid-range. Neutral entry point."
        return f"At {val:.0f}% of its 52-week range — close to its 52-week high. Less attractive entry."
    return "—"


def _insight_summary(row: pd.Series, symbol: str, w52_pos) -> str:
    """Build a 2–3 sentence narrative explaining the overall rating."""
    score  = row.get("value_score", 5)
    rating = row.get("rating", "Hold")

    factors = [
        ("pe",  row.get("pe_score", 5),     row.get("PE Ratio")),
        ("pb",  row.get("pb_score", 5),     row.get("PB Ratio")),
        ("roe", row.get("roe_score", 5),    row.get("ROE (%)")),
        ("de",  row.get("de_score", 5),     row.get("Debt/Equity")),
        ("gr",  row.get("growth_score", 5), row.get("Revenue Growth (%)")),
        ("w52", row.get("week52_score", 5), w52_pos),
    ]
    strengths  = sorted([(k, s, v) for k, s, v in factors if s >= 7], key=lambda x: -x[1])
    weaknesses = sorted([(k, s, v) for k, s, v in factors if s <= 3], key=lambda x: x[1])

    def _phrase(k, v, positive):
        na = pd.isna(v) if k != "w52" else v is None
        if na: return None
        if k == "pe":  return f"low P/E of {v:.1f}" if positive else f"high P/E of {v:.1f}"
        if k == "pb":  return f"attractive P/B of {v:.2f}" if positive else f"high P/B of {v:.2f}"
        if k == "roe": return f"strong ROE of {v:.1f}%" if positive else f"weak ROE of {v:.1f}%"
        if k == "de":  return f"low debt (D/E {v:.2f})" if positive else f"high debt (D/E {v:.2f})"
        if k == "gr":  return f"revenue growth of {v:.1f}%" if positive else f"{'declining' if v < 0 else 'slow'} revenue ({v:.1f}%)"
        if k == "w52": return "trading near its 52-week low" if positive else "trading near its 52-week high"
        return None

    parts = [f"<b>{symbol}</b> scores <b>{score:.1f}/10</b>, earning a <b>{rating}</b> rating."]

    s_phrases = []
    for k, s, v in strengths[:2]:
        p = _phrase(k, v, True)
        if p: s_phrases.append(p)
    w_phrases = []
    for k, s, v in weaknesses[:1]:
        p = _phrase(k, v, False)
        if p: w_phrases.append(p)

    if s_phrases:
        parts.append(f"The score is driven by {' and '.join(s_phrases)}.")
    if w_phrases:
        parts.append(f"Main drag on the score: {w_phrases[0]}.")
    elif not s_phrases:
        parts.append("No single factor dominates — the rating reflects a balanced mix across all six metrics.")

    return " ".join(parts)


def _render_insight(row: pd.Series) -> None:
    symbol  = str(row["Symbol"]).replace(".NS", "")
    company = (row.get("Company") or "")[:50]
    score   = row.get("value_score", 5)
    rating  = row.get("rating", "Hold")
    bcls    = _BADGE_CLASS.get(rating, "b-h")
    w52_pos = _52w_pct(row)

    bar_data = [
        ("P/E Ratio",    row.get("pe_score", 5),     row.get("PE Ratio"),           "pe"),
        ("P/B Ratio",    row.get("pb_score", 5),     row.get("PB Ratio"),            "pb"),
        ("ROE (%)",      row.get("roe_score", 5),    row.get("ROE (%)"),             "roe"),
        ("Debt/Equity",  row.get("de_score", 5),     row.get("Debt/Equity"),         "de"),
        ("Rev Growth",   row.get("growth_score", 5), row.get("Revenue Growth (%)"),  "gr"),
        ("52-Week Pos.", row.get("week52_score", 5), w52_pos,                        "w52"),
    ]

    def _bar_col(s):
        if s >= 7: return "#00e676"
        if s >= 4: return "#f0b429"
        return "#ff5252"

    rows_html = ""
    for name, sc, val, key in bar_data:
        pct = sc / 10 * 100
        why = _factor_explain_text(key, val, sc)
        rows_html += (
            f'<div class="factor-row">'
            f'<div class="factor-name">{name}</div>'
            f'<div class="factor-track"><div class="factor-fill" style="width:{pct:.0f}%;background:{_bar_col(sc)};"></div></div>'
            f'<div class="factor-pts">{sc:.0f}&thinsp;/&thinsp;10</div>'
            f'<div class="factor-why">{why}</div>'
            f'</div>'
        )

    summary = _insight_summary(row, symbol, w52_pos)

    st.markdown(
        f'<div class="insight-wrap">'
        f'<div class="insight-hdr">'
        f'<div><div class="insight-sym">{symbol}</div><div class="insight-co">{company or "&nbsp;"}</div></div>'
        f'<div class="insight-right"><div class="insight-big">{score:.1f}<small> / 10</small></div>'
        f'<span class="pick-badge {bcls}" style="margin-top:.45rem;display:inline-block;">{rating}</span></div>'
        f'</div>'
        f'{rows_html}'
        f'<div class="insight-summary">{summary}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fetch on button click
# ─────────────────────────────────────────────────────────────────────────────
if analyse:
    symbols = get_symbols(index_choice)
    progress_bar = st.progress(0, text="Fetching data from Yahoo Finance…")

    try:
        raw_df = fetch_stock_data(
            symbols,
            progress_callback=lambda frac: progress_bar.progress(
                frac, text=f"Fetching data… {int(frac * 100)}%"
            ),
        )
    except Exception as exc:
        progress_bar.empty()
        st.error(f"Failed to fetch data: {exc}")
        st.stop()

    progress_bar.empty()

    if raw_df.empty:
        st.error("No data was returned. Check your internet connection and try again.")
        st.stop()

    complete_df   = raw_df[raw_df["Current Price"].notna()].copy()
    skipped_count = len(raw_df) - len(complete_df)

    if complete_df.empty:
        st.error("None of the stocks returned valid market data. Try again later.")
        st.stop()

    scored_df = score_stocks(complete_df)

    st.session_state["scored_df"]      = scored_df
    st.session_state["last_refreshed"] = datetime.now()
    st.session_state["index_label"]    = index_choice
    st.session_state["skipped_count"]  = skipped_count


# ─────────────────────────────────────────────────────────────────────────────
# Read persisted state
# ─────────────────────────────────────────────────────────────────────────────
scored_df     = st.session_state.get("scored_df")
skipped_count = st.session_state.get("skipped_count", 0)

if scored_df is None:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem;">
      <div style="font-size:3rem; margin-bottom:1rem;">📊</div>
      <div style="font-size:1.1rem; font-weight:700; color:#a0c8de; margin-bottom:.5rem;">
        No data loaded yet
      </div>
      <div style="font-size:.82rem; color:#7a9ab5;">
        Select an index above and click <b style="color:#00d4aa;">⚡ Analyse</b> to load live fundamentals.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Timestamp & alerts
# ─────────────────────────────────────────────────────────────────────────────
ts    = st.session_state.get("last_refreshed")
label = st.session_state.get("index_label", "")

col_ts, col_warn = st.columns([3, 2])
with col_ts:
    if ts:
        st.caption(
            f"📂 **{label}** &nbsp;·&nbsp; "
            f"Last refreshed: **{ts.strftime('%d %b %Y, %H:%M:%S')}**"
        )
with col_warn:
    if skipped_count > 0:
        st.warning(f"⚠️ Data unavailable for **{skipped_count}** stock(s) — excluded from results.", icon=None)

if len(scored_df) < 5:
    st.warning(f"Only **{len(scored_df)}** stocks have sufficient data — Top 5 section may be incomplete.")


# ─────────────────────────────────────────────────────────────────────────────
# Stats bar
# ─────────────────────────────────────────────────────────────────────────────
_render_stats(scored_df, skipped_count)


# ─────────────────────────────────────────────────────────────────────────────
# How scores are calculated
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("ℹ️ How scores are calculated — click to expand"):
    st.markdown("""
<div>
<p class="sg-intro">
Each stock is scored across <b>6 fundamental factors</b>, each rated <b>1–10</b>.
Missing data defaults to a neutral <b>5</b>.
The <b>Value Score</b> is the equal-weighted average of all six factors.
</p>
<div class="sg-grid">
  <div class="sg-item">
    <div class="sg-name">P/E Ratio</div>
    <div class="sg-desc">How much you pay per ₹1 of company profit. Lower is cheaper.</div>
    <div class="sg-tiers">
      <span class="sgt-g">🟢 Below 15 — cheap</span>
      <span class="sgt-y">🟡 15 – 30 — fair</span>
      <span class="sgt-r">🔴 Above 30 — expensive</span>
    </div>
  </div>
  <div class="sg-item">
    <div class="sg-name">P/B Ratio</div>
    <div class="sg-desc">Price vs book value of assets. Below 1 means trading below asset value.</div>
    <div class="sg-tiers">
      <span class="sgt-g">🟢 Below 2 — undervalued</span>
      <span class="sgt-y">🟡 2 – 5 — fair</span>
      <span class="sgt-r">🔴 Above 5 — premium</span>
    </div>
  </div>
  <div class="sg-item">
    <div class="sg-name">ROE %</div>
    <div class="sg-desc">Profit generated per ₹1 of shareholder equity. Higher = more efficient.</div>
    <div class="sg-tiers">
      <span class="sgt-g">🟢 Above 20% — excellent</span>
      <span class="sgt-y">🟡 10 – 20% — average</span>
      <span class="sgt-r">🔴 Below 10% — poor</span>
    </div>
  </div>
  <div class="sg-item">
    <div class="sg-name">D/E Ratio</div>
    <div class="sg-desc">Total debt divided by equity. Lower means less financial risk.</div>
    <div class="sg-tiers">
      <span class="sgt-g">🟢 Below 0.5 — low debt</span>
      <span class="sgt-y">🟡 0.5 – 1.5 — moderate</span>
      <span class="sgt-r">🔴 Above 2 — high risk</span>
    </div>
  </div>
  <div class="sg-item">
    <div class="sg-name">Rev Growth %</div>
    <div class="sg-desc">Year-on-year revenue change. Positive = business is expanding.</div>
    <div class="sg-tiers">
      <span class="sgt-g">🟢 Above 15% — strong</span>
      <span class="sgt-y">🟡 5 – 15% — moderate</span>
      <span class="sgt-r">🔴 Below 5% — stagnant</span>
    </div>
  </div>
  <div class="sg-item">
    <div class="sg-name">52W Position</div>
    <div class="sg-desc">Where current price sits in the 52-week range. 0% = at the year's low.</div>
    <div class="sg-tiers">
      <span class="sgt-g">🟢 Below 30% — buy zone</span>
      <span class="sgt-y">🟡 30 – 70% — mid range</span>
      <span class="sgt-r">🔴 Above 70% — near high</span>
    </div>
  </div>
</div>
<div class="sg-ratings">
  <b>Ratings:</b>
  <span class="sgr-sb">🟢 Strong Buy ≥ 8.0</span>
  <span class="sgr-b">🟢 Buy ≥ 6.0</span>
  <span class="sgr-h">🟡 Hold ≥ 4.0</span>
  <span class="sgr-av">🔴 Avoid &lt; 4.0</span>
</div>
</div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Top 5 Picks
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-head">🏆 &nbsp;Top 5 Picks</div>', unsafe_allow_html=True)
_render_top5(scored_df)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Full table
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="sec-head">📊 &nbsp;All {len(scored_df)} Stocks</div>',
    unsafe_allow_html=True,
)

# Column guide — inline card grid explaining every metric
st.markdown("""
<div class="col-guide">
  <div class="cg-card">
    <div class="cg-abbr">P/E</div>
    <div class="cg-full">Price / Earnings</div>
    <div class="cg-desc">How much you pay per ₹1 of company profit. Lower = cheaper stock.</div>
    <div class="cg-tiers">
      <span class="cg-t cg-tg">🟢 Below 15 — cheap</span>
      <span class="cg-t cg-ty">🟡 15–30 — fair</span>
      <span class="cg-t cg-tr">🔴 Above 30 — expensive</span>
    </div>
  </div>
  <div class="cg-card">
    <div class="cg-abbr">P/B</div>
    <div class="cg-full">Price / Book Value</div>
    <div class="cg-desc">How much you pay per ₹1 of company assets. Below 1 = trading below book.</div>
    <div class="cg-tiers">
      <span class="cg-t cg-tg">🟢 Below 2 — undervalued</span>
      <span class="cg-t cg-ty">🟡 2–5 — fair</span>
      <span class="cg-t cg-tr">🔴 Above 5 — premium</span>
    </div>
  </div>
  <div class="cg-card">
    <div class="cg-abbr">ROE %</div>
    <div class="cg-full">Return on Equity</div>
    <div class="cg-desc">Profit generated per ₹1 of shareholder equity. Higher = more efficient.</div>
    <div class="cg-tiers">
      <span class="cg-t cg-tg">🟢 Above 20% — excellent</span>
      <span class="cg-t cg-ty">🟡 10–20% — average</span>
      <span class="cg-t cg-tr">🔴 Below 10% — poor</span>
    </div>
  </div>
  <div class="cg-card">
    <div class="cg-abbr">D/E</div>
    <div class="cg-full">Debt / Equity</div>
    <div class="cg-desc">Total debt divided by shareholder equity. Lower = less financial risk.</div>
    <div class="cg-tiers">
      <span class="cg-t cg-tg">🟢 Below 0.5 — low debt</span>
      <span class="cg-t cg-ty">🟡 0.5–1.5 — moderate</span>
      <span class="cg-t cg-tr">🔴 Above 2 — high risk</span>
    </div>
  </div>
  <div class="cg-card">
    <div class="cg-abbr">Rev Gr%</div>
    <div class="cg-full">Revenue Growth</div>
    <div class="cg-desc">Year-on-year revenue change. Positive = business expanding.</div>
    <div class="cg-tiers">
      <span class="cg-t cg-tg">🟢 Above 15% — strong</span>
      <span class="cg-t cg-ty">🟡 5–15% — moderate</span>
      <span class="cg-t cg-tr">🔴 Below 5% — stagnant</span>
    </div>
  </div>
  <div class="cg-card">
    <div class="cg-abbr">52W Pos%</div>
    <div class="cg-full">52-Week Position</div>
    <div class="cg-desc">Where current price sits in the 52-week range. 0% = at the year's low.</div>
    <div class="cg-tiers">
      <span class="cg-t cg-tg">🟢 Below 30% — buy zone</span>
      <span class="cg-t cg-ty">🟡 30–70% — mid range</span>
      <span class="cg-t cg-tr">🔴 Above 70% — near high</span>
    </div>
  </div>
  <div class="cg-card">
    <div class="cg-abbr">Score</div>
    <div class="cg-full">Value Score / 10</div>
    <div class="cg-desc">Equal-weighted average of all 6 factors. The overall quality rating.</div>
    <div class="cg-tiers">
      <span class="cg-t cg-tg">🟢 7–10 — Strong Buy/Buy</span>
      <span class="cg-t cg-ty">🟡 4–6 — Hold</span>
      <span class="cg-t cg-tr">🔴 Below 4 — Avoid</span>
    </div>
  </div>
</div>
<div class="legend-row" style="margin-top:.25rem;">
  <span style="font-size:.68rem;color:#5a8099;font-weight:600;">Cell colours:</span>
  <span class="lc lc-g">■ Good score ≥ 7</span>
  <span class="lc lc-y">■ Neutral 4–6</span>
  <span class="lc lc-r">■ Poor &lt; 4</span>
  <span style="font-size:.68rem;color:#5a8099;margin-left:6px;">· Scroll right to see all metrics — Company name stays pinned</span>
</div>
""", unsafe_allow_html=True)

st.markdown(_render_table_html(scored_df), unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Stock Insights — per-stock rating rationale
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-head">🔍 &nbsp;Stock Insights — Why this Rating?</div>', unsafe_allow_html=True)
st.caption(
    "Select any stock below to see a factor-by-factor breakdown "
    "explaining exactly why it received its rating."
)

symbols_display = scored_df["Symbol"].str.replace(".NS", "", regex=False).tolist()

selected = st.selectbox(
    "Choose a stock",
    options=symbols_display,
    label_visibility="collapsed",
    key="insight_select",
)

if selected:
    match = scored_df[scored_df["Symbol"].str.replace(".NS", "", regex=False) == selected]
    if not match.empty:
        _render_insight(match.iloc[0])

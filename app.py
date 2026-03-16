import math
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

from data.stocks import get_symbols
from data.fetcher import fetch_stock_data, clear_cache
from analysis.scorer import score_stocks
from utils.date_utils import get_market_status
from utils.indian_formatting import format_price

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
/* ═══ RESET ═══ */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
.block-container { padding: 0 2rem 4rem !important; max-width: 1440px; }

/* ═══ BACKGROUND — deep dark purple-navy with glowing blobs ═══ */
.stApp {
    background-color: #0A0812;
    background-image:
        radial-gradient(ellipse 70% 55% at 15% 30%, rgba(109,40,217,0.28) 0%, transparent 65%),
        radial-gradient(ellipse 60% 50% at 88% 82%, rgba(168,17,72,0.28) 0%, transparent 65%);
    background-attachment: fixed;
}

/* ═══ SIDEBAR ═══ */
[data-testid="stSidebar"] > div:first-child {
    background: rgba(13,9,30,0.95);
    border-right: 1px solid rgba(139,92,246,0.15);
    box-shadow: 2px 0 24px rgba(0,0,0,0.5);
    backdrop-filter: blur(20px);
}

/* ═══ HERO ═══ */
.hero-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 3.2rem 1rem 2rem;
    position: relative;
}
.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(139,92,246,0.12);
    border: 1px solid rgba(139,92,246,0.32);
    border-radius: 50px;
    padding: .35rem 1rem .35rem .7rem;
    font-size: .68rem;
    font-weight: 600;
    color: #a78bfa;
    letter-spacing: .5px;
    margin-bottom: 1.5rem;
}
.hero-dot {
    width: 6px; height: 6px;
    background: #8b5cf6; border-radius: 50%;
    box-shadow: 0 0 10px rgba(139,92,246,0.9);
    animation: pulse 2.2s ease-in-out infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; box-shadow: 0 0 10px rgba(139,92,246,0.9); }
    50%      { opacity:.4; box-shadow: 0 0 4px rgba(139,92,246,0.3); }
}
.hero-title {
    font-size: 4rem;
    font-weight: 900;
    line-height: 1.05;
    letter-spacing: -1.5px;
    color: #f1f5f9;
    margin: 0 0 .2rem;
    text-align: center;
    width: 100%;
}
.hero-accent {
    background: linear-gradient(95deg, #8b5cf6 0%, #a855f7 40%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: .9rem;
    color: #94a3b8;
    line-height: 1.75;
    max-width: 560px;
    width: 100%;
    margin: .9rem 0 1.8rem;
    text-align: center;
}
.hero-chart-wrap {
    display: flex;
    justify-content: center;
    margin-bottom: .5rem;
}
.hero-chart-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 1.1rem 1.8rem;
    display: inline-flex;
    align-items: center;
    gap: 2rem;
    box-shadow: 0 4px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.07);
    backdrop-filter: blur(12px);
}
.hcc-stat { text-align: center; }
.hcc-val  { font-size: 1.65rem; font-weight: 900; color: #f1f5f9; line-height: 1; }
.hcc-lbl  { font-size: .57rem; color: #94a3b8; text-transform: uppercase; letter-spacing: .9px; font-weight: 700; margin-top: .25rem; }
.hcc-div  { width: 1px; height: 40px; background: rgba(255,255,255,0.10); flex-shrink: 0; }

/* ═══ STAT CARDS ═══ */
.stat-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    padding: 1.1rem 1rem;
    text-align: center;
    transition: border-color .2s, transform .2s, box-shadow .2s;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    backdrop-filter: blur(8px);
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    border-radius: 14px 14px 0 0;
}
.stat-card:hover { border-color: rgba(139,92,246,0.35); transform: translateY(-2px); box-shadow: 0 10px 28px rgba(0,0,0,0.45), 0 0 0 1px rgba(139,92,246,0.15); }
.stat-card.c-total::before  { background: linear-gradient(90deg, #8b5cf6, #ec4899); }
.stat-card.c-sbuy::before   { background: linear-gradient(90deg, #10b981, #34d399); }
.stat-card.c-buy::before    { background: linear-gradient(90deg, #34d399, #6ee7b7); }
.stat-card.c-watch::before  { background: linear-gradient(90deg, #0ea5e9, #38bdf8); }
.stat-card.c-hold::before   { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.stat-card.c-avoid::before  { background: linear-gradient(90deg, #ef4444, #f87171); }
.stat-card.c-savoid::before { background: linear-gradient(90deg, #e11d48, #f43f5e); }
.stat-card.c-gap::before    { background: rgba(255,255,255,0.15); }
.s-val { font-size: 2.1rem; font-weight: 900; line-height: 1; margin-bottom: .25rem; }
.c-total  .s-val { background: linear-gradient(135deg,#8b5cf6,#ec4899); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.c-sbuy   .s-val { color: #34d399; }
.c-buy    .s-val { color: #6ee7b7; }
.c-watch  .s-val { color: #38bdf8; }
.c-hold   .s-val { color: #fbbf24; }
.c-avoid  .s-val { color: #f87171; }
.c-savoid .s-val { color: #f43f5e; }
.c-gap    .s-val { color: #64748b; }
.s-lbl { font-size: .6rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; font-weight: 700; }

/* ═══ PICK CARDS ═══ */
.pick-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px;
    padding: 1.4rem 1.2rem 1.2rem;
    position: relative;
    overflow: hidden;
    transition: border-color .25s, transform .25s, box-shadow .25s;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    backdrop-filter: blur(8px);
}
.pick-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #8b5cf6 0%, #a855f7 50%, #ec4899 100%);
    border-radius: 18px 18px 0 0;
}
.pick-card:hover {
    border-color: rgba(139,92,246,0.45);
    transform: translateY(-5px);
    box-shadow: 0 22px 52px rgba(0,0,0,0.55), 0 0 0 1px rgba(139,92,246,0.2), 0 0 36px rgba(139,92,246,0.1);
}
.pick-rank  { font-size: .58rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: .45rem; }
.pick-sym   { font-size: 1.3rem; font-weight: 900; color: #f1f5f9; line-height: 1.1; }
.pick-co    { font-size: .68rem; color: #94a3b8; margin: .1rem 0 .55rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pick-score { font-size: 3rem; font-weight: 900; background: linear-gradient(135deg,#8b5cf6,#ec4899); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; line-height: 1; letter-spacing: -2px; }
.pick-score small { font-size: .82rem; font-weight: 400; color: #64748b; letter-spacing: 0; -webkit-text-fill-color:#64748b; }
.pick-badge { display: inline-block; font-size: .58rem; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; padding: .22rem .75rem; border-radius: 50px; margin: .4rem 0 .7rem; }
.b-sb { background: rgba(16,185,129,0.15);  color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.b-b  { background: rgba(74,222,128,0.12);  color: #4ade80; border: 1px solid rgba(74,222,128,0.28); }
.b-w  { background: rgba(56,189,248,0.12);  color: #38bdf8; border: 1px solid rgba(56,189,248,0.28); }
.b-h  { background: rgba(251,191,36,0.12);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.28); }
.b-av { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.28); }
.b-sa { background: rgba(244,63,94,0.15);   color: #f43f5e; border: 1px solid rgba(244,63,94,0.35); }
.pick-mets  { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: .7rem; }
.pm { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); border-radius: 5px; padding: .13rem .42rem; font-size: .62rem; color: #94a3b8; }
.pm b { color: #cbd5e1; font-weight: 700; }
.pick-sep   { border: none; border-top: 1px solid rgba(255,255,255,0.07); margin: .55rem 0; }
.pick-reason { font-size: .68rem; color: #94a3b8; line-height: 1.55; }

/* ═══ SECTION HEADERS ═══ */
.sec-head {
    font-size: .7rem; font-weight: 700; color: #64748b;
    text-transform: uppercase; letter-spacing: 1.8px;
    display: flex; align-items: center; gap: 10px; margin: 2rem 0 .9rem;
}
.sec-head::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(139,92,246,0.35) 0%, transparent 70%); }

/* ═══ LEGEND ═══ */
.legend-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: .8rem; }
.lc { display: inline-flex; align-items: center; gap: 5px; padding: .18rem .6rem; border-radius: 4px; font-size: .68rem; font-weight: 600; }
.lc-g { background: rgba(16,185,129,0.15);  color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.lc-y { background: rgba(251,191,36,0.12);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.28); }
.lc-r { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.28); }

/* ═══ COLUMN GUIDE ═══ */
.col-guide { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin: .5rem 0 1rem; }
.cg-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 11px; padding: .85rem .8rem;
    border-top: 2px solid rgba(139,92,246,0.55);
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    backdrop-filter: blur(8px);
}
.cg-abbr { font-size: .92rem; font-weight: 800; color: #f1f5f9; margin-bottom: .12rem; }
.cg-full { font-size: .58rem; color: #a78bfa; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; margin-bottom: .4rem; }
.cg-desc { font-size: .64rem; color: #94a3b8; line-height: 1.5; margin-bottom: .5rem; min-height: 2.6rem; }
.cg-tiers { display: flex; flex-direction: column; gap: 3px; }
.cg-t  { font-size: .6rem; font-weight: 600; padding: .1rem .38rem; border-radius: 3px; }
.cg-tg { background: rgba(16,185,129,0.15);  color: #34d399; }
.cg-ty { background: rgba(251,191,36,0.12);  color: #fbbf24; }
.cg-tr { background: rgba(248,113,113,0.12); color: #f87171; }

/* ═══ SIDEBAR COMPONENTS ═══ */
.sb-brand { padding: .6rem 0 .9rem; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: .9rem; }
.sb-title { font-size: .95rem; font-weight: 800; color: #f1f5f9; line-height: 1.2; }
.sb-tagline { font-size: .6rem; color: #a78bfa; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-top: .25rem; }
.sb-step { display: flex; gap: 9px; align-items: flex-start; margin-bottom: .6rem; }
.sb-num {
    background: rgba(139,92,246,0.15); color: #a78bfa; border: 1px solid rgba(139,92,246,0.32);
    border-radius: 50%; width: 20px; height: 20px; min-width: 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: .6rem; font-weight: 800; margin-top: 1px;
}
.sb-text { font-size: .73rem; color: #94a3b8; line-height: 1.5; }
.info-pill {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: .7rem .9rem; font-size: .7rem; color: #94a3b8; line-height: 1.65; margin-top: .5rem;
}

/* ═══ STOCK INSIGHTS PANEL ═══ */
.insight-wrap {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px; padding: 1.6rem 1.8rem; margin-top: .5rem;
    box-shadow: 0 4px 28px rgba(0,0,0,0.45);
    backdrop-filter: blur(12px);
}
.insight-hdr {
    display: flex; justify-content: space-between; align-items: flex-start;
    padding-bottom: 1.1rem; margin-bottom: 1.1rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.insight-sym  { font-size: 1.8rem; font-weight: 900; color: #f1f5f9; line-height: 1; letter-spacing: -.5px; }
.insight-co   { font-size: .78rem; color: #94a3b8; margin-top: .3rem; }
.insight-right { text-align: right; }
.insight-big  { font-size: 2.6rem; font-weight: 900; background: linear-gradient(135deg,#8b5cf6,#ec4899); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; line-height: 1; letter-spacing: -1px; }
.insight-big small { font-size: .85rem; font-weight: 400; color: #64748b; -webkit-text-fill-color:#64748b; }
.factor-row {
    display: grid; grid-template-columns: 130px 1fr 52px;
    align-items: center; gap: 10px; margin-bottom: .85rem;
}
.factor-name  { font-size: .73rem; font-weight: 700; color: #94a3b8; }
.factor-track { background: rgba(255,255,255,0.08); border-radius: 4px; height: 6px; overflow: hidden; }
.factor-fill  { height: 100%; border-radius: 4px; }
.factor-pts   { font-size: .72rem; font-weight: 700; color: #cbd5e1; text-align: right; white-space: nowrap; }
.factor-why   {
    font-size: .67rem; color: #94a3b8; grid-column: 2 / 4;
    margin-top: -.35rem; padding-left: 2px; line-height: 1.45;
}
.insight-summary {
    margin-top: .9rem; padding-top: .9rem;
    border-top: 1px solid rgba(255,255,255,0.07);
    font-size: .78rem; color: #94a3b8; line-height: 1.7;
}

/* ═══ RESPONSIVE GRIDS ═══ */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 10px;
    margin: .5rem 0 2rem;
}
.picks-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
    margin-bottom: 1.5rem;
}

@media (max-width: 1100px) { .picks-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px)  {
    .stats-grid { grid-template-columns: repeat(4, 1fr); }
    .col-guide  { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 768px) {
    .block-container { padding: 0 .8rem 2rem !important; }
    .hero-title  { font-size: 2.2rem; letter-spacing: -.6px; text-align: center; }
    .hero-sub    { font-size: .8rem; text-align: center; }
    .hero-chart-card { gap: 1.2rem; padding: .9rem 1.1rem; }
    .hcc-val     { font-size: 1.3rem; }
    .col-guide   { grid-template-columns: repeat(3, 1fr); }
    .cg-desc     { min-height: unset; }
    .insight-wrap { padding: 1rem 1.1rem; }
    .factor-row  { grid-template-columns: 100px 1fr 44px; gap: 8px; }
    .sg-grid     { grid-template-columns: repeat(2, 1fr); }
    .sg-desc     { min-height: unset; }
}
@media (max-width: 640px) {
    .picks-grid      { grid-template-columns: repeat(2, 1fr); }
    .hero-chart-wrap { display: none; }
}
@media (max-width: 480px) {
    .block-container { padding: 0 .45rem 2rem !important; }
    .hero-wrap   { padding: 2rem .5rem 1.2rem; }
    .hero-title  { font-size: 1.7rem; letter-spacing: -.4px; text-align: center; }
    .hero-pill   { font-size: .6rem; }
    .stats-grid  { grid-template-columns: repeat(4, 1fr); }
    .picks-grid  { grid-template-columns: repeat(2, 1fr); }
    .col-guide   { grid-template-columns: repeat(2, 1fr); }
    .pick-score  { font-size: 2.4rem; }
    .factor-row  { grid-template-columns: 82px 1fr 40px; gap: 7px; }
    .factor-name { font-size: .65rem; }
    .insight-wrap { padding: .85rem .9rem; }
    .insight-sym  { font-size: 1.4rem; }
    .insight-big  { font-size: 2rem; }
    .sec-head    { font-size: .66rem; }
    .s-val       { font-size: 1.7rem; }
    .sg-grid     { grid-template-columns: 1fr; }
}

/* ═══ TABLE ═══ */
.table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1rem;
    box-shadow: 0 4px 28px rgba(0,0,0,0.45);
}
.stocks-table {
    width: 100%;
    border-collapse: collapse;
    font-size: .8rem;
}
.stocks-table th {
    background: rgba(13,9,30,0.92);
    color: #64748b;
    font-size: .62rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .7px;
    padding: .75rem .65rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    white-space: nowrap;
    text-align: right;
    position: sticky;
    top: 0;
    z-index: 3;
}
.stocks-table th:nth-child(-n+3) { text-align: left; }
.stocks-table tbody tr               { --rbg: rgba(255,255,255,0.03); }
.stocks-table tbody tr:nth-child(even) { --rbg: rgba(255,255,255,0.055); }
@media (hover: hover) {
    .stocks-table tbody tr:hover { --rbg: rgba(139,92,246,0.09); }
}
.stocks-table tbody tr:hover .sc-rank,
.stocks-table tbody tr:hover .sc-sym,
.stocks-table tbody tr:hover .sc-co { background: rgba(139,92,246,0.09) !important; }
.stocks-table td {
    padding: .58rem .65rem;
    white-space: nowrap;
    text-align: right;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    background: var(--rbg);
    color: #cbd5e1;
}
.stocks-table td:nth-child(-n+3) { text-align: left; }
.sc-rank {
    position: sticky; left: 0; z-index: 2;
    min-width: 34px; width: 34px;
    text-align: center !important;
    color: #64748b; font-size: .72rem;
}
.sc-sym {
    position: sticky; left: 34px; z-index: 2;
    min-width: 62px; width: 62px;
    font-weight: 700; color: #f1f5f9 !important;
}
.sc-co {
    position: sticky; left: 96px; z-index: 2;
    min-width: 118px; width: 118px;
    max-width: 118px;
    color: #94a3b8 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
    font-size: .76rem;
    white-space: normal;
}
.sc-co-name   { display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 110px; }
.sc-co-sector { display: block; font-size: .6rem; color: #64748b; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 110px; }
.stocks-table thead .sc-rank,
.stocks-table thead .sc-sym,
.stocks-table thead .sc-co {
    z-index: 4;
    background: rgba(13,9,30,0.92) !important;
}

/* ═══ SCORE GUIDE (expander) ═══ */
.sg-intro { font-size: .75rem; color: #94a3b8; line-height: 1.65; margin-bottom: .9rem; }
.sg-grid  { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: .85rem; }
.sg-item  { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.09); border-radius: 10px; padding: .75rem .8rem; box-shadow: 0 1px 2px rgba(0,0,0,0.3); backdrop-filter: blur(8px); }
.sg-name  { font-size: .77rem; font-weight: 800; color: #f1f5f9; margin-bottom: .2rem; }
.sg-desc  { font-size: .63rem; color: #94a3b8; margin-bottom: .42rem; line-height: 1.45; min-height: 2.5rem; }
.sg-tiers { display: flex; flex-direction: column; gap: 3px; }
.sgt-g, .sgt-y, .sgt-r { font-size: .62rem; font-weight: 600; padding: .1rem .4rem; border-radius: 3px; display: inline-block; }
.sgt-g { background: rgba(16,185,129,0.15);  color: #34d399; }
.sgt-y { background: rgba(251,191,36,0.12);  color: #fbbf24; }
.sgt-r { background: rgba(248,113,113,0.12); color: #f87171; }
.sg-ratings { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; padding-top: .75rem; border-top: 1px solid rgba(255,255,255,0.07); font-size: .72rem; }
.sg-ratings b { color: #94a3b8; margin-right: 2px; }
.sgr-sb, .sgr-b, .sgr-h, .sgr-av { padding: .16rem .6rem; border-radius: 50px; font-size: .66rem; font-weight: 700; }
.sgr-sb, .sgr-b { color: #34d399; background: rgba(16,185,129,0.15);  border: 1px solid rgba(52,211,153,0.3); }
.sgr-w  { color: #38bdf8; background: rgba(56,189,248,0.12);  border: 1px solid rgba(56,189,248,0.28); }
.sgr-h  { color: #fbbf24; background: rgba(251,191,36,0.12);  border: 1px solid rgba(251,191,36,0.28); }
.sgr-av { color: #f87171; background: rgba(248,113,113,0.12); border: 1px solid rgba(248,113,113,0.28); }
.sgr-sa { color: #f43f5e; background: rgba(244,63,94,0.15);   border: 1px solid rgba(244,63,94,0.35); }

/* ═══ RATING LEGEND (inline, above the table) ═══ */
.rating-legend {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
    margin: .75rem 0 1rem;
}
.rl-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: .7rem .75rem .65rem;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
}
.rl-score   { font-size: .68rem; font-weight: 700; color: #94a3b8; letter-spacing: .2px; }
.rl-meaning { font-size: .63rem; color: #94a3b8; line-height: 1.4; }
@media (max-width: 900px)  { .rating-legend { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 480px)  { .rating-legend { grid-template-columns: repeat(2, 1fr); } }

/* ═══ MARKET STATUS BANNER ═══ */
.mkt-banner {
    display: flex;
    align-items: center;
    gap: 14px;
    background: rgba(251,191,36,0.07);
    border: 1px solid rgba(251,191,36,0.22);
    border-radius: 14px;
    padding: .95rem 1.4rem;
    margin: 0 0 1.4rem;
    backdrop-filter: blur(8px);
}
.mkt-banner-icon { font-size: 1.5rem; line-height: 1; flex-shrink: 0; }
.mkt-banner-body { flex: 1; }
.mkt-banner-title {
    font-size: .78rem; font-weight: 700; color: #fbbf24; margin-bottom: .2rem;
    letter-spacing: .1px;
}
.mkt-banner-sub { font-size: .72rem; color: #94a3b8; line-height: 1.5; }
.mkt-banner-sub b { color: #cbd5e1; }
.mkt-banner-date { text-align: right; flex-shrink: 0; }
.mkt-banner-date-lbl {
    font-size: .55rem; text-transform: uppercase; letter-spacing: 1px;
    color: #64748b; font-weight: 700; margin-bottom: .2rem;
}
.mkt-banner-date-val { font-size: .92rem; font-weight: 800; color: #fbbf24; white-space: nowrap; }

/* ═══ NIFTY 50 INDEX WIDGET ═══ */
.nifty-widget {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(12px);
}
.nifty-section   { flex: 1; min-width: 0; }
.nifty-idx-name  { font-size: .55rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin-bottom: .3rem; }
.nifty-price-val { font-size: 1.9rem; font-weight: 900; color: #f1f5f9; line-height: 1.05; font-variant-numeric: tabular-nums; letter-spacing: -.5px; }
.nifty-chg-pill  { display: inline-flex; align-items: center; gap: 4px; font-size: .8rem; font-weight: 700; padding: .18rem .65rem; border-radius: 50px; margin-top: .38rem; }
.nifty-up { background: rgba(16,185,129,0.15); color: #34d399; }
.nifty-dn { background: rgba(248,113,113,0.12); color: #f87171; }
.nifty-spark-section { flex: 0 0 auto; text-align: center; }
.nifty-spark-lbl { font-size: .55rem; color: #64748b; text-transform: uppercase; letter-spacing: .8px; margin-bottom: 5px; }
.nifty-gauge-section { flex: 0 0 130px; text-align: center; }
.nifty-sentiment { font-size: .95rem; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; margin-top: .25rem; }
.nifty-bull { color: #34d399; }
.nifty-bear { color: #f87171; }
.nifty-sent-sub { font-size: .58rem; color: #64748b; letter-spacing: .3px; margin-top: 3px; }
@media (max-width: 640px) {
    .nifty-widget { flex-direction: column; gap: .85rem; }
    .nifty-gauge-section { display: flex; align-items: center; gap: .75rem; flex: none; width: 100%; }
    .nifty-sentiment { margin-top: 0; }
}

/* ═══ PRICE IN TOP5 PICKS & INSIGHTS ═══ */
.pick-price    { font-size: 1.05rem; font-weight: 800; color: #f1f5f9; margin: .2rem 0 .05rem; letter-spacing: -.2px; }
.insight-price { font-size: .88rem; font-weight: 700; color: #94a3b8; margin-top: .3rem; }

/* ═══ MARKET INDICES PANEL ═══ */
.mkt-panel {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 1.2rem;
}
.mkt-primary-row {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 1rem 1.4rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    background: rgba(255,255,255,0.025);
    flex-wrap: wrap;
}
.mkt-primary-tile {
    flex: 0 0 auto;
    padding-right: 1.4rem;
    margin-right: 1.4rem;
    border-right: 1px solid rgba(255,255,255,0.08);
}
.mkt-pt-name  { font-size:.52rem; font-weight:800; text-transform:uppercase; letter-spacing:1.4px; color:#64748b; margin-bottom:.22rem; }
.mkt-pt-price { font-size:1.55rem; font-weight:900; color:#f1f5f9; line-height:1.1; font-variant-numeric:tabular-nums; letter-spacing:-.5px; }
.mkt-pt-chg   { font-size:.78rem; font-weight:700; margin-top:.28rem; }
.mkt-mood-col { text-align:center; flex:0 0 auto; padding:0 1.4rem; border-right:1px solid rgba(255,255,255,0.08); margin-right:1.4rem; }
.mkt-bull { color:#34d399; }
.mkt-bear { color:#f87171; }
.mkt-up   { color:#34d399; }
.mkt-dn   { color:#f87171; }
.mkt-sentiment  { font-size:.9rem; font-weight:900; letter-spacing:2px; text-transform:uppercase; margin-top:.15rem; }
.mkt-mood-sub   { font-size:.55rem; color:#64748b; margin-top:2px; }
.mkt-days-col   { flex:1; min-width:0; }
.mkt-days-lbl   { font-size:.52rem; text-transform:uppercase; letter-spacing:.8px; color:#64748b; margin-bottom:.45rem; }
.mkt-days-row   { display:flex; gap:.55rem; }
.mkt-day-item   { display:flex; flex-direction:column; align-items:center; gap:4px; }
.mkt-day-circle { width:22px; height:22px; border-radius:6px; }
.mkt-day-up { background:rgba(16,185,129,0.2); border:1px solid rgba(52,211,153,0.35); }
.mkt-day-dn { background:rgba(248,113,113,0.15); border:1px solid rgba(248,113,113,0.3); }
.mkt-day-lbl { font-size:.47rem; text-transform:uppercase; letter-spacing:.4px; color:#64748b; }
.mkt-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: rgba(255,255,255,0.06);
}
.mkt-cell {
    background: #0A0812;
    padding: .7rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 3px;
    cursor: default;
    transition: background .18s;
}
.mkt-cell:hover { background: rgba(139,92,246,0.07); }
.mkt-cell-hdr   { display:flex; justify-content:space-between; align-items:center; margin-bottom:2px; }
.mkt-cell-name  { font-size:.57rem; font-weight:700; text-transform:uppercase; letter-spacing:.8px; color:#64748b; }
.mkt-cell-chg   { font-size:.68rem; font-weight:700; }
.mkt-cell-price { font-size:.92rem; font-weight:800; color:#f1f5f9; font-variant-numeric:tabular-nums; margin-top:3px; }
.mkt-cell-empty { color:#475569; font-size:.75rem; }
@media (max-width:700px) {
    .mkt-primary-row { gap:.8rem; }
    .mkt-primary-tile { border-right:none; padding-right:0; margin-right:0; }
    .mkt-mood-col { border-right:none; padding:0; }
    .mkt-days-col { width:100%; }
    .mkt-grid { grid-template-columns:repeat(2,1fr); }
}
@media (max-width:400px) { .mkt-grid { grid-template-columns:1fr; } }

/* ═══ PRESET STRATEGY PILLS ═══ */
.preset-row { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:.5rem; }

/* Uniform height for ALL sidebar buttons (presets + refresh) */
[data-testid="stSidebar"] .stButton button {
    height: 2.35rem !important;
    min-height: 2.35rem !important;
    padding: 0 .6rem !important;
    font-size: .76rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ═══ RISING MARKET CHART BACKGROUND ═══ */
.bg-rising-chart {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}
.bg-rising-chart svg { width: 100%; height: 100%; }

/* Keep sidebar and main content above the background chart */
[data-testid="stSidebar"] { position: relative; z-index: 1; }
[data-testid="stMain"]    { position: relative; z-index: 1; }

/* Pulsing glow ring at the chart tip */
@keyframes bcg-pulse {
    0%, 100% { transform: scale(1);   opacity: .45; }
    50%       { transform: scale(1.6); opacity: .08; }
}
.bcg-glow-ring {
    transform-origin: 1440px 232px;
    animation: bcg-pulse 3s ease-in-out infinite;
}

/* ═══ FILTER BAR ═══ */
.filter-section-lbl { font-size:.58rem; font-weight:700; text-transform:uppercase; letter-spacing:.9px; color:#64748b; margin-bottom:.3rem; }

/* ═══ PRESET ACTIVE PILL ═══ */
.preset-active-pill {
    margin-top: .45rem;
    padding: .28rem .65rem;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.35);
    border-radius: 999px;
    color: #10b981;
    font-size: .7rem;
    font-weight: 600;
    text-align: center;
    letter-spacing: .4px;
}

/* ═══ HEATMAP & COMPARISON SECTIONS ═══ */
.chart-section-wrap {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.2rem 1.4rem 1rem;
    margin-bottom: 1.2rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Rising market chart background (fixed, behind all content)
# ─────────────────────────────────────────────────────────────────────────────
# The SVG path traces a bull-market rally from bottom-left to top-right with
# natural corrections. Gradient fades from purple (left) to emerald (right).
# preserveAspectRatio="xMidYMid slice" ensures it always covers the viewport.
st.markdown("""
<div class="bg-rising-chart">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900"
     preserveAspectRatio="xMidYMid slice">
  <defs>
    <!-- Line: transparent purple → visible emerald green -->
    <linearGradient id="bcg-line" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#6d28d9" stop-opacity="0"/>
      <stop offset="20%"  stop-color="#8b5cf6" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#10b981" stop-opacity="0.55"/>
    </linearGradient>
    <!-- Area fill below the line -->
    <linearGradient id="bcg-fill" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%"   stop-color="#10b981" stop-opacity="0.07"/>
      <stop offset="100%" stop-color="#10b981" stop-opacity="0"/>
    </linearGradient>
    <!-- Radial glow at the "latest price" dot -->
    <radialGradient id="bcg-glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="#10b981" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#10b981" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <!-- Filled area under the line -->
  <path d="M 0,830
    C  80,825  140,810  200,790
    C 260,770  280,785  340,758
    C 400,731  415,720  475,695
    C 535,670  548,660  600,635
    C 652,610  670,625  730,595
    C 790,565  800,575  850,545
    C 900,515  895,540  955,495
    C1015,450 1035,465 1090,425
    C1145,385 1155,400 1215,358
    C1275,316 1300,330 1360,288
    C1400,258 1425,242 1440,232
    L 1440,900 L 0,900 Z"
    fill="url(#bcg-fill)"/>

  <!-- Rising price line -->
  <path d="M 0,830
    C  80,825  140,810  200,790
    C 260,770  280,785  340,758
    C 400,731  415,720  475,695
    C 535,670  548,660  600,635
    C 652,610  670,625  730,595
    C 790,565  800,575  850,545
    C 900,515  895,540  955,495
    C1015,450 1035,465 1090,425
    C1145,385 1155,400 1215,358
    C1275,316 1300,330 1360,288
    C1400,258 1425,242 1440,232"
    fill="none"
    stroke="url(#bcg-line)"
    stroke-width="2.5"
    stroke-linecap="round"
    stroke-linejoin="round"/>

  <!-- Pulsing glow ring at the latest price tip -->
  <circle class="bcg-glow-ring" cx="1440" cy="232" r="30"
          fill="url(#bcg-glow)"/>
  <!-- Solid dot -->
  <circle cx="1440" cy="232" r="7"  fill="#10b981" opacity="0.45"/>
  <circle cx="1440" cy="232" r="3.5" fill="#10b981" opacity="0.85"/>
</svg>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
_GREEN  = "background:rgba(16,185,129,0.15);color:#34d399"
_YELLOW = "background:rgba(251,191,36,0.12);color:#fbbf24"
_RED    = "background:rgba(248,113,113,0.12);color:#f87171"

_BADGE_CLASS = {
    "Strong Buy":   "b-sb",
    "Buy":          "b-b",
    "Watch":        "b-w",
    "Hold":         "b-h",
    "Avoid":        "b-av",
    "Strong Avoid": "b-sa",
}

# Market indices panel — ordered for the 3×3 grid display
_MARKET_TICKERS = [
    ("^NSEI",      "NIFTY 50",      False),   # (symbol, label, is_forex)
    ("^CNX100",    "NIFTY 100",     False),
    ("^NSEBANK",   "NIFTY Bank",    False),
    ("USDINR=X",   "USD / INR",     True),
    ("^NSEMDCP50", "NIFTY Midcap",  False),
    ("^CNXIT",     "NIFTY IT",      False),
    ("GC=F",       "Gold (USD)",    True),
    ("^CNXSC",     "NIFTY Smallcap",False),
    ("^CNXPHARMA", "NIFTY Pharma",  False),
]

# Preset screening strategies — sets filter defaults when clicked
# "sort_lbl" must match a key in _SORT_MAP exactly (the selectbox display label)
_PRESETS = {
    "🔍 Deep Value": {"min_score": 5.0, "weights": [3, 2, 1, 1, 1, 2], "sort_lbl": "P/E Ratio",   "asc": True},
    "📈 Growth":     {"min_score": 5.0, "weights": [1, 1, 3, 1, 3, 1], "sort_lbl": "Rev Growth",  "asc": False},
    "🛡 Low Risk":   {"min_score": 4.0, "weights": [1, 1, 1, 3, 1, 3], "sort_lbl": "D/E Ratio",   "asc": True},
    "💎 Quality":    {"min_score": 6.0, "weights": [2, 2, 3, 2, 2, 1], "sort_lbl": "Value Score",  "asc": False},
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

    # ── Preset Strategies ────────────────────────────────────────────────────
    st.markdown('<div class="filter-section-lbl">⚡ Preset Strategies</div>', unsafe_allow_html=True)

    def _apply_preset(pname: str) -> None:
        cfg = _PRESETS[pname]
        st.session_state["min_score"]      = cfg["min_score"]
        st.session_state["tbl_sort_lbl"]   = cfg["sort_lbl"]   # direct widget key
        st.session_state["sort_asc"]       = cfg["asc"]
        st.session_state["_active_preset"] = pname
        for i, k in enumerate(["w_pe", "w_pb", "w_roe", "w_de", "w_gr", "w_w52"]):
            st.session_state[k] = cfg["weights"][i]

    def _clear_preset() -> None:
        st.session_state.pop("_active_preset", None)
        st.session_state["tbl_sort_lbl"] = "Value Score"
        st.session_state["sort_asc"]     = False
        st.session_state["min_score"]    = 0.0
        for _k in ["w_pe", "w_pb", "w_roe", "w_de", "w_gr", "w_w52"]:
            st.session_state[_k] = 1

    _pc = st.columns(2)
    for _pi, _pname in enumerate(_PRESETS):
        with _pc[_pi % 2]:
            st.button(
                _pname, key=f"preset_{_pi}",
                use_container_width=True,
                on_click=_apply_preset, args=(_pname,),
            )

    # Active preset indicator + clear button
    _active_preset = st.session_state.get("_active_preset")
    if _active_preset:
        st.markdown(
            f'<div class="preset-active-pill">▶ {_active_preset} active</div>',
            unsafe_allow_html=True,
        )
        st.button("✕ Clear Strategy", on_click=_clear_preset,
                  use_container_width=True, type="secondary", key="btn_clear_preset")

    # ── Custom Factor Weights ─────────────────────────────────────────────────
    with st.expander("⚖️ Custom Factor Weights", expanded=False):
        st.caption("Adjust the weight of each factor. Equal weights = 1.")

        def _reset_weights() -> None:
            for _k in ["w_pe", "w_pb", "w_roe", "w_de", "w_gr", "w_w52"]:
                st.session_state[_k] = 1

        st.button("↺ Reset to Equal", on_click=_reset_weights, use_container_width=True)
        st.slider("P/E Ratio",     1, 5, 1, key="w_pe")
        st.slider("P/B Ratio",     1, 5, 1, key="w_pb")
        st.slider("ROE (%)",       1, 5, 1, key="w_roe")
        st.slider("Debt/Equity",   1, 5, 1, key="w_de")
        st.slider("Rev Growth",    1, 5, 1, key="w_gr")
        st.slider("52W Position",  1, 5, 1, key="w_w52")

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
# NIFTY 50 widget helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sparkline_svg(prices: list, width: int = 160, height: int = 42) -> str:
    """Minimal SVG sparkline for a list of prices."""
    if len(prices) < 2:
        return ""
    mn, mx = min(prices), max(prices)
    rng = mx - mn or 1.0
    pts = []
    for i, p in enumerate(prices):
        x = 4.0 + (i / (len(prices) - 1)) * (width - 8)
        y = (height - 6) - ((p - mn) / rng) * (height - 12) + 2.0
        pts.append((x, y))
    color = "#34d399" if prices[-1] >= prices[0] else "#f87171"
    poly  = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    fill  = f"{pts[0][0]:.1f},{height} {poly} {pts[-1][0]:.1f},{height}"
    lx, ly = pts[-1]
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<defs><linearGradient id="nsg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.3"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{fill}" fill="url(#nsg)"/>'
        f'<polyline points="{poly}" fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3" fill="{color}"/>'
        f'</svg>'
    )


def _gauge_svg(change_pct: float) -> str:
    """
    Semi-circular sentiment gauge.
    Red (left) = bearish · Yellow (centre) = neutral · Green (right) = bullish.
    Needle position is driven by today's % change, clamped to ±2%.
    """
    W, H = 120, 68
    cx, cy = 60, 64
    r_out, r_in = 54, 38
    clamped = max(-2.0, min(2.0, change_pct))
    # needle: -2% → 180° (left/bearish), 0% → 90° (top/neutral), +2% → 0° (right/bullish)
    needle_deg = 90.0 - (clamped / 2.0) * 90.0
    rad = math.radians(needle_deg)
    nl  = r_in - 3
    nx  = cx + nl * math.cos(rad)
    ny  = cy - nl * math.sin(rad)

    def _seg(a1_deg: float, a2_deg: float, color: str) -> str:
        a1 = math.radians(a1_deg)
        a2 = math.radians(a2_deg)
        ox1, oy1 = cx + r_out * math.cos(a1), cy - r_out * math.sin(a1)
        ox2, oy2 = cx + r_out * math.cos(a2), cy - r_out * math.sin(a2)
        ix1, iy1 = cx + r_in  * math.cos(a2), cy - r_in  * math.sin(a2)
        ix2, iy2 = cx + r_in  * math.cos(a1), cy - r_in  * math.sin(a1)
        return (
            f'<path d="M {ox1:.1f},{oy1:.1f} A {r_out},{r_out} 0 0,0 {ox2:.1f},{oy2:.1f} '
            f'L {ix1:.1f},{iy1:.1f} A {r_in},{r_in} 0 0,1 {ix2:.1f},{iy2:.1f} Z" '
            f'fill="{color}"/>'
        )

    nc   = "#34d399" if change_pct >= 0 else "#f87171"
    segs = (
        _seg(180, 120, "rgba(248,113,113,0.55)") +
        _seg(120, 60,  "rgba(251,191,36,0.45)")  +
        _seg(60,  0,   "rgba(16,185,129,0.55)")
    )
    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'{segs}'
        f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" '
        f'stroke="{nc}" stroke-width="2.5" stroke-linecap="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="5" fill="{nc}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="2.5" fill="#0A0812"/>'
        f'</svg>'
    )


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_nifty() -> dict | None:
    """Fetch NIFTY 50 current price, day change, and recent price history."""
    try:
        ticker = yf.Ticker("^NSEI")
        info   = ticker.info
        current = (
            info.get("regularMarketPrice")
            or info.get("currentPrice")
            or info.get("previousClose")
            or info.get("regularMarketPreviousClose")
        )
        prev = (
            info.get("regularMarketPreviousClose")
            or info.get("previousClose")
        )
        if not current or not prev:
            return None
        current, prev = float(current), float(prev)
        change     = current - prev
        change_pct = (change / prev) * 100
        hist   = ticker.history(period="12d")
        prices = hist["Close"].dropna().tolist()[-7:] if not hist.empty else []
        return {
            "price":      current,
            "change":     change,
            "change_pct": change_pct,
            "prices":     prices,
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_market_panel() -> dict:
    """
    Fetch current price, % change, 7-day sparkline, and last-5-day up/down
    for every index in _MARKET_TICKERS.  Cached 1 h.
    """
    results = {}
    for sym, name, is_forex in _MARKET_TICKERS:
        try:
            hist = yf.Ticker(sym).history(period="14d")
            if hist.empty or len(hist) < 2:
                continue
            closes = hist["Close"].dropna()
            prices = [float(p) for p in closes.tolist()]
            current, prev = prices[-1], prices[-2]
            change     = current - prev
            change_pct = (change / prev) * 100 if prev else 0.0

            # Last-5-day up/down circles
            days = []
            start = max(1, len(closes) - 5)
            for i in range(start, len(closes)):
                days.append({
                    "label": closes.index[i].strftime("%a").upper()[:3],
                    "up":    closes.iloc[i] >= closes.iloc[i - 1],
                })

            results[sym] = {
                "name":       name,
                "is_forex":   is_forex,
                "price":      current,
                "change":     change,
                "change_pct": change_pct,
                "prices":     prices[-7:],
                "days":       days,
            }
        except Exception:
            pass
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Hero banner
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
  <div class="hero-pill">
    <span class="hero-dot"></span>
    Live NSE Market Data &nbsp;·&nbsp; India
  </div>
  <h1 class="hero-title">
    Smarter Stock Picks<br>
    <span class="hero-accent">Backed by Fundamentals</span>
  </h1>
  <p class="hero-sub">
    Screen the entire NSE universe across 6 key metrics — P/E, P/B, ROE,
    Debt, Revenue Growth &amp; 52-Week position — scored, ranked and
    explained in plain English. No guesswork, just data.
  </p>
  <div class="hero-chart-wrap">
    <div class="hero-chart-card">
      <div class="hcc-stat">
        <div class="hcc-val">50<span style="color:#10b981;font-size:1.1rem;">+</span></div>
        <div class="hcc-lbl">Stocks Screened</div>
      </div>
      <div class="hcc-div"></div>
      <div class="hcc-stat">
        <div class="hcc-val" style="color:#10b981;">6</div>
        <div class="hcc-lbl">Value Factors</div>
      </div>
      <div class="hcc-div"></div>
      <div class="hcc-stat">
        <div class="hcc-val" style="color:#f59e0b;">1h</div>
        <div class="hcc-lbl">Live Cache</div>
      </div>
      <div class="hcc-div"></div>
      <div class="hcc-stat">
        <svg viewBox="0 0 130 52" width="130" height="52" style="display:block;">
          <defs>
            <linearGradient id="hg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#10b981" stop-opacity="0.25"/>
              <stop offset="100%" stop-color="#10b981" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <polygon points="0,48 22,40 44,33 66,22 88,15 110,8 130,2 130,52 0,52" fill="url(#hg)"/>
          <polyline points="0,48 22,40 44,33 66,22 88,15 110,8 130,2"
                    fill="none" stroke="#10b981" stroke-width="2"
                    stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="16" y1="34" x2="16" y2="46" stroke="#10b981" stroke-width="1.5"/>
          <rect x="12" y="37" width="8" height="6" fill="#10b981" rx="1"/>
          <line x1="38" y1="26" x2="38" y2="40" stroke="#ef4444" stroke-width="1.5"/>
          <rect x="34" y="29" width="8" height="8" fill="#ef4444" rx="1"/>
          <line x1="60" y1="16" x2="60" y2="30" stroke="#10b981" stroke-width="1.5"/>
          <rect x="56" y="19" width="8" height="7" fill="#10b981" rx="1"/>
          <line x1="82" y1="9"  x2="82" y2="22" stroke="#10b981" stroke-width="1.5"/>
          <rect x="78" y="12" width="8" height="7" fill="#10b981" rx="1"/>
          <line x1="104" y1="2" x2="104" y2="16" stroke="#10b981" stroke-width="1.5"/>
          <rect x="100" y="5" width="8" height="7" fill="#10b981" rx="1"/>
        </svg>
        <div class="hcc-lbl">NSE Trend</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Market status banner (shown only when NSE is closed)
# ─────────────────────────────────────────────────────────────────────────────
_mkt = get_market_status()
if not _mkt["is_open"]:
    _last = _mkt["last_close"].strftime("%a, %d %b %Y")
    _reason = _mkt["reason"]
    st.markdown(
        f'<div class="mkt-banner">'
        f'<div class="mkt-banner-icon">🔔</div>'
        f'<div class="mkt-banner-body">'
        f'<div class="mkt-banner-title">NSE Market Closed — {_reason}</div>'
        f'<div class="mkt-banner-sub">'
        f'Showing last available closing prices from <b>{_last}</b>. '
        f'Fundamental data (P/E, ROE, etc.) remains current.'
        f'</div>'
        f'</div>'
        f'<div class="mkt-banner-date">'
        f'<div class="mkt-banner-date-lbl">Prices as of</div>'
        f'<div class="mkt-banner-date-val">{_mkt["last_close"].strftime("%d %b %Y")}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Market Indices Panel (always visible — fetched independently)
# ─────────────────────────────────────────────────────────────────────────────
_panel = _fetch_market_panel()
if _panel:
    # ── Primary row: NIFTY 50 + NIFTY Bank tiles + gauge + day circles ──────
    def _pt(sym: str) -> str:
        d    = _panel.get(sym, {})
        name = next((n for s, n, _ in _MARKET_TICKERS if s == sym), sym)
        if not d:
            # Show placeholder so the tile is never invisibly missing
            return (
                f'<div class="mkt-primary-tile">'
                f'<div class="mkt-pt-name">{name}</div>'
                f'<div class="mkt-pt-price" style="color:#475569">—</div>'
                f'<div class="mkt-pt-chg" style="color:#475569;font-size:.7rem">Unavailable</div>'
                f'</div>'
            )
        _up  = d["change_pct"] >= 0
        _cls = "mkt-up" if _up else "mkt-dn"
        _dir = "▲" if _up else "▼"
        return (
            f'<div class="mkt-primary-tile">'
            f'<div class="mkt-pt-name">{d["name"]}</div>'
            f'<div class="mkt-pt-price">{d["price"]:,.2f}</div>'
            f'<div class="mkt-pt-chg {_cls}">'
            f'{_dir} {abs(d["change_pct"]):.2f}%'
            f'&ensp;<span style="opacity:.6;font-weight:500">'
            f'({_dir} {abs(d["change"]):,.2f})</span></div>'
            f'</div>'
        )

    _n50     = _panel.get("^NSEI", {})
    _n50_chg = _n50.get("change_pct", 0)
    _sent    = "Bullish" if _n50_chg >= 0 else "Bearish"
    _scls    = "mkt-bull" if _n50_chg >= 0 else "mkt-bear"
    _gauge   = _gauge_svg(_n50_chg)

    # Day circles for NIFTY 50
    _dcircles = ""
    for _d in _n50.get("days", []):
        _cc = "mkt-day-up" if _d["up"] else "mkt-day-dn"
        _dcircles += (
            f'<div class="mkt-day-item">'
            f'<div class="mkt-day-circle {_cc}"></div>'
            f'<div class="mkt-day-lbl">{_d["label"]}</div>'
            f'</div>'
        )
    _days_html = (
        f'<div class="mkt-days-col">'
        f'<div class="mkt-days-lbl">5-Day Trend</div>'
        f'<div class="mkt-days-row">{_dcircles}</div>'
        f'</div>'
    ) if _dcircles else ""

    _primary = (
        f'<div class="mkt-primary-row">'
        + _pt("^NSEI") + _pt("^NSEBANK")
        + f'<div class="mkt-mood-col">{_gauge}'
        f'<div class="mkt-sentiment {_scls}">{_sent}</div>'
        f'<div class="mkt-mood-sub">Today\'s mood</div></div>'
        + _days_html
        + f'</div>'
    )

    # ── 3×3 grid of all indices ──────────────────────────────────────────────
    _cells = ""
    for _sym, _name, _is_fx in _MARKET_TICKERS:
        _d = _panel.get(_sym, {})
        if not _d:
            _cells += f'<div class="mkt-cell mkt-cell-empty">{_name}<br><small>—</small></div>'
            continue
        _up  = _d["change_pct"] >= 0
        _cls = "mkt-up" if _up else "mkt-dn"
        _dir = "▲" if _up else "▼"
        _chg = f"{_dir} {abs(_d['change_pct']):.2f}%"
        if _sym == "USDINR=X":
            _pf = f"₹{_d['price']:.4f}"
        elif _sym == "GC=F":
            _pf = f"${_d['price']:,.2f}"
        else:
            _pf = f"{_d['price']:,.2f}"
        _spark = _sparkline_svg(_d["prices"], width=110, height=28) if len(_d.get("prices", [])) >= 2 else ""
        _cells += (
            f'<div class="mkt-cell">'
            f'<div class="mkt-cell-hdr">'
            f'<span class="mkt-cell-name">{_name}</span>'
            f'<span class="mkt-cell-chg {_cls}">{_chg}</span>'
            f'</div>'
            f'{_spark}'
            f'<div class="mkt-cell-price">{_pf}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="mkt-panel">{_primary}'
        f'<div class="mkt-grid">{_cells}</div></div>',
        unsafe_allow_html=True,
    )

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


def _rating_from_score(s: float) -> str:
    if s >= 8.0: return "Strong Buy"
    if s >= 6.0: return "Buy"
    if s >= 5.0: return "Watch"
    if s >= 4.0: return "Hold"
    if s >= 2.0: return "Avoid"
    return "Strong Avoid"


def _apply_weights(df: pd.DataFrame, weights: list) -> pd.DataFrame:
    """Recompute value_score and rating using custom per-factor weights."""
    out   = df.copy()
    w     = [max(1, int(x)) for x in weights]
    cols  = ["pe_score", "pb_score", "roe_score", "de_score", "growth_score", "week52_score"]
    total = sum(w)
    out["value_score"] = sum(out[c] * wt for c, wt in zip(cols, w)) / total
    out["value_score"] = out["value_score"].round(2)
    out["rating"]      = out["value_score"].apply(_rating_from_score)
    return out.sort_values("value_score", ascending=False).reset_index(drop=True)


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
    n_w   = int((scored_df["rating"] == "Watch").sum())
    n_h   = int((scored_df["rating"] == "Hold").sum())
    n_av  = int((scored_df["rating"] == "Avoid").sum())
    n_sav = int((scored_df["rating"] == "Strong Avoid").sum())
    n_tot = len(scored_df)

    items = [
        ("c-total",  n_tot,  "Analysed"),
        ("c-sbuy",   n_sb,   "Strong Buy"),
        ("c-buy",    n_b,    "Buy"),
        ("c-watch",  n_w,    "Watch"),
        ("c-hold",   n_h,    "Hold"),
        ("c-avoid",  n_av,   "Avoid"),
        ("c-savoid", n_sav,  "Strong Avoid"),
        ("c-gap",    skipped,"Data N/A"),
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
        price   = format_price(row.get("Current Price"))

        pe_s  = _fmt(row.get("PE Ratio"),           "{:.1f}")
        roe_s = _fmt(row.get("ROE (%)"),             "{:.1f}%")
        de_s  = _fmt(row.get("Debt/Equity"),         "{:.2f}")
        gr_s  = _fmt(row.get("Revenue Growth (%)"),  "{:.1f}%")

        cards += (
            f'<div class="pick-card">'
            f'<div class="pick-rank">#{i + 1} &nbsp;·&nbsp; Top Pick</div>'
            f'<div class="pick-sym">{symbol}</div>'
            f'<div class="pick-co">{company or "&nbsp;"}</div>'
            f'<div class="pick-price">{price}</div>'
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
        if s >= 7: return "background:rgba(16,185,129,0.15);color:#34d399;font-weight:600"
        if s >= 4: return "background:rgba(251,191,36,0.12);color:#fbbf24;font-weight:600"
        return "background:rgba(248,113,113,0.12);color:#f87171;font-weight:600"

    def _f(val, fmt_str: str) -> str:
        return fmt_str.format(val) if pd.notna(val) else "—"

    _r_style = {
        "Strong Buy":   "color:#34d399;font-weight:800",
        "Buy":          "color:#4ade80;font-weight:800",
        "Watch":        "color:#38bdf8;font-weight:700",
        "Hold":         "color:#fbbf24;font-weight:700",
        "Avoid":        "color:#f87171;font-weight:700",
        "Strong Avoid": "color:#f43f5e;font-weight:800",
    }
    _r_emoji = {
        "Strong Buy":   "🟢",
        "Buy":          "🟢",
        "Watch":        "🔵",
        "Hold":         "🟡",
        "Avoid":        "🔴",
        "Strong Avoid": "🔴",
    }

    rows_html = ""
    for i, (_, row) in enumerate(df.iterrows()):
        symbol  = str(row["Symbol"]).replace(".NS", "")
        company = str(row.get("Company") or "")[:22]
        sector  = str(row.get("Sector") or "")[:20]
        rating  = str(row.get("rating", "Hold"))
        w52pos  = _52w_pct(row)
        price   = format_price(row.get("Current Price"))

        pe  = _f(row.get("PE Ratio"),           "{:.1f}")
        pb  = _f(row.get("PB Ratio"),            "{:.2f}")
        roe = _f(row.get("ROE (%)"),             "{:.1f}%")
        div = _f(row.get("Dividend Yield (%)"),  "{:.2f}%")
        de  = _f(row.get("Debt/Equity"),         "{:.2f}")
        gr  = _f(row.get("Revenue Growth (%)"),  "{:.1f}%")
        w52 = _f(w52pos,                         "{:.0f}%")
        vs  = f"{row.get('value_score', 0):.2f}"

        _sector_html = f'<span class="sc-co-sector">{sector}</span>' if sector else ""
        rows_html += (
            f'<tr>'
            f'<td class="sc-rank">{i + 1}</td>'
            f'<td class="sc-sym">{symbol}</td>'
            f'<td class="sc-co" title="{company}">'
            f'<span class="sc-co-name">{company}</span>{_sector_html}</td>'
            f'<td style="{_cell(row.get("week52_score", 5))};text-align:right">{price}</td>'
            f'<td style="{_cell(row.get("pe_score", 5))}">{pe}</td>'
            f'<td style="{_cell(row.get("pb_score", 5))}">{pb}</td>'
            f'<td style="{_cell(row.get("roe_score", 5))}">{roe}</td>'
            f'<td style="text-align:right;color:#94a3b8">{div}</td>'
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
        '<th class="sc-rank" title="Rank by Value Score">#</th>'
        '<th class="sc-sym" title="NSE stock ticker">Symbol</th>'
        '<th class="sc-co" title="Company name and sector">Company</th>'
        '<th title="Current market price in INR">Price ₹</th>'
        '<th title="Price/Earnings — how much you pay per ₹1 of profit. Lower = cheaper. Scored 1–10.">P/E</th>'
        '<th title="Price/Book — how much you pay per ₹1 of assets. Below 1 = trading below book value. Scored 1–10.">P/B</th>'
        '<th title="Return on Equity % — profit generated per ₹1 of shareholder equity. Higher = more efficient. Scored 1–10.">ROE %</th>'
        '<th title="Dividend Yield % — annual dividend as a % of the share price. Informational only.">Div %</th>'
        '<th title="Debt/Equity ratio — lower means less financial leverage and risk. Scored 1–10.">D/E</th>'
        '<th title="Revenue Growth % YoY — positive means the business is expanding. Scored 1–10.">Rev Gr%</th>'
        '<th title="52-Week Position % — 0% = at the year\'s low (best entry), 100% = at the year\'s high. Scored 1–10.">52W Pos</th>'
        '<th title="Value Score (1–10) — equal-weighted average of all 6 factors. Higher = better value.">Score</th>'
        '<th title="Rating based on the Value Score">Rating</th>'
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
    _price  = format_price(row.get("Current Price"))

    bar_data = [
        ("P/E Ratio",    row.get("pe_score", 5),     row.get("PE Ratio"),           "pe"),
        ("P/B Ratio",    row.get("pb_score", 5),     row.get("PB Ratio"),            "pb"),
        ("ROE (%)",      row.get("roe_score", 5),    row.get("ROE (%)"),             "roe"),
        ("Debt/Equity",  row.get("de_score", 5),     row.get("Debt/Equity"),         "de"),
        ("Rev Growth",   row.get("growth_score", 5), row.get("Revenue Growth (%)"),  "gr"),
        ("52-Week Pos.", row.get("week52_score", 5), w52_pos,                        "w52"),
    ]

    def _bar_col(s):
        if s >= 7: return "#34d399"
        if s >= 4: return "#fbbf24"
        return "#f87171"

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
        f'<div><div class="insight-sym">{symbol}</div>'
        f'<div class="insight-co">{company or "&nbsp;"}</div>'
        f'<div class="insight-price">{_price}</div></div>'
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
        st.error(
            "**Yahoo Finance returned no price data for any stock in this index.**\n\n"
            "This is usually a temporary rate-limit from Yahoo Finance — it does not mean "
            "the symbols are wrong. Please:\n"
            "1. Wait 30–60 seconds, then click **⚡ Analyse** again.\n"
            "2. If the problem persists, click **🔄 Refresh Data** in the sidebar first "
            "to clear the cache, then retry."
        )
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

# Apply custom factor weights when any weight differs from the default of 1
if scored_df is not None:
    _cw = [
        st.session_state.get("w_pe",  1),
        st.session_state.get("w_pb",  1),
        st.session_state.get("w_roe", 1),
        st.session_state.get("w_de",  1),
        st.session_state.get("w_gr",  1),
        st.session_state.get("w_w52", 1),
    ]
    if _cw != [1, 1, 1, 1, 1, 1]:
        scored_df = _apply_weights(scored_df, _cw)

if scored_df is None:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem;">
      <div style="font-size:3rem; margin-bottom:1rem;">📊</div>
      <div style="font-size:1.1rem; font-weight:700; color:#a78bfa; margin-bottom:.5rem;">
        No data loaded yet
      </div>
      <div style="font-size:.82rem; color:#94a3b8;">
        Select an index above and click <b style="background:linear-gradient(90deg,#8b5cf6,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">⚡ Analyse</b> to load live fundamentals.
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
  <span class="sgr-w">🔵 Watch ≥ 5.0</span>
  <span class="sgr-h">🟡 Hold ≥ 4.0</span>
  <span class="sgr-av">🔴 Avoid ≥ 2.0</span>
  <span class="sgr-sa">🔴 Strong Avoid &lt; 2.0</span>
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
      <span class="cg-t cg-tg">🟢 ≥ 8 Strong Buy · ≥ 6 Buy</span>
      <span class="cg-t cg-ty">🔵 ≥ 5 Watch · 🟡 ≥ 4 Hold</span>
      <span class="cg-t cg-tr">🔴 ≥ 2 Avoid · &lt; 2 Strong Avoid</span>
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

st.markdown("""
<div class="rating-legend">
  <div class="rl-card">
    <span class="pick-badge b-sb" style="margin:0;">🟢 Strong Buy</span>
    <div class="rl-score">Score ≥ 8.0</div>
    <div class="rl-meaning">Exceptional value across all six factors</div>
  </div>
  <div class="rl-card">
    <span class="pick-badge b-b" style="margin:0;">🟢 Buy</span>
    <div class="rl-score">Score ≥ 6.0</div>
    <div class="rl-meaning">Strong fundamentals — attractive entry</div>
  </div>
  <div class="rl-card">
    <span class="pick-badge b-w" style="margin:0;">🔵 Watch</span>
    <div class="rl-score">Score ≥ 5.0</div>
    <div class="rl-meaning">Just below Buy — monitor for improvement</div>
  </div>
  <div class="rl-card">
    <span class="pick-badge b-h" style="margin:0;">🟡 Hold</span>
    <div class="rl-score">Score ≥ 4.0</div>
    <div class="rl-meaning">Mixed signals — no strong buy or sell case</div>
  </div>
  <div class="rl-card">
    <span class="pick-badge b-av" style="margin:0;">🔴 Avoid</span>
    <div class="rl-score">Score ≥ 2.0</div>
    <div class="rl-meaning">Weak across most factors — consider alternatives</div>
  </div>
  <div class="rl-card">
    <span class="pick-badge b-sa" style="margin:0;">🔴 Strong Avoid</span>
    <div class="rl-score">Score &lt; 2.0</div>
    <div class="rl-meaning">Multiple serious red flags — high risk</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Handle heatmap bar click: pre-populate sector filter BEFORE widgets render
_hm_pending = st.session_state.pop("_hm_click", None)
if _hm_pending and _hm_pending in scored_df["Sector"].dropna().unique():
    st.session_state["tbl_sector"] = [_hm_pending]

# ── Filter bar — row 1: search · sector · min score ────────────────────────
_SORT_MAP = {
    "Value Score": "value_score",
    "P/E Ratio":   "PE Ratio",
    "P/B Ratio":   "PB Ratio",
    "ROE %":       "ROE (%)",
    "D/E Ratio":   "Debt/Equity",
    "Rev Growth":  "Revenue Growth (%)",
    "Price":       "Current Price",
}

_fb1, _fb2, _fb3 = st.columns([3, 3, 2])
with _fb1:
    _search = st.text_input(
        "search", placeholder="🔍  Symbol or company name…",
        label_visibility="collapsed", key="tbl_search",
    )
with _fb2:
    _sectors = sorted(scored_df["Sector"].dropna().unique().tolist())
    _sel_sectors = st.multiselect(
        "sector", _sectors,
        placeholder="All sectors…",
        label_visibility="collapsed", key="tbl_sector",
    )
with _fb3:
    if "min_score" not in st.session_state:
        st.session_state["min_score"] = 0.0
    _min_score = st.slider(
        "min_score", 0.0, 10.0, step=0.5, format="Min score: %.1f",
        label_visibility="collapsed", key="min_score",
    )

# ── Filter bar — row 2: rating · sort-by · direction ───────────────────────
_fb4, _fb5, _fb6 = st.columns([5, 3, 1])
with _fb4:
    _RATING_OPTS = ["All", "Strong Buy", "Buy", "Watch", "Hold", "Avoid", "Strong Avoid"]
    _sel_rating = st.radio(
        "Rating", _RATING_OPTS, horizontal=True,
        label_visibility="collapsed", key="rating_filter",
    )
with _fb5:
    _sort_labels = list(_SORT_MAP.keys())
    _sort_lbl = st.selectbox(
        "sort", _sort_labels,
        label_visibility="collapsed", key="tbl_sort_lbl",
    )
    _sort_col_key = _SORT_MAP[_sort_lbl]
with _fb6:
    _sort_asc = st.checkbox("↑ Asc", key="sort_asc")

# ── Apply all filters ───────────────────────────────────────────────────────
_table_df = scored_df.copy()
if _sel_rating != "All":
    _table_df = _table_df[_table_df["rating"] == _sel_rating]
if _search:
    _q = _search.strip().upper()
    _table_df = _table_df[
        _table_df["Symbol"].str.upper().str.contains(_q, na=False) |
        _table_df["Company"].fillna("").str.upper().str.contains(_q, na=False)
    ]
if _sel_sectors:
    _table_df = _table_df[_table_df["Sector"].isin(_sel_sectors)]
if _min_score > 0:
    _table_df = _table_df[_table_df["value_score"] >= _min_score]
_table_df = _table_df.sort_values(
    _sort_col_key, ascending=_sort_asc, na_position="last"
).reset_index(drop=True)

# ── Count + export row ──────────────────────────────────────────────────────
_cnt_col, _dl_col = st.columns([5, 1])
with _cnt_col:
    _active_filters = any([
        _sel_rating != "All", _search, _sel_sectors, _min_score > 0,
    ])
    if _active_filters:
        st.caption(f"Showing **{len(_table_df)}** of {len(scored_df)} stocks")
with _dl_col:
    st.download_button(
        "⬇ Export CSV",
        data=_table_df.to_csv(index=False),
        file_name=f"nse_screen_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown(_render_table_html(_table_df), unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Sector Heatmap
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-head">🗂️ &nbsp;Sector Heatmap</div>', unsafe_allow_html=True)
st.caption(
    "Average Value Score per sector — colours are **relative** within the current screen "
    "(best sector = green, worst = red). Click any bar to filter the table by that sector."
)

_hm_data = scored_df.dropna(subset=["Sector"]).copy()
if not _hm_data.empty:
    _hm_grp = (
        _hm_data.groupby("Sector")["value_score"]
        .agg(mean="mean", count="count")
        .reset_index()
        .sort_values("mean", ascending=True)
    )
    _scores_list = _hm_grp["mean"].tolist()
    _hm_fig = go.Figure(go.Bar(
        x=_scores_list,
        y=_hm_grp["Sector"],
        orientation="h",
        marker=dict(
            # Continuous colorscale mapped to the ACTUAL data range so we
            # always see contrast: worst sector → red, best sector → green.
            color=_scores_list,
            colorscale=[[0.0, "#f87171"], [0.5, "#fbbf24"], [1.0, "#34d399"]],
            cmin=min(_scores_list),
            cmax=max(_scores_list),
            showscale=False,
            line=dict(width=0),
        ),
        text=[f'  {s:.2f}  ({n} stocks)' for s, n in zip(_scores_list, _hm_grp["count"])],
        textposition="auto",
        textfont=dict(color="#f1f5f9", size=11),
        hovertemplate="<b>%{y}</b><br>Avg Score: %{x:.2f}<extra></extra>",
    ))
    _hm_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=12),
        margin=dict(l=10, r=20, t=10, b=10),
        xaxis=dict(
            range=[0, 10],
            gridcolor="rgba(255,255,255,0.06)",
            tickfont=dict(color="#64748b"),
            showgrid=True,
        ),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#94a3b8")),
        height=max(240, len(_hm_grp) * 34 + 40),
    )
    _hm_event = st.plotly_chart(
        _hm_fig,
        use_container_width=True,
        config={"displayModeBar": False},
        on_select="rerun",
        key="hm_chart",
    )
    # When the user clicks a bar, store the sector and rerun so the filter
    # bar (rendered earlier in the page) picks it up via _hm_pending above.
    try:
        _pts = (_hm_event or {}).get("selection", {}).get("points", [])
        if _pts:
            _clicked_sector = _pts[0].get("y")
            if _clicked_sector and st.session_state.get("_hm_click") != _clicked_sector:
                st.session_state["_hm_click"] = _clicked_sector
                st.rerun()
    except Exception:
        pass
else:
    st.caption("No sector data available for the current screen.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Stock Comparison — radar chart
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-head">🔄 &nbsp;Stock Comparison</div>', unsafe_allow_html=True)
st.caption("Select 2–4 stocks to compare across all 6 factors on a radar chart.")

_comp_syms = scored_df["Symbol"].str.replace(".NS", "", regex=False).tolist()
_comp_sel  = st.multiselect(
    "compare", _comp_syms,
    default=_comp_syms[:2] if len(_comp_syms) >= 2 else _comp_syms,
    max_selections=4,
    label_visibility="collapsed",
    key="comparison_stocks",
)

if len(_comp_sel) >= 2:
    _radar_factors  = ["P/E", "P/B", "ROE", "D/E", "Growth", "52W Pos"]
    _radar_cols     = ["pe_score", "pb_score", "roe_score", "de_score", "growth_score", "week52_score"]
    _fill_colors    = ["rgba(139,92,246,0.12)", "rgba(52,211,153,0.12)", "rgba(248,113,113,0.12)", "rgba(251,191,36,0.12)"]
    _line_colors    = ["#8b5cf6", "#34d399", "#f87171", "#fbbf24"]
    _theta_closed   = _radar_factors + [_radar_factors[0]]

    _fig_radar = go.Figure()
    for _ci, _sym in enumerate(_comp_sel):
        _row = scored_df[scored_df["Symbol"].str.replace(".NS", "", regex=False) == _sym]
        if _row.empty:
            continue
        _r    = _row.iloc[0]
        _vals = [float(_r.get(c, 5)) for c in _radar_cols]
        _fig_radar.add_trace(go.Scatterpolar(
            r=_vals + [_vals[0]],
            theta=_theta_closed,
            fill="toself",
            fillcolor=_fill_colors[_ci % 4],
            line=dict(color=_line_colors[_ci % 4], width=2),
            name=_sym,
            hovertemplate="<b>%{theta}</b>: %{r:.1f}/10<extra>" + _sym + "</extra>",
        ))
    _fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 10],
                tickfont=dict(color="#64748b", size=9),
                gridcolor="rgba(255,255,255,0.08)",
            ),
            angularaxis=dict(
                tickfont=dict(color="#94a3b8", size=11),
                gridcolor="rgba(255,255,255,0.08)",
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        legend=dict(font=dict(color="#94a3b8", size=12)),
        margin=dict(l=40, r=40, t=40, b=40),
        height=400,
    )
    st.plotly_chart(_fig_radar, use_container_width=True, config={"displayModeBar": False})
elif len(_comp_sel) == 1:
    st.caption("Select at least one more stock to enable comparison.")

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

"""AI consensus analysis for the Macro Quant War Room.

Combines the regime/backtest/risk/rebalancer outputs with recent Yahoo
Finance news into a single LLM-generated narrative analysis, served for
free via the Gemini API.
"""

import os
from pathlib import Path

from google import genai
import yfinance as yf
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# See https://ai.google.dev/gemini-api/docs/models for the current free-tier catalog.
GEMINI_MODEL = "gemini-2.5-flash"
NEWS_TICKERS = ["SPY", "QQQ", "IBB"]
NEWS_PER_TICKER = 3


def _get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to the .env file next to this "
            "script (see .env.example) or export GEMINI_API_KEY in your shell. "
            "Get a free key at https://aistudio.google.com/apikey."
        )
    return genai.Client(api_key=api_key)


def fetch_recent_news(tickers=NEWS_TICKERS, limit_per_ticker=NEWS_PER_TICKER):
    """Pull a handful of recent Yahoo Finance headlines for each ticker."""
    items = []
    for ticker in tickers:
        try:
            raw = yf.Ticker(ticker).news or []
        except Exception:
            continue
        for entry in raw[:limit_per_ticker]:
            content = entry.get("content", {})
            title = content.get("title")
            if not title:
                continue
            link = (
                (content.get("canonicalUrl") or {}).get("url")
                or (content.get("clickThroughUrl") or {}).get("url")
            )
            items.append({
                "ticker": ticker,
                "title": title,
                "summary": content.get("summary") or "",
                "publisher": (content.get("provider") or {}).get("displayName", "Yahoo Finance"),
                "published": content.get("pubDate"),
                "link": link,
            })
    return items


def _build_context_summary(df, risk_df, slip_df=None):
    """Condense the pipeline's numeric outputs into a compact text bundle for the prompt."""
    latest = df.iloc[-1]
    risk_latest = risk_df.iloc[-1]

    sector_cols = [
        c for c in df.columns
        if c.endswith("_Z") and not c.startswith(("RiskOn", "EconExp", "Inflation"))
    ]
    sector_scores = latest[sector_cols].sort_values(ascending=False) if sector_cols else None

    lines = [
        f"Current regime state score: {latest.get('Regime_State_Score', float('nan')):+.2f}",
        f"Cash cushion target: {risk_latest.get('Cash_Weight', 0) * 100:.1f}%",
        f"QQQ weight: {risk_latest.get('QQQ_Weight', 0) * 100:.1f}%, "
        f"IBB weight: {risk_latest.get('IBB_Weight', 0) * 100:.1f}%",
    ]

    if sector_scores is not None and len(sector_scores):
        top = sector_scores.head(3)
        bottom = sector_scores.tail(3)
        lines.append(
            "Strongest sectors (Z-score): "
            + ", ".join(f"{k.replace('_Z', '')} {v:+.2f}" for k, v in top.items())
        )
        lines.append(
            "Weakest sectors (Z-score): "
            + ", ".join(f"{k.replace('_Z', '')} {v:+.2f}" for k, v in bottom.items())
        )

    if slip_df is not None and not slip_df.empty and "Action" in slip_df.columns:
        buys = slip_df[slip_df["Action"] == "BUY_MARKET"]
        if not buys.empty:
            lines.append(
                "Latest proposed trades: "
                + "; ".join(f"{row['Ticker']} {row['Target_Weight']}" for _, row in buys.iterrows())
            )

    return "\n".join(lines)


def generate_ai_consensus(df, risk_df, backtest_summary=None, slip_df=None, news_items=None):
    """Ask the LLM to synthesize the pipeline outputs and recent news into one consensus analysis."""
    client = _get_client()
    context = _build_context_summary(df, risk_df, slip_df)

    news_block = "No recent news retrieved."
    if news_items:
        news_block = "\n".join(f"- [{n['ticker']}] {n['title']} ({n['publisher']})" for n in news_items)

    backtest_block = ""
    if backtest_summary is not None:
        backtest_block = (
            f"\nBacktest: strategy total return {backtest_summary.get('strategy_total_return_pct', float('nan')):.1f}%, "
            f"Sharpe {backtest_summary.get('strategy_sharpe_ratio', float('nan')):.2f}, "
            f"max drawdown {backtest_summary.get('strategy_max_drawdown_pct', float('nan')):.1f}%, "
            f"alpha vs SPY {backtest_summary.get('alpha_vs_spy_pct', float('nan')):+.1f}%."
        )

    prompt = (
        "You are a macro quant analyst reviewing a systematic sector-rotation strategy's latest output. "
        "Write a concise consensus analysis (250-350 words) covering: (1) what the current regime score "
        "and sector data imply, (2) how the recent news headlines below might reinforce or contradict that "
        "read, (3) key risks to watch, and (4) an overall stance (bullish / neutral / cautious) with a "
        "one-line rationale. Be specific and reference the actual numbers given. Frame this as a research "
        "note, not individualized investment advice.\n\n"
        f"--- Quantitative snapshot ---\n{context}{backtest_block}\n\n"
        f"--- Recent news headlines ---\n{news_block}"
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text.strip()

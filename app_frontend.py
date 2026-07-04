"""Streamlit dashboard for the Macro Quant War Room.

This front-end provides interactive workflow controls, regime monitoring,
valuation tools, and visualizations for the macro quant system.
"""

import subprocess
import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

import ai_analyst

ROOT = Path(__file__).parent

# --- APP LAYOUT CONFIGURATION ---
st.set_page_config(page_title="Macro War Room Dashboard", layout="wide")

st.title("⚡ MACRO QUANT WAR ROOM")
st.subheader("Institutional State Detector, Risk Optimization, & Automated Rebalancer")
st.markdown("---")


def section_header(title, explanation, level="###"):
    """Render a section header with a click-to-open plain-English explainer beside it."""
    head_col, info_col = st.columns([8, 1])
    with head_col:
        st.write(f"{level} {title}")
    with info_col:
        with st.popover("❓ ELI5"):
            st.markdown(explanation)


def sidebar_section_header(title, explanation):
    """Same as section_header, but for the sidebar."""
    head_col, info_col = st.sidebar.columns([4, 1])
    with head_col:
        st.write(f"### {title}")
    with info_col:
        with st.popover("❓"):
            st.markdown(explanation)

# --- CENTRALIZED AUTOMATION PROCESS ENGINE ---
def execute_system_subprocess(script_path, operational_step_name):
    """Execute an external pipeline script and report the result in the sidebar."""
    python_exe = sys.executable
    def _run(cmd_args):
        try:
            result = subprocess.run(cmd_args, capture_output=True, text=True, check=True)
            st.sidebar.success(f"✅ {operational_step_name} Succeeded!")
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    # default invocation
    cmd = [python_exe, script_path]
    return _run(cmd)

# --- SIDEBAR CONTROL PANEL ---
sidebar_section_header(
    "🕹️ Live Infrastructure Controls",
    "These buttons are like pressing **go** on machines in a factory line, one after another:\n\n"
    "- **Data Ingestion** grabs fresh numbers from the internet (interest rates, stock prices).\n"
    "- **State Detection Engine** does the math to figure out if the economy looks *sunny* or *stormy* "
    "right now, checks how well our strategy would have done in the past, works out how much cash to "
    "keep safe, and prints a shopping list of trades.\n\n"
    "You click them in order, and each one hands its answer to the next, like an assembly line."
)

if st.sidebar.button("🔄 Execute Data Ingestion Pipeline"):
    with st.spinner("Executing Data Downloader..."):
        execute_system_subprocess(ROOT / "pipeline_data.py", "Data Ingestion Pipeline")

if st.sidebar.button("🧠 Compute State Detection Engine"):
    with st.spinner("Processing Matrix Weights..."):
        execute_system_subprocess(ROOT / "engine_regime.py", "Regime Scoring Engine")
        execute_system_subprocess(ROOT / "engine_backtest.py", "Portfolio Performance Backtest")
        execute_system_subprocess(ROOT / "portfolio_manager.py", "Risk Matrix Optimizer")
        execute_system_subprocess(ROOT / "macro_rebalancer.py", "Automated Order Rebalancer")
    st.sidebar.success("All Systems Synchronized!")

# --- DATA STORAGE BRIDGE ---
try:
    df = pd.read_csv(ROOT / "processed_regime_matrix.csv", index_col=0, parse_dates=True).sort_index()
    risk_df = pd.read_csv(ROOT / "portfolio_risk_metrics.csv", index_col=0, parse_dates=True).sort_index()
    latest_row = risk_df.iloc[-1]
    current_score = df["Regime_State_Score"].iloc[-1]
except Exception:
    st.info("💡 Welcome to your War Room. Click the sidebar execution buttons to bootstrap your local data analytics streams.")
    try:
        st.stop()
    except Exception:
        pass
    sys.exit(0)

# --- METRIC PRESENTATION SUITE ---
m1, m2, m3, m4 = st.columns([3, 3, 3, 1])
with m1:
    st.metric(label="Current Macro State Vector", value=f"{current_score:+.2f}")
with m2:
    status = "LIQUIDITY EXPANSION" if current_score > 0.3 else "LIQUIDITY SQUEEZE" if current_score < -0.3 else "NEUTRAL STATE"
    st.metric(label="Detected Structural Regime", value=status)
with m3:
    st.metric(label="System Cash Cushion Target", value=f"{latest_row['Cash_Weight']*100:.1f}%")
with m4:
    with st.popover("❓ ELI5"):
        st.markdown(
            "**Macro State Vector**: one number that sums up the economy's *mood* - positive means "
            "things look healthy and growing, negative means things look tight and risky.\n\n"
            "**Structural Regime**: the plain-English label for that number, like calling 70°F "
            "'warm' instead of just saying '70'.\n\n"
            "**Cash Cushion**: how much money we'd keep as safe cash instead of investing, like keeping "
            "some of your allowance in a piggy bank instead of spending all of it, just in case."
        )

st.markdown("---")

# --- AI CONSENSUS ANALYSIS ---
section_header(
    "🤖 AI Consensus Analysis",
    "This asks a large language model (an AI, similar in kind to ChatGPT, but here it's Google's Gemini "
    "on its free tier) to read everything on this page - the regime score, sector "
    "strengths, backtest results, and proposed trades - plus a few recent news headlines, and write a "
    "short plain-English research note connecting them. Think of it as asking a sharp research assistant "
    "to turn a big spreadsheet into a few paragraphs you can actually read. Generation only runs when you "
    "click the button."
)

if st.button("✨ Generate AI Analysis"):
    with st.spinner("Reading the data and recent news, then asking the AI for a consensus read..."):
        try:
            backtest_summary_row = None
            backtest_summary_path = ROOT / "backtest_summary_metrics.csv"
            if backtest_summary_path.exists():
                backtest_summary_row = pd.read_csv(backtest_summary_path).iloc[0].to_dict()

            slip_df_for_ai = None
            slip_path_for_ai = ROOT / "execution_order_slip.csv"
            if slip_path_for_ai.exists():
                slip_df_for_ai = pd.read_csv(slip_path_for_ai)

            news_items = ai_analyst.fetch_recent_news()
            analysis_text = ai_analyst.generate_ai_consensus(
                df, risk_df,
                backtest_summary=backtest_summary_row,
                slip_df=slip_df_for_ai,
                news_items=news_items,
            )
            st.markdown(analysis_text)

            if news_items:
                with st.expander("📰 News headlines used in this analysis"):
                    for n in news_items:
                        if n.get("link"):
                            st.markdown(f"- [{n['title']}]({n['link']}) — *{n['publisher']}* ({n['ticker']})")
                        else:
                            st.markdown(f"- {n['title']} — *{n['publisher']}* ({n['ticker']})")
        except Exception as e:
            st.error(f"AI analysis failed: {e}")

st.markdown("---")

# --- TIMELINE SYNC CHART ---
section_header(
    "📊 Cross-Asset Timeline Sync",
    "Think of the black line as a weather forecast for the economy - up means *sunny* (good for "
    "investing), down means *stormy* (riskier). The colored lines below show how three different "
    "investments grew over that same time (SPY = the whole stock market, QQQ = tech-heavy stocks, "
    "IBB = biotech stocks), all starting from the same point so we can compare who grew fastest."
)
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08)
fig.add_trace(go.Scatter(x=df.index, y=df["Regime_State_Score"], name="Regime Score Vector", line=dict(color="black", width=2.5)), row=1, col=1)

for ticker in ["SPY", "QQQ", "IBB"]:
    norm_perf = (df[ticker] / df[ticker].iloc[0]) * 100
    fig.add_trace(go.Scatter(x=df.index, y=norm_perf, name=f"{ticker} Momentum"), row=2, col=1)

fig.update_layout(template="plotly_white", height=600, hovermode="x unified")
# RESOLVED LAYOUT WARNINGS: Upgraded structural element container parameters
st.plotly_chart(fig, width="stretch")

# --- SECTOR ROTATION HEATMAP ---
st.markdown("---")
section_header(
    "🔥 Dynamic Sector Rotation Heatmap",
    "Imagine 11 classrooms, each one a different part of the economy (Tech class, Energy class, "
    "Health class, and so on). Each box is colored like a thermometer: blue means that classroom is "
    "doing better than its own normal, red means it's doing worse than its own normal. This helps spot "
    "which parts of the economy are 'hot' or 'cold' right now."
)
try:
    # Define sectors order for the heatmap
    sectors = ["XLK","XLY","XLP","XLE","XLF","XLI","XLV","XLB","XLU","XLC","XLRE"]
    zcols = [f"{s}_Z" for s in sectors]

    if all(c in df.columns for c in zcols):
        latest = df[zcols].iloc[-1]
        heat_vals = latest.values.reshape(len(sectors), 1)

        heatmap = go.Figure(data=go.Heatmap(
            z=heat_vals,
            x=["Z-Score"],
            y=sectors,
            colorscale="RdBu",
            zmid=0,
            colorbar=dict(title="Z")
        ))

        heatmap.update_layout(height=500, template="plotly_white")
        st.plotly_chart(heatmap, width="stretch")
        # Add annotated values as a compact table
        score_df = pd.DataFrame({"Sector": sectors, "Z": latest.values})
        st.table(score_df.style.format({"Z": "{:.2f}"}))
    else:
        st.info("Sector Z-scores not yet available. Run the State Detection Engine to compute them.")
except Exception:
    st.info("Unable to render sector heatmap at this time.")
    
# --- FACTOR OVERLAY PANEL ---
st.markdown("---")
section_header(
    "📈 Factor Overlay & Multi-Asset Signals",
    "**Momentum** answers: 'Has this investment been going up lately?' - like checking if a ball "
    "rolling downhill is speeding up or slowing down.\n\n"
    "**Valuation ratios** (P/E, P/B, etc.) answer: 'Is this expensive or cheap compared to what the "
    "company actually earns or owns?' - like comparing the price tags on two same-size backpacks to "
    "see which is the better deal.\n\n"
    "**Alternative signals** are extra clues from outside the stock market, like counting how much "
    "freight is being shipped, to guess how the economy is really doing."
)
try:
    momentum_cols = [c for c in df.columns if c.startswith("Momentum_")]
    valuation_cols = [c for c in df.columns if c.startswith(("PE_","PB_","ROE_","DE_"))]
    alt_cols = [c for c in ["Baltic_Dry", "Cass_Freight", "Consumer_Sentiment", "Dollar_Index"] if c in df.columns]

    if momentum_cols:
        latest_mom = df[momentum_cols].iloc[-1].sort_values(ascending=False)
        st.write("#### Latest 12-Month Momentum")
        st.table(latest_mom.to_frame("Momentum").style.format({"Momentum": "{:.2%}"}))

    if valuation_cols:
        latest_vals = df[valuation_cols].iloc[-1].round(2)
        st.write("#### Current Factor Snapshots")
        st.table(latest_vals.to_frame("Latest"))

    if alt_cols:
        st.write("#### Alternative Macro Signals")
        alt_latest = df[alt_cols].iloc[-1]
        alt_df = alt_latest.to_frame("Latest").round(2)
        st.table(alt_df)

    if not momentum_cols and not valuation_cols and not alt_cols:
        st.info("Factor and alternative data not yet available. Run the pipeline to populate these signals.")
except Exception:
    st.info("Unable to render the factor overlay panel at the moment.")

# --- HISTORICAL ANIMATION (SECTOR ROTATION OVER TIME) ---
st.markdown("---")
section_header(
    "🎞️ Historical Sector Rotation Movie",
    "This is the sector heatmap from above, but played like a time-lapse video, so you can watch "
    "which parts of the economy were 'hot' or 'cold' month by month, instead of only seeing right now. "
    "Press **Play** to watch it move through history."
)
try:
    anim_sectors = ["XLK","XLY","XLP","XLE","XLF","XLI","XLV","XLB","XLU","XLC","XLRE"]
    anim_zcols = [f"{s}_Z" for s in anim_sectors]
    if all(c in df.columns for c in anim_zcols):
        # Build a 2D matrix: time x sectors
        hist = df[anim_zcols].copy()
        hist.index = hist.index.strftime('%Y-%m')

        fig_anim = go.Figure()
        # Initial frame (first time point)
        first = hist.iloc[0].values.reshape(len(anim_sectors), 1)
        fig_anim.add_trace(go.Heatmap(z=first, x=[hist.index[0]], y=anim_sectors, colorscale='RdBu', zmid=0))

        # Build frames for each time step
        frames = []
        for t_idx, t in enumerate(hist.index):
            z = hist.iloc[t_idx].values.reshape(len(anim_sectors), 1)
            frames.append(dict(data=[go.Heatmap(z=z, x=[t], y=anim_sectors, colorscale='RdBu', zmid=0)], name=str(t)))

        fig_anim.frames = frames

        # Slider and play button
        fig_anim.update_layout(
            updatemenus=[dict(type="buttons", showactive=False,
                              y=1.05, x=1.15, xanchor="right",
                              buttons=[dict(label="Play",
                                            method="animate",
                                            args=[None, {"frame": {"duration": 300, "redraw": True}, "fromcurrent": True}])])]
        )

        fig_anim.update_layout(width=900, height=600, template='plotly_white', title='Sector Rotation: Historical Z-scores')
        st.plotly_chart(fig_anim, width="stretch")

        # Quadrant legend description (static)
        st.markdown("**Quadrant Guide:**")
        st.write("- Top: Liquidity/Risk-on sectors (Tech, Discretionary).\n- Right: Cyclical strength (Energy, Materials, Industrials).\n- Bottom: Defensive (Staples, Utilities, Healthcare).\n- Left: Rate-sensitive/Financials and Real Estate.")
    else:
        st.info("Historical sector animation requires computed sector Z-scores. Run engine.")
except Exception:
    pass


# --- FUNDAMENTALS TAB: VALUATION TOOLKIT ---
st.markdown("---")
section_header(
    "🧾 Fundamentals: Company Valuation Toolkit (DCF & Ratios)",
    "This tool guesses what a company is really worth. It asks: 'How much cash will this company make "
    "every year for the next few years, and how much is that future cash worth in today's dollars?' "
    "Money today is worth more than the same amount later - a dollar now can start earning more dollars "
    "- so we *discount* future cash to make it comparable, similar to knowing $10 today beats a promise "
    "of $10 next year."
)

col1, col2 = st.columns([2,1])
with col1:
    symbol = st.text_input("Ticker (Yahoo) for Valuation", value="SPY")
    periods = st.selectbox("DCF Forecast Years", options=[3,5,7,10], index=1)
    growth = st.number_input("Forecast annual growth rate (FCF %)", value=0.05, step=0.01, format="%.3f")
    discount = st.number_input("Discount rate (WACC) %", value=0.10, step=0.005, format="%.3f")
    terminal_method = st.selectbox("Terminal Value Method", options=["Gordon", "Exit Multiple"], index=0)
    if terminal_method == "Gordon":
        term_growth = st.number_input("Terminal growth rate %", value=0.02, step=0.005, format="%.3f")
    else:
        exit_multiple = st.number_input("Exit EV/FCF multiple", value=10.0, step=0.5)
    if st.button("Run Valuation"):
        try:
            tk = yf.Ticker(symbol)
            info = tk.info if hasattr(tk, 'info') else {}

            # Price
            hist = tk.history(period="1d")
            price = float(hist['Close'].iloc[-1]) if not hist.empty else info.get('previousClose', None)

            # Try to obtain free cash flow (annual)
            fcf = None
            if info.get('freeCashflow'):
                fcf = float(info.get('freeCashflow'))
            else:
                try:
                    cf = tk.cashflow
                    # cashflow columns are recent years; compute most recent FCF estimate
                    if 'Capital Expenditures' in cf.index and 'Total Cash From Operating Activities' in cf.index:
                        fcf = float(cf.loc['Total Cash From Operating Activities'].iloc[0] + cf.loc.get('Capital Expenditures', pd.Series([0])).iloc[0])
                except Exception:
                    fcf = None

            shares_out = info.get('sharesOutstanding', None)
            market_cap = info.get('marketCap', None)
            if shares_out is None and market_cap and price:
                shares_out = market_cap / price

            # Prepare ratio summary
            ratios = {
                'Price': price,
                'Trailing P/E': info.get('trailingPE'),
                'Forward P/E': info.get('forwardPE'),
                'Price/Book': info.get('priceToBook'),
                'Market Cap': market_cap,
                'Shares Outstanding': shares_out
            }

            st.write("**Key Ratios**")
            st.table(pd.DataFrame.from_dict(ratios, orient='index', columns=['Value']))

            # DCF
            if fcf is None or fcf == 0:
                st.warning("Unable to derive Free Cash Flow for DCF. Using market-based ratios only.")
            else:
                proj = []
                last_fcf = float(fcf)
                for i in range(1, periods+1):
                    fc = last_fcf * ((1.0 + growth) ** i)
                    proj.append(fc)

                # Discount projected FCF
                disc_rates = [(1.0 / ((1.0 + discount) ** i)) for i in range(1, periods+1)]
                pv_proj = sum([p * d for p, d in zip(proj, disc_rates)])

                # Terminal value
                if terminal_method == 'Gordon':
                    tv = proj[-1] * (1.0 + term_growth) / max((discount - term_growth), 1e-6)
                else:
                    tv = proj[-1] * exit_multiple

                pv_tv = tv * (1.0 / ((1.0 + discount) ** periods))
                enterprise_value = pv_proj + pv_tv

                if shares_out:
                    intrinsic_per_share = enterprise_value / shares_out
                elif market_cap:
                    intrinsic_per_share = enterprise_value / (market_cap / price)
                else:
                    intrinsic_per_share = None

                st.write("**DCF Results**")
                dcf_table = {
                    'Discounted Projected FCF (PV)': pv_proj,
                    'Discounted Terminal Value (PV)': pv_tv,
                    'Enterprise Value (PV Total)': enterprise_value,
                    'Intrinsic Value / Share': intrinsic_per_share,
                }
                st.table(pd.DataFrame.from_dict(dcf_table, orient='index', columns=['Value']))

        except Exception as e:
            st.error(f"Valuation failed: {e}")
with col2:
    st.write("Use this toolkit to run a quick DCF and view basic valuation multiples. For deeper fundamental analysis, consider adding a fundamentals dataset (10-K/10-Q parsing, analyst estimates, or premium data feeds).")

# --- DRAWDOWN MATRIX STRESS GAUGE ---
st.markdown("---")
section_header(
    "🛡️ Drawdown Profile Stress-Testing",
    "A drawdown measures how far something has fallen from its highest point - like measuring how far "
    "you slid back down after climbing partway up a hill. This chart compares the biggest 'slides' of "
    "our strategy versus just holding the S&P 500, showing how bumpy the ride can get even when the "
    "long-term direction is up."
)
fig_dd = go.Figure()
fig_dd.add_trace(go.Scatter(x=risk_df.index, y=risk_df["Strategy_DD"], name="Regime Allocation Strategy", fill='tozeroy', line=dict(color="red")))
fig_dd.add_trace(go.Scatter(x=risk_df.index, y=risk_df["SPY_DD"], name="S&P 500 Benchmark", line=dict(color="grey", dash="dash")))
fig_dd.update_layout(template="plotly_white", height=300)
st.plotly_chart(fig_dd, width="stretch")

# --- AUTOMATED ORDER SLIP REBALANCER MATRIX VIEW ---
st.markdown("---")
section_header(
    "📜 Automated Execution Order Slip Ticket",
    "Once the model decides which sectors look best, this turns that decision into an actual shopping "
    "list: exactly how many shares of each thing to buy, plus the price, fees, and 'slippage' (extra "
    "cost from the price moving slightly while your order is being filled) - like a receipt printed "
    "before you even walk into the store."
)
slip_file = ROOT / "execution_order_slip.csv"

if os.path.exists(slip_file):
    slip_df = pd.read_csv(slip_file)
    # RESOLVED CONTAINER LAYOUT WARNINGS: Adjusted dataframe parameter width to conform to stretch styles
    st.dataframe(slip_df, width="stretch")
    
    with open(slip_file, "r") as f:
        st.download_button(
            label="📥 Download CSV Execution Ticket to Broker",
            data=f.read(),
            file_name="execution_order_slip.csv",
            mime="text/csv",
            width="stretch"
        )
else:
    st.info("Execute the State Engine via the controls menu to display your actionable target trade allocation slip records.")

# --- REBALANCER PARAMS (Sidebar) ---
st.sidebar.markdown("---")
sidebar_section_header(
    "🧾 Rebalancer Parameters",
    "These sliders change the *rules* the shopping list follows:\n\n"
    "- **Allocation Method** decides how we split money between winning sectors.\n"
    "- **Min Z threshold** ignores sectors that aren't doing well enough to bother with.\n"
    "- **Max weight per sector** stops us from putting too many eggs in one basket.\n"
    "- **Portfolio Value** is simply how much total money we're pretending to invest."
)
method = st.sidebar.selectbox("Allocation Method", options=["positive","softmax"], index=0)
min_z = st.sidebar.slider("Min Z threshold", -1.0, 3.0, 0.0, 0.1)
max_w = st.sidebar.slider("Max weight per sector (%)", 1, 50, 20)
temperature = st.sidebar.number_input("Softmax temperature", min_value=0.01, value=1.0)
portfolio_val = st.sidebar.number_input("Portfolio Value (USD)", min_value=1000.0, value=100000.0)

if st.sidebar.button("🧾 Generate Execution Slip (Heatmap-driven) "):
    # Build command line args
    python_exe = sys.executable
    script = ROOT / "macro_rebalancer.py"
    cmd = [python_exe, script, f"--portfolio={portfolio_val}", f"--min-z={min_z}", f"--max-weight={max_w/100.0}", f"--method={method}", f"--temperature={temperature}"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        st.sidebar.success("Execution Slip Generated")
        # refresh display
        if os.path.exists(slip_file):
            slip_df = pd.read_csv(slip_file)
            st.dataframe(slip_df, width="stretch")
    except subprocess.CalledProcessError as e:
        st.sidebar.error(f"Failed to generate slip: {e.stderr}")


# --- STEP 2 INTEGRATION: THE PERFORMANCE TAB ---
try:
    backtest_df = pd.read_csv(ROOT / "backtest_performance_results.csv", index_col=0, parse_dates=True)
    
    st.markdown("---")
    section_header(
        "📈 Capital Growth Backtest Audit",
        "This shows what a single dollar would have grown into over time if you'd followed our "
        "strategy, compared to if you'd just bought the S&P 500 and never touched it again. It's "
        "basically a race between two piggy banks that both started with $1."
    )

    fig_perf = go.Figure()
    fig_perf.add_trace(go.Scatter(x=backtest_df.index, y=backtest_df["Strategy_Cum"], name="Dynamic Regime Strategy", line=dict(color="green", width=3)))
    fig_perf.add_trace(go.Scatter(x=backtest_df.index, y=backtest_df["SPY_Cum"], name="S&P 500 Benchmark", line=dict(color="grey", dash="dash")))
    
    fig_perf.update_layout(template="plotly_white", height=450, title="Growth of $1 Over Time (Regime Switching Strategy vs. Buy & Hold)")
    st.plotly_chart(fig_perf, width="stretch")
except Exception:
    pass

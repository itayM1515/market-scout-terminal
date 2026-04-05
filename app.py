import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# --- הגדרות דף ---
st.set_page_config(page_title="Market Scout | Institutional Terminal", layout="wide")

# --- CSS עיצוב מוסדי נעול (הסטנדרט שלך) ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-left: 2rem; padding-right: 2rem; max-width: 100%; }
    .stApp { background-color: #0c1017; color: #ffffff; }
    
    .stat-container { margin-bottom: 20px; }
    .stat-label { color: #adb5bd; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; margin-bottom: 2px; }
    .stat-value { font-size: 2rem !important; font-weight: 900 !important; line-height: 1.1; margin-bottom: 15px; }
    
    .analysis-section { background-color: #ffda1a; padding: 15px; border-radius: 8px; margin-top: 20px; color: #000000; }
    .analysis-header { font-weight: 900; font-size: 1rem; margin-bottom: 10px; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 5px; }
    .analysis-item { font-size: 0.9rem; font-weight: 700; margin-bottom: 6px; }
    
    .ticker-highlight { color: #FFD60A; background-color: rgba(255, 214, 10, 0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(255, 214, 10, 0.3); font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

def render_stat(label, value, color="#FFFFFF"):
    st.markdown(f'<div class="stat-container"><p class="stat-label">{label}</p><p class="stat-value" style="color: {color};">{value}</p></div>', unsafe_allow_html=True)

# --- מנוע נתונים מקצועי (Alpha Vantage) ---
@st.cache_data(ttl=300)
def get_reliable_data(ticker_symbol):
    api_key = "N3GVW283WK6UOAZ6" # המפתח שקיבלת
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker_symbol}&outputsize=compact&apikey={api_key}'
    try:
        r = requests.get(url)
        data = r.json()
        
        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            return df, "LIVE (AlphaVantage)"
    except Exception:
        pass
    return None, "OFFLINE"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ TERMINAL SETTINGS")
    ticker_input = st.text_input("Ticker:", value="GOOG").upper().strip()
    
    # לוגיקת קפיצות סכום
    if 'cap_val' not in st.session_state: st.session_state.cap_val = 70000.0
    c_step = 1000.0 if st.session_state.cap_val < 10000 else 5000.0
    cap_input = st.number_input("Capital ($)", value=st.session_state.cap_val, step=c_step)
    st.session_state.cap_val = cap_input 
    
    sl_pct = st.number_input("Stop Loss (%)", value=3.0, step=0.5)
    
    df, status = get_reliable_data(ticker_input)
    
    if df is not None:
        curr_p = float(df['Close'].iloc[-1])
        ema50 = df['Close'].ewm(span=50).mean().iloc[-1]
        st.markdown(f"""
        <div class="analysis-section">
            <div class="analysis-header">📊 SMC ANALYSIS</div>
            <div class="analysis-item">Structure: {"BULLISH 🚀" if curr_p > ema50 else "BEARISH 🔴"}</div>
            <div class="analysis-item">Source: {status}</div>
            <div class="analysis-item">Trend (EMA50): ${ema50:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🚀 RUN ANALYSIS"): st.rerun()

# --- MAIN ENGINE ---
if df is not None:
    curr_p = float(df['Close'].iloc[-1])
    sl_p = curr_p * (1 - (sl_pct/100))
    tp_p = curr_p + (abs(curr_p - sl_p) * 3)
    risk_usd = cap_input * (sl_pct/100)

    st.markdown(f'### 🖥️ ANALYZER | <span class="ticker-highlight">{ticker_input}</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # 6 המדדים
    c1, c2, c3 = st.columns(3)
    with c1: 
        render_stat("CURRENT PRICE", f"${curr_p:,.2f}")
        render_stat("ENTRY POI", f"${curr_p:,.2f}", "#FF8C00") 
    with c2:
        render_stat("STOP LOSS PRICE", f"${sl_p:,.2f}", "#FF1744")
        render_stat("RISK (-$)", f"-${risk_usd:,.0f}", "#FF1744")
    with c3:
        render_stat("TAKE PROFIT PRICE", f"${tp_p:,.2f}", "#00E676")
        render_stat("REWARD (+$)", f"+${risk_usd*3:,.0f}", "#00E676")

    # --- CHART ---
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#00E676', decreasing_line_color='#FF1744', 
        increasing_fillcolor='#00E676', decreasing_fillcolor='#FF1744'
    )])

    fig.add_hline(y=tp_p, line=dict(color="#00E676", width=1.5))
    fig.add_hline(y=curr_p, line=dict(color="#FF8C00", width=2, dash="dash"))
    fig.add_hline(y=sl_p, line=dict(color="#FF1744", width=1.5))

    fig.update_layout(
        template="plotly_dark", height=720, xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=50, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(side="right", gridcolor='rgba(255,255,255,0.05)', fixedrange=False, showgrid=True),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True, type='date')
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.error("❌ API Fetch Error. Verify your internet connection or Ticker symbol.")

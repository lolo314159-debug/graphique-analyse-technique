import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Terminal Analyse ATR", layout="wide")

# --- CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00CCFF; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Analyseur de Prix & Volatilité (ATR)")

# --- BARRE LATÉRALE ---
st.sidebar.header("Configuration")
ticker_input = st.sidebar.text_input("Symbole Actif", value="GOOGL")
periode = st.sidebar.selectbox("Période", ["3mo", "6mo", "1y", "2y", "5y", "max"], index=1)
atr_period = st.sidebar.slider("Période ATR", 5, 30, 14)

st.sidebar.markdown("---")
st.sidebar.write("**Guide des symboles :**")
st.sidebar.code("CAC 40 : ^FCHI\nOrange : ORAN.PA\nBitcoin : BTC-USD\nApple : AAPL")

# --- FONCTION DE CALCUL ---
@st.cache_data
def load_and_calc(symbol, p):
    df = yf.download(symbol, period=p, interval="1d")
    if df.empty:
        return None
    
    # Correction pour les nouvelles versions de yfinance (MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Calcul de l'ATR (Average True Range)
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = true_range.rolling(window=atr_period).mean()
    
    # Moyenne Mobile 20 de l'ATR
    df['ATR_SMA20'] = df['ATR'].rolling(window=20).mean()
    
    return df

# --- AFFICHAGE PRINCIPAL ---
if ticker_input:
    df = load_and_calc(ticker_input, periode)

    if df is not None:
        # Métriques rapides
        last_price = df['Close'].iloc[-1]
        last_atr = df['ATR'].iloc[-1]
        prev_atr_sma = df['ATR_SMA20'].iloc[-1]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Prix de Clôture", f"{last_price:.2f} $")
        c2.metric("ATR Actuel", f"{last_atr:.2f}")
        c3.metric("Tendance Volatilité", "HAUTE" if last_atr > prev_atr_sma else "BASSE", 
                  delta=f"{last_atr - prev_atr_sma:.2f}", delta_color="inverse")

        # --- CRÉATION DU GRAPHIQUE ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, 
                           row_heights=[0.7, 0.3])

        # 1. Bougies Japonaises
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Prix'
        ), row=1, col=1)

        # 2. ATR (Orange)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ATR'], 
            line=dict(color='#FF9900', width=2), 
            name=f'ATR {atr_period}',
            fill='tozeroy', fillcolor='rgba(255, 153, 0, 0.1)'
        ), row=2, col=1)

        # 3. SMA 20 de l'ATR (Cyan)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ATR_SMA20'], 
            line=dict(color='#00CCFF', width=2), 
            name='SMA 20 (ATR)'
        ), row=2, col=1)

        # Mise en forme globale
        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=750,
            margin=dict(t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_yaxes(title_text="Prix ($)", row=1, col=1)
        fig.update_yaxes(title_text="ATR", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)
        
        # Tableau de données
        with st.expander("Historique complet des données"):
            st.dataframe(df.style.format(precision=2))

    else:
        st.error(f"Erreur : Impossible de récupérer les données pour '{ticker_input}'.")

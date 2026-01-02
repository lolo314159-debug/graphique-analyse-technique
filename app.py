import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Analyseur de Volatilité Pro", layout="wide")

st.title("📈 Graphique en Bougies & Indicateur ATR")

# 2. Barre latérale
st.sidebar.header("🔍 Configuration")
ticker_input = st.sidebar.text_input("Symbole (Ticker)", value="GOOGL")
periode = st.sidebar.selectbox("Période", ["3mo", "6mo", "1y", "2y", "5y"], index=1)
atr_period = st.sidebar.slider("Période ATR", min_value=5, max_value=30, value=14)

# 3. Récupération et calculs
@st.cache_data
def get_financial_data(symbol, p):
    df = yf.download(symbol, period=p, interval="1d")
    if df.empty:
        return None
    
    # Nettoyage des colonnes si multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # --- CALCUL DE L'ATR ---
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR'] = true_range.rolling(window=atr_period).mean()
    
    # --- MOYENNE MOBILE DE L'ATR (SMA 20) ---
    df['ATR_SMA20'] = df['ATR'].rolling(window=20).mean()
    
    return df

if ticker_input:
    df = get_financial_data(ticker_input, periode)

    if df is not None:
        # 4. Création des sous-graphiques (2 lignes : Prix et ATR)
        # vertical_spacing ajuste l'écart entre les deux
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.1, 
                           row_heights=[0.7, 0.3])

        # --- GRAPHIQUE PRINCIPAL (BOUGIES) ---
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Prix'
        ), row=1, col=1)

        # --- GRAPHIQUE ATR (PANNEAU DU BAS) ---
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ATR'], 
            line=dict(color='orange', width=2), name=f'ATR ({atr_period})'
        ), row=2, col=1)

        # AJOUT DE LA SMA 20 SUR L'ATR
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ATR_SMA20'], 
            line=dict(color='cyan', width=1, dash='dot'), name='SMA 20 (ATR)'
        ), row=2, col=1)

        # 5. Mise en forme
        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False, # Désactivé pour mieux voir l'ATR
            height=800,
            title=f"Analyse Technique : {ticker_input}",
            yaxis_title="Prix",
            yaxis2_title="Volatilité (ATR)"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # Petit résumé de l'indicateur
        last_atr = df['ATR'].iloc[-1]
        st.info(f"💡 **Lecture de l'ATR :** La volatilité moyenne actuelle est de **{last_atr:.2f}**. "
                f"Si l'ATR orange est au-dessus de la ligne pointillée blanche, la volatilité augmente.")

    else:
        st.error("Symbole non trouvé.")

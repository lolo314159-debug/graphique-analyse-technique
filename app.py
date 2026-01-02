import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Terminal CAC 40 & ATR", layout="wide")

# --- DICTIONNAIRE DU CAC 40 ---
# Liste à jour des entreprises du CAC 40 avec leurs tickers correspondants
CAC40_DICT = {
    "Accor": "AC.PA", "Air Liquide": "AI.PA", "Airbus": "AIR.PA", "ArcelorMittal": "MT.AS",
    "AXA": "CS.PA", "BNP Paribas": "BNP.PA", "Bouygues": "EN.PA", "Capgemini": "CAP.PA",
    "Carrefour": "CA.PA", "Crédit Agricole": "ACA.PA", "Danone": "BN.PA", "Dassault Systèmes": "DSY.PA",
    "Edenred": "EDEN.PA", "Engie": "ENGI.PA", "EssilorLuxottica": "EL.PA", "Eurofins Scientific": "ERF.PA",
    "Hermès": "RMS.PA", "Kering": "KER.PA", "L'Oréal": "OR.PA", "Legrand": "LR.PA",
    "LVMH": "MC.PA", "Michelin": "ML.PA", "Orange": "ORAN.PA", "Pernod Ricard": "RI.PA",
    "Publicis Groupe": "PUB.PA", "Renault": "RNO.PA", "Safran": "SAF.PA", "Saint-Gobain": "SGO.PA",
    "Sanofi": "SAN.PA", "Schneider Electric": "SU.PA", "Société Générale": "GLE.PA", "Stellantis": "STLAP.PA",
    "STMicroelectronics": "STMPA.PA", "Teleperformance": "TEP.PA", "Thales": "HO.PA", "TotalEnergies": "TTE.PA",
    "Unibail-Rodamco-Westfield": "URW.PA", "Veolia": "VIE.PA", "Vinci": "DG.PA", "Vivendi": "VIV.PA"
}

st.title("🇫🇷 Terminal d'Analyse : CAC 40 & Volatilité")

# --- BARRE LATÉRALE ---
st.sidebar.header("🔍 Sélection de l'actif")

# Choix du mode de sélection
mode = st.sidebar.radio("Mode de sélection :", ["Liste CAC 40", "Saisie libre (Ticker US/Crypto)"])

if mode == "Liste CAC 40":
    nom_action = st.sidebar.selectbox("Choisissez une entreprise :", list(CAC40_DICT.keys()))
    ticker_final = CAC40_DICT[nom_action]
else:
    ticker_final = st.sidebar.text_input("Saisissez un symbole (ex: AAPL, BTC-USD) :", value="GOOGL")

st.sidebar.markdown("---")
periode = st.sidebar.selectbox("Période", ["3mo", "6mo", "1y", "2y", "5y", "max"], index=1)
atr_period = st.sidebar.slider("Période ATR", 5, 30, 14)

# --- FONCTION DE CALCUL ---
@st.cache_data
def load_and_calc(symbol, p):
    df = yf.download(symbol, period=p, interval="1d")
    if df.empty:
        return None
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Calcul ATR
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = true_range.rolling(window=atr_period).mean()
    
    # SMA 20 de l'ATR
    df['ATR_SMA20'] = df['ATR'].rolling(window=20).mean()
    return df

# --- AFFICHAGE ---
if ticker_final:
    df = load_and_calc(ticker_final, periode)

    if df is not None:
        last_price = df['Close'].iloc[-1]
        last_atr = df['ATR'].iloc[-1]
        prev_atr_sma = df['ATR_SMA20'].iloc[-1]
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Prix {ticker_final}", f"{last_price:.2f} €" if ".PA" in ticker_final else f"{last_price:.2f} $")
        c2.metric("Indice ATR", f"{last_atr:.2f}")
        c3.metric("État Volatilité", "ÉLEVÉE" if last_atr > prev_atr_sma else "CALME", 
                  delta=f"{last_atr - prev_atr_sma:.2f}", delta_color="inverse")

        # --- GRAPHIQUE ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # Prix
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Prix'
        ), row=1, col=1)

        # ATR
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ATR'], 
            line=dict(color='#FF9900', width=2), name='ATR',
            fill='tozeroy', fillcolor='rgba(255, 153, 0, 0.1)'
        ), row=2, col=1)

        # SMA 20 (Cyan)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['ATR_SMA20'], 
            line=dict(color='#00CCFF', width=2), name='Moyenne Mobile (ATR)'
        ), row=2, col=1)

        fig.update_layout(template="plotly_dark", height=750, xaxis_rangeslider_visible=False,
                          margin=dict(t=30, b=10))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Données indisponibles pour ce symbole.")

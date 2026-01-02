import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Terminal Analyse Technique Pro", layout="wide")

# --- DICTIONNAIRE DU CAC 40 ---
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

st.title("🇫🇷 Terminal d'Analyse Technique Multi-Indicateurs")

# --- BARRE LATÉRALE ---
st.sidebar.header("🔍 Configuration")
mode = st.sidebar.radio("Mode de sélection :", ["Liste CAC 40", "Saisie libre"])

if mode == "Liste CAC 40":
    nom_action = st.sidebar.selectbox("Entreprise :", list(CAC40_DICT.keys()))
    ticker_final = CAC40_DICT[nom_action]
else:
    ticker_final = st.sidebar.text_input("Symbole (ex: AAPL, BTC-USD) :", value="GOOGL")

periode = st.sidebar.selectbox("Période", ["6mo", "1y", "2y", "5y", "max"], index=0)

st.sidebar.markdown("---")
st.sidebar.header("📊 Indicateurs à afficher")
show_volume = st.sidebar.checkbox("Volumes", value=True)
show_atr = st.sidebar.checkbox("ATR (Volatilité)", value=True)
show_rsi = st.sidebar.checkbox("RSI (Surachat/Survente)", value=False)
show_macd = st.sidebar.checkbox("MACD (Tendance)", value=False)

# --- CALCULS TECHNIQUES ---
@st.cache_data
def get_full_analysis(symbol, p):
    df = yf.download(symbol, period=p, interval="1d")
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # ATR & Sa MM20
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    df['ATR_SMA20'] = df['ATR'].rolling(window=20).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']
    
    return df

# --- AFFICHAGE ---
if ticker_final:
    df = get_full_analysis(ticker_final, periode)

    if df is not None:
        # Calcul dynamique du nombre de lignes du graphique
        rows = 1 + show_volume + show_atr + show_rsi + show_macd
        row_heights = [0.5] + [0.15] * (rows - 1)
        
        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, row_heights=row_heights)

        current_row = 1
        # 1. Bougies (Toujours affiché)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                   low=df['Low'], close=df['Close'], name='Prix'), row=1, col=1)
        
        # 2. Volumes
        if show_volume:
            current_row += 1
            colors = ['red' if row['Open'] > row['Close'] else 'green' for _, row in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors, opacity=0.5), row=current_row, col=1)
            fig.update_yaxes(title_text="Volume", row=current_row, col=1)

        # 3. ATR
        if show_atr:
            current_row += 1
            fig.add_trace(go.Scatter(x=df.index, y=df['ATR'], line=dict(color='#FF9900', width=2), name='ATR'), row=current_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['ATR_SMA20'], line=dict(color='#00CCFF', width=1.5), name='ATR SMA20'), row=current_row, col=1)
            fig.update_yaxes(title_text="ATR", row=current_row, col=1)

        # 4. RSI
        if show_rsi:
            current_row += 1
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#FF00FF', width=2), name='RSI'), row=current_row, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=current_row, col=1)
            fig.update_yaxes(title_text="RSI", row=current_row, col=1)

        # 5. MACD
        if show_macd:
            current_row += 1
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='white', width=1.5), name='MACD'), row=current_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='yellow', width=1.5), name='Signal'), row=current_row, col=1)
            fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Hist', marker_color='gray'), row=current_row, col=1)
            fig.update_yaxes(title_text="MACD", row=current_row, col=1)

        fig.update_layout(template="plotly_dark", height=400 + (150 * (rows-1)), xaxis_rangeslider_visible=False,
                          margin=dict(t=30, b=10), showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Données indisponibles.")

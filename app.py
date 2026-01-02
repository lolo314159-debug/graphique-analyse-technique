import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Configuration de la page
st.set_page_config(page_title="Analyseur de Marché Pro", layout="wide")

# Style CSS pour améliorer l'apparence
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Analyseur de Bougies Japonaises")

# 2. Barre latérale de configuration
st.sidebar.header("🔍 Paramètres de recherche")
ticker_input = st.sidebar.text_input("Symbole (Ticker)", value="GOOGL")
periode = st.sidebar.selectbox("Période", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=2)
intervalle = st.sidebar.selectbox("Intervalle", ["1d", "1wk", "1mo"], index=0)

# Aide pour l'utilisateur
st.sidebar.info("""
**Exemples :**
- Google : `GOOGL`
- CAC 40 : `^FCHI`
- Bitcoin : `BTC-USD`
- Orange : `ORAN.PA`
""")

# 3. Fonction de récupération des données
@st.cache_data
def get_data(symbol, p, i):
    try:
        data = yf.download(symbol, period=p, interval=i)
        return data
    except Exception as e:
        return None

# 4. Exécution et Affichage
if ticker_input:
    df = get_data(ticker_input, periode, intervalle)

    if df is not None and not df.empty:
        # Nettoyage des données pour Plotly (gestion des Index Multi-niveaux de yfinance)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Indicateurs en colonnes
        col1, col2, col3 = st.columns(3)
        last_close = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        change = ((last_close - prev_close) / prev_close) * 100

        col1.metric("Dernier Prix", f"{last_close:.2f} $")
        col2.metric("Variation (24h)", f"{change:.2f} %")
        col3.metric("Volume (Session)", f"{df['Volume'].iloc[-1]:,.0f}")

        # 5. Construction du graphique Plotly
        fig = go.Figure()

        # Bougies
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Prix'
        ))

        # Design du graphique
        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=True,
            height=700,
            title=f"Graphique Historique : {ticker_input}",
            yaxis_title="Prix en USD",
            xaxis_title="Temps"
        )

        # Affichage du graphique
        st.plotly_chart(fig, use_container_width=True)
        
        # Données brutes
        with st.expander("Consulter les données brutes"):
            st.dataframe(df.sort_index(ascending=False))
            
    else:
        st.error(f"❌ Impossible de trouver des données pour '{ticker_input}'. Vérifiez le symbole sur Google Finance.")

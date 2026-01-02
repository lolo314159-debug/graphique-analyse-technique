import yfinance as yf
import plotly.graph_objects as go

# Récupération immédiate
df = yf.download("GOOGL", period="6mo", interval="1d")

# Graphique interactif
fig = go.Figure(data=[go.Candlestick(
    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
)])
fig.update_layout(template="plotly_dark", title="Google Finance Data")
# Ajout des volumes en dessous des bougies
fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='gray', opacity=0.3), secondary_y=True)
fig.show()

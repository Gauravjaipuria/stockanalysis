import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ollama
import tempfile
import base64
import os
import pandas_market_calendars as mcal
from nselib import capital_market

# 🏗️ Set up Streamlit app
st.set_page_config(layout="wide")
st.title("📈 AI-Powered Technical Stock Analysis Dashboard")
st.sidebar.header("⚙️ Configuration")

# 📅 User Input for Stock Ticker & Date Range
ticker = st.sidebar.text_input("Enter NSE Stock Ticker (e.g., VEDL):", "VEDL").upper()
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-12-31"))

# 🔄 Convert date format to match NSE API requirements
start_date_str = start_date.strftime("%d-%m-%Y")  # Format: "DD-MM-YYYY"
end_date_str = end_date.strftime("%d-%m-%Y")      # Format: "DD-MM-YYYY"

# 🖋️ Custom CSS to style the UI
st.markdown("""
    <style>
        .sidebar .sidebar-content {
            background-color: #f0f4f8;
        }
        .css-1v3fvcr {  # Title custom styling
            color: #2E3B4E;
            font-weight: bold;
        }
        .stButton button {
            background-color: #00bfae;
            color: white;
            font-weight: bold;
            padding: 12px 20px;
            border-radius: 10px;
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stButton button:hover {
            background-color: #008f7e;
        }
        .stMultiSelect {
            background-color: #f5f5f5;
        }
        .stAlert {
            background-color: #ffb6b6;
        }
        .stSuccess {
            background-color: #d1f5d3;
        }
    </style>
""", unsafe_allow_html=True)

# 📥 Fetch stock data when button is clicked
if st.sidebar.button("Fetch Data"):
    try:
        st.info("Fetching stock data... Please wait.")
        stock_data = capital_market.price_volume_and_deliverable_position_data(
            symbol=ticker, from_date=start_date_str, to_date=end_date_str
        )

        if stock_data.empty:
            st.error("⚠️ No data found. Please check the stock symbol and date range.")
        else:
            st.session_state["stock_data"] = stock_data
            st.success("✅ Stock data loaded successfully!")

    except Exception as e:
        st.error(f"❌ Error fetching NSE data: {e}")

# ✅ Check if stock data is available
if "stock_data" in st.session_state and not st.session_state["stock_data"].empty:
    data = st.session_state["stock_data"]

    # 🎨 Plot candlestick chart
    fig = go.Figure(data=[
        go.Candlestick(
            x=pd.to_datetime(data['Date']),
            open=data['OpenPrice'],
            high=data['HighPrice'],
            low=data['LowPrice'],
            close=data['ClosePrice'],
            name="Candlestick"
        )
    ])

    # 📊 Sidebar: Select Technical Indicators
    st.sidebar.subheader("📊 Technical Indicators")
    indicators = st.sidebar.multiselect(
        "Select Indicators:",
        ["20-Day SMA", "20-Day EMA", "20-Day Bollinger Bands", "VWAP", "50-Day DMA", "200-Day DMA"],
        default=["20-Day SMA"]  # Default indicator selected
    )

    # 🛠️ Helper Function: Add Indicators to the Chart
    def add_indicator(indicator):
        if indicator == "20-Day SMA":
            sma = data['ClosePrice'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(x=pd.to_datetime(data['Date']), y=sma, mode='lines', name='SMA (20)', line=dict(color='blue')))
        elif indicator == "20-Day EMA":
            ema = data['ClosePrice'].ewm(span=20).mean()
            fig.add_trace(go.Scatter(x=pd.to_datetime(data['Date']), y=ema, mode='lines', name='EMA (20)', line=dict(color='orange')))
        elif indicator == "20-Day Bollinger Bands":
            sma = data['ClosePrice'].rolling(window=20).mean()
            std = data['ClosePrice'].rolling(window=20).std()
            bb_upper = sma + 2 * std
            bb_lower = sma - 2 * std
            fig.add_trace(go.Scatter(x=pd.to_datetime(data['Date']), y=bb_upper, mode='lines', name='BB Upper', line=dict(color='green')))
            fig.add_trace(go.Scatter(x=pd.to_datetime(data['Date']), y=bb_lower, mode='lines', name='BB Lower', line=dict(color='red')))
        elif indicator == "VWAP":
            data['VWAP'] = (data['ClosePrice'] * data['TotalTradedQuantity']).cumsum() / data['TotalTradedQuantity'].cumsum()
            fig.add_trace(go.Scatter(x=pd.to_datetime(data['Date']), y=data['VWAP'], mode='lines', name='VWAP', line=dict(color='purple')))
        elif indicator == "50-Day DMA":
            dma_50 = data['ClosePrice'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(x=pd.to_datetime(data['Date']), y=dma_50, mode='lines', name='DMA (50)', line=dict(color='brown')))
        elif indicator == "200-Day DMA":
            dma_200 = data['ClosePrice'].rolling(window=200).mean()
            fig.add_trace(go.Scatter(x=pd.to_datetime(data['Date']), y=dma_200, mode='lines', name='DMA (200)', line=dict(color='cyan')))

    # ➕ Add Selected Indicators
    for indicator in indicators:
        add_indicator(indicator)

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark",  # Dark theme for the plot
        title="Stock Candlestick and Technical Indicators",
        title_x=0.5,
        title_font=dict(size=20),
        plot_bgcolor="#1e1e1e"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 🤖 AI-Powered Chart Analysis
    st.subheader("🤖 AI-Powered Technical Analysis")
    if st.button("Run AI Analysis"):
        with st.spinner("🔍 Analyzing the chart, please wait..."):
            # 📸 Save chart as an image
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                fig.write_image(tmpfile.name)
                tmpfile_path = tmpfile.name

            # 🔄 Convert Image to Base64
            with open(tmpfile_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # 📩 AI Model Request
            messages = [{
                'role': 'user',
                'content': """You are a Stock Trader specializing in Technical Analysis at a top financial institution.
                            Analyze the stock chart's technical indicators and provide a buy/hold/sell recommendation.
                            Base your recommendation only on the candlestick chart and the displayed technical indicators.
                            First, provide the recommendation, then provide your detailed reasoning.
                """,
                'images': [image_data]
            }]
            response = ollama.chat(model='llama3.2-vision', messages=messages)

            # 📌 Display AI Analysis Result
            st.write("**📌 AI Analysis Results:**")
            st.write(response["message"]["content"])

            # 🧹 Clean up temporary file
            os.remove(tmpfile_path)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import openai
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

            # 📩 AI Model Request using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": "You are a financial analyst specializing in technical stock analysis."},
                    {"role": "user", "content": "Analyze the stock chart and technical indicators. Provide a buy/hold/sell recommendation with reasoning."}
                ],
                max_tokens=500
            )

            # 📌 Display AI Analysis Result
            st.write("**📌 AI Analysis Results:**")
            st.write(response["choices"][0]["message"]["content"])

            # 🧹 Clean up temporary file
            os.remove(tmpfile_path)

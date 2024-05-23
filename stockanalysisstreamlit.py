import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import requests

# Helper function to get financial ratios
def get_financial_ratios(ticker):
    API_KEY = '90c1c9da624fcab78500a10f9634b0cf'
    BASE_URL = 'https://financialmodelingprep.com/api/v3'

    def get_financial_statements(statement_type):
        endpoint = f'{BASE_URL}/{statement_type}/{ticker}'
        params = {'limit': 120, 'apikey': API_KEY}
        response = requests.get(endpoint, params=params)
        return pd.DataFrame(response.json())

    statement_types = ['income-statement', 'balance-sheet-statement', 'cash-flow-statement']
    financial_data = {statement_type: get_financial_statements(statement_type) for statement_type in statement_types}
    
    income_statement_df = financial_data['income-statement']
    balance_sheet_df = financial_data['balance-sheet-statement']
    cash_flow_df = financial_data['cash-flow-statement']

    # Replace "None" with "NaN" in the DataFrames
    income_statement_df = income_statement_df.replace("None", "NaN")
    balance_sheet_df = balance_sheet_df.replace("None", "NaN")
    cash_flow_df = cash_flow_df.replace("None", "NaN")

    # Calculate ratios
    ratios = {}
    try:
        ratios['Current Ratio'] = balance_sheet_df['totalCurrentAssets'][0] / balance_sheet_df['totalCurrentLiabilities'][0]
    except:
        ratios['Current Ratio'] = "N/A"
    
    try:
        ratios['Quick Ratio'] = (balance_sheet_df['totalCurrentAssets'][0] - balance_sheet_df['inventory'][0]) / balance_sheet_df['totalCurrentLiabilities'][0]
    except:
        ratios['Quick Ratio'] = "N/A"

    try:
        ratios['Return on Equity (ROE)'] = income_statement_df['netIncome'][0] / balance_sheet_df['totalStockholdersEquity'][0]
    except:
        ratios['Return on Equity (ROE)'] = "N/A"

    try:
        ratios['Return on Assets (ROA)'] = income_statement_df['netIncome'][0] / balance_sheet_df['totalAssets'][0]
    except:
        ratios['Return on Assets (ROA)'] = "N/A"

    try:
        ratios['Gross Profit Margin'] = income_statement_df['grossProfit'][0] / income_statement_df['revenue'][0]
    except:
        ratios['Gross Profit Margin'] = "N/A"

    try:
        ratios['Operating Profit Margin'] = income_statement_df['operatingIncome'][0] / income_statement_df['revenue'][0]
    except:
        ratios['Operating Profit Margin'] = "N/A"

    try:
        ratios['Net Profit Margin'] = income_statement_df['netIncome'][0] / income_statement_df['revenue'][0]
    except:
        ratios['Net Profit Margin'] = "N/A"

    try:
        ratios['Earnings Per Share (EPS)'] = income_statement_df['eps'][0]
    except:
        ratios['Earnings Per Share (EPS)'] = "N/A"

    try:
        latest_price = yf.Ticker(ticker).history(period="1d")['Close'][0]
        ratios['Price to Earnings (P/E) Ratio'] = latest_price / ratios['Earnings Per Share (EPS)']
    except:
        ratios['Price to Earnings (P/E) Ratio'] = "N/A"

    return pd.DataFrame(ratios, index=[0]).transpose().reset_index().rename(columns={"index": "Ratio", 0: "Value"})

# Streamlit app
st.title("Stock Analysis Dashboard")

ticker_input = st.text_input("Enter a stock ticker:", value="AAPL")
submit_button = st.button("Submit")

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if submit_button or st.session_state.submitted:
    st.session_state.submitted = True
    ticker = ticker_input.upper()

    # Technical Analysis
    st.subheader("Technical Analysis")
    timeframe = st.selectbox("Select a time period:", ['1 minute', '30 minutes', '1 hour', '3 hour', '1 day', '1 month'], index=4)

    if 'moving_averages' not in st.session_state:
        st.session_state.moving_averages = [10, 25, 50]

    if 'show_bollinger_bands' not in st.session_state:
        st.session_state.show_bollinger_bands = False

    if 'std_dev' not in st.session_state:
        st.session_state.std_dev = 2.0

    if 'show_rsi' not in st.session_state:
        st.session_state.show_rsi = False

    if 'show_macd' not in st.session_state:
        st.session_state.show_macd = False

    moving_averages = st.multiselect("Select Moving Averages:", [10, 25, 50], default=st.session_state.moving_averages)
    show_bollinger_bands = st.checkbox("Show Bollinger Bands", value=st.session_state.show_bollinger_bands)
    std_dev = st.slider("Standard Deviation", 1.0, 5.0, st.session_state.std_dev)
    show_rsi = st.checkbox("Show RSI", value=st.session_state.show_rsi)
    show_macd = st.checkbox("Show MACD", value=st.session_state.show_macd)

    st.session_state.moving_averages = moving_averages
    st.session_state.show_bollinger_bands = show_bollinger_bands
    st.session_state.std_dev = std_dev
    st.session_state.show_rsi = show_rsi
    st.session_state.show_macd = show_macd

    time_frame_days = {
        '1 minute': 1,
        '30 minutes': 10,
        '1 day': 350,
        '1 hour': 20,
        '3 hour': 20,
        '1 month': 30 * 60,
    }

    period = f'{time_frame_days[timeframe]}d'
    interval = {
        '1 minute': '1m',
        '30 minutes': '30m',
        '1 hour': '1h',
        '3 hour': '3h',
        '1 day': '1d',
        '1 month': '1mo'
    }[timeframe]

    stock_data = yf.download(ticker, period=period, interval=interval)

    fig = make_subplots(rows=4, cols=1, vertical_spacing=0.02, row_heights=[0.5, 0.3, 0.1, 0.1])
    fig.add_trace(go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Candlestick'), row=1, col=1)

    for ma in moving_averages:
        col_name = f"SMA{ma}"
        stock_data[col_name] = stock_data['Close'].rolling(ma).mean()
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[col_name], name=col_name, line=dict(width=1)), row=1, col=1)

    if show_bollinger_bands:
        stock_data['SMA10'] = stock_data['Close'].rolling(10).mean()
        stock_data['STD'] = stock_data['Close'].rolling(10).std() * std_dev
        stock_data['Bollinger High'] = stock_data['SMA10'] + stock_data['STD']
        stock_data['Bollinger Low'] = stock_data['SMA10'] - stock_data['STD']
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger High'], name='Bollinger High', line=dict(width=1, dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Bollinger Low'], name='Bollinger Low', line=dict(width=1, dash='dash')), row=1, col=1)

    if show_rsi:
        delta = stock_data['Adj Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        stock_data['RSI'] = 100 - (100 / (1 + rs))
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], name='RSI'), row=3, col=1)

    if show_macd:
        exp1 = stock_data['Adj Close'].ewm(span=12, adjust=False).mean()
        exp2 = stock_data['Adj Close'].ewm(span=26, adjust=False).mean()
        stock_data['MACD'] = exp1 - exp2
        stock_data['signal'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
        stock_data['MACD_hist'] = stock_data['MACD'] - stock_data['signal']
        fig.add_trace(go.Scatter(y=stock_data['MACD'], name='MACD'), row=4, col=1)
        fig.add_trace(go.Scatter(y=stock_data['signal'], name='Signal'), row=4, col=1)
        fig.add_trace(go.Bar(y=stock_data['MACD_hist'], marker=dict(color=['red' if x < 0 else 'green' for x in stock_data['MACD_hist']]), name='MACD Histogram'), row=4, col=1)

    fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['Volume'], name='Volume'), row=2, col=1)
    fig.update_layout(title=f'{ticker} Stock Price Chart ({timeframe})', height=1000)

    st.plotly_chart(fig)

    # Fundamentals
    st.subheader("Fundamentals")
    fundamental_data = get_financial_ratios(ticker)
    st.table(fundamental_data)

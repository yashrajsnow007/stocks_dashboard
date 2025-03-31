import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np

st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide"
)

@st.cache_data(ttl=3600)
def fetch_single_stock_data(ticker, start_date, end_date):
    try:
        time.sleep(0.5)
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)
        return data
    except Exception as e:
        st.error(f"Error fetching {ticker}: {e}")
        return None

def format_number(num):
    if num is None or num == 'N/A' or pd.isna(num):
        return 'N/A'
    return "{:,}".format(float(num))

def main():
    st.title("📈 Stock Market Dashboard")
    
    st.sidebar.header("Dashboard Settings")
    
    default_stocks = ["AAPL", "MSFT", "GOOGL"]
    
    selected_stocks = st.sidebar.multiselect(
        "Select stocks to visualize",
        options=["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT", "DIS", "NFLX"],
        default=default_stocks
    )
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date",
            datetime.now() - timedelta(days=365)
        )
    with col2:
        end_date = st.date_input(
            "End date",
            datetime.now()
        )
    
    chart_type = st.sidebar.selectbox(
        "Select chart type",
        options=["Line Chart", "Candlestick", "Area Chart"]
    )
    
    price_type = st.sidebar.selectbox(
        "Select price type",
        options=["Close", "Open", "High", "Low", "Adj Close", "Volume"]
    )
    
    if selected_stocks:
        all_stock_data = {}
        plot_data = pd.DataFrame()
        
        progress_bar = st.progress(0)
        
        for i, stock in enumerate(selected_stocks):
            with st.spinner(f'Fetching data for {stock}...'):
                stock_data = fetch_single_stock_data(stock, start_date, end_date)
                if stock_data is not None and not stock_data.empty:
                    all_stock_data[stock] = stock_data
                    plot_data[stock] = stock_data[price_type]
                progress_bar.progress((i + 1) / len(selected_stocks))
        
        progress_bar.empty()
        
        if plot_data.empty:
            st.error("Could not retrieve data for any of the selected stocks.")
        else:
            st.subheader("Current Stock Prices")
            
            cols = st.columns(len(selected_stocks))
            
            for i, stock in enumerate(selected_stocks):
                if stock in plot_data.columns:
                    try:
                        current_price = plot_data[stock].iloc[-1]
                        previous_price = plot_data[stock].iloc[-2]
                        
                        pct_change = ((current_price - previous_price) / previous_price) * 100
                        
                        delta_color = "normal"
                        if pct_change > 0:
                            delta_color = "off"
                        elif pct_change < 0:
                            delta_color = "inverse"
                            
                        cols[i].metric(
                            f"{stock}",
                            f"${current_price:.2f}",
                            f"{pct_change:.2f}%",
                            delta_color=delta_color
                        )
                    except Exception as e:
                        cols[i].error(f"Error: {e}")
                else:
                    cols[i].error(f"No data for {stock}")
            
            st.subheader(f"Stock Price Comparison ({price_type})")
            
            try:
                if chart_type == "Line Chart":
                    fig = px.line(
                        plot_data, 
                        title=f"{price_type} Prices"
                    )
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title=f"Price ($)" if price_type != "Volume" else "Volume",
                        legend_title="Stocks"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Area Chart":
                    fig = px.area(
                        plot_data, 
                        title=f"{price_type} Prices"
                    )
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title=f"Price ($)" if price_type != "Volume" else "Volume",
                        legend_title="Stocks"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Candlestick":
                    available_stocks = [s for s in selected_stocks if s in all_stock_data]
                    if available_stocks:
                        selected_stock = st.selectbox("Select a stock for candlestick view", available_stocks)
                        
                        fig = go.Figure()
                        stock_data = all_stock_data[selected_stock]
                        
                        fig.add_trace(go.Candlestick(
                            x=stock_data.index,
                            open=stock_data['Open'],
                            high=stock_data['High'],
                            low=stock_data['Low'],
                            close=stock_data['Close'],
                            name=selected_stock
                        ))
                        
                        fig.update_layout(
                            title=f"{selected_stock} Candlestick Chart",
                            xaxis_title="Date",
                            yaxis_title="Price ($)",
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("No stock data available for candlestick chart")
                
                st.subheader("Historical Performance")
                
                valid_stocks = plot_data.dropna(axis=1, how='all').columns
                if len(valid_stocks) > 0:
                    start_prices = plot_data[valid_stocks].iloc[0]
                    end_prices = plot_data[valid_stocks].iloc[-1]
                    performance = ((end_prices - start_prices) / start_prices) * 100
                    
                    performance_df = pd.DataFrame({
                        'Stock': performance.index,
                        'Start Price': start_prices.values,
                        'End Price': end_prices.values,
                        'Change (%)': performance.values
                    })
                    
                    performance_df['Start Price'] = performance_df['Start Price'].apply(lambda x: f"${x:.2f}")
                    performance_df['End Price'] = performance_df['End Price'].apply(lambda x: f"${x:.2f}")
                    performance_df['Change (%)'] = performance_df['Change (%)'].apply(lambda x: f"{x:.2f}%")
                    
                    st.dataframe(performance_df, use_container_width=True)
                
                st.subheader("Detailed Stock Information")
                
                available_stocks = [s for s in selected_stocks if s in all_stock_data]
                if available_stocks:
                    selected_detail_stock = st.selectbox(
                        "Select a stock to view detailed information",
                        options=available_stocks
                    )
                    
                    with st.spinner(f"Fetching details for {selected_detail_stock}..."):
                        try:
                            stock_info = yf.Ticker(selected_detail_stock).info
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.markdown(f"**Company Name**: {stock_info.get('longName', 'N/A')}")
                                st.markdown(f"**Sector**: {stock_info.get('sector', 'N/A')}")
                                st.markdown(f"**Industry**: {stock_info.get('industry', 'N/A')}")
                            
                            with col2:
                                st.markdown(f"**Market Cap**: ${format_number(stock_info.get('marketCap', 'N/A'))}")
                                
                                pe_ratio = stock_info.get('trailingPE')
                                if pe_ratio is not None and not pd.isna(pe_ratio):
                                    pe_display = f"{pe_ratio:.2f}"
                                else:
                                    pe_display = "N/A"
                                st.markdown(f"**P/E Ratio**: {pe_display}")
                                
                                dividend_yield = stock_info.get('dividendYield')
                                if dividend_yield is not None and not pd.isna(dividend_yield):
                                    dividend_display = f"{dividend_yield * 100:.2f}%"
                                else:
                                    dividend_display = "N/A"
                                st.markdown(f"**Dividend Yield**: {dividend_display}")
                            
                            with col3:
                                st.markdown(f"**52 Week High**: ${stock_info.get('fiftyTwoWeekHigh', 'N/A')}")
                                st.markdown(f"**52 Week Low**: ${stock_info.get('fiftyTwoWeekLow', 'N/A')}")
                                st.markdown(f"**Avg Volume**: {format_number(stock_info.get('averageVolume', 'N/A'))}")
                        
                            st.subheader("Company Description")
                            st.write(stock_info.get('longBusinessSummary', 'No description available.'))
                        except Exception as e:
                            st.error(f"Error fetching details for {selected_detail_stock}: {e}")
                else:
                    st.error("No stock data available for detailed information")
                
            except Exception as e:
                st.error(f"Error creating visualizations: {str(e)}")
    else:
        st.info("Please select at least one stock from the sidebar to visualize data.")

if __name__ == "__main__":
    main()

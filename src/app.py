# -*- coding: utf-8 -*-
from utils.handler_funcs import handle_data, handle_news
from utils.plot_funcs import get_palette, format_plot
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ===============================================================
# Candlestick plot for selected ticker, period and interval
# ===============================================================

def plot_candlestick(fig: go.Figure, ticker_code: str, history: pd.DataFrame, horizon: str, earnings_dates: list=[],
                     name: str="", currency: str="Currency Undefined", period: str="3mo", interval: str="1d") -> None:
    """
    Applies candlestick price data and trade volume data to a Plotly figure.
    Called by handle_plots()

    Parameters
    ----------
    See run_once() and handle_data() functions for parameter descriptions

    Complete example : plot_candlestick("MSFT", <pd.DataFrame>, "YYYY-MM-DD", ["YYYY-DD-MM", "YYYY-DD-MM"],
    "Microsoft Corporation", "USD", "1d")
    """
    # Get custom palette
    palette = get_palette()
    # Add OHLC data to first subplot (Prices)
    fig.update_traces(x=history.index, open=history["Open"], high=history["High"],
                      low=history["Low"], close=history["Close"], hoverinfo="x+y",
                      selector={"name": "Prices"})
    # Add trade volume data to second subplot (Volume)
    fig.update_traces(x=history.index, y=history["Volume"], mode="lines", line_color=palette["sky"],
                      hovertemplate="%{x|%b %d, %Y}<br>%{y:,.0f}<extra></extra>",  # <extra> code removes trace name default
                      selector={"name": "Volume"})

    start_date = history.index.min()
    end_date = history.index.max()
    # Get date range information for plot title
    start_date_string = start_date.strftime("%d %b. %Y")
    end_date_string = end_date.strftime("%d %b. %Y")  # here b/c end_date reassigned to horizon below
    date_range_label = f"{start_date_string} - {end_date_string}"

    # Extend x-axis to horizon
    if horizon != "":
        fig.update_layout(xaxis_range=[history.index.min(), horizon])
        end_date = horizon

    # Calculate mean close price and mean trade volume
    mean_price = history["Close"].mean()
    mean_volume = history["Volume"].mean()
    # Add horizontal dashed lines for mean values - declare only one on legend
    fig.add_shape(type="line", x0=start_date, x1=end_date, y0=mean_price, y1=mean_price,
                  line=dict(color=palette["stone"], width=2, dash="dash"), name="Mean", showlegend=True, row=1, col=1)
    fig.add_shape(type="line", x0=start_date, x1=end_date, y0=mean_volume, y1=mean_volume,
                  line=dict(color=palette["stone"], width=2, dash="dash"), name="Mean", row=2, col=1)

    # Get period to determine x-axis date display
    periods_dict = {"3mo": 7, "6mo": 7, "1y": 14}
    period_label = periods_dict[period.lower()]

    # Hide dates on Prices (top) subplot x-axis
    fig.update_xaxes(dtick=86400000*period_label, showticklabels=False, row=1, col=1)
    fig.update_yaxes(title_text=f"Price ({currency})", row=1, col=1)
    # Show dates on Volume (bottom) subplot x-axis
    fig.update_xaxes(range=[history.index.min(), horizon], tickfont=dict(color=palette["stone"]), 
                     gridcolor=palette["grey"], linecolor=palette["stone"],
                     tickangle=45, dtick=86400000*period_label, tickformat="%Y-%m-%d", row=2, col=1)
    fig.update_yaxes(title_text="Volume", title=dict(font=dict(color=palette["light"])), tickfont=dict(color=palette["stone"]),
                     gridcolor=palette["grey"], linecolor=palette["stone"], row=2, col=1)

    # Get interval label for figure title
    intervals_dict = {"1d": "Daily", "1wk": "Weekly"}
    interval_label = intervals_dict[interval.lower()]

    # Combine name, ticker, and interval for figure title
    ticker_label = f"{name} ({ticker_code.upper()}) {interval_label}"
    # Update layout
    fig.update_layout(title_text=f"{ticker_label} Market Data <br>{date_range_label}",
                      xaxis_rangeslider_visible=False, width=1080, height=560)

    # Add earnings dates as vertical lines
    if earnings_dates != []:
        reverse_earnings_dates = earnings_dates[::-1] # Reverse list so legend is chronological
        for date in reverse_earnings_dates:
            fig.add_shape(
                type="line", x0=date, x1=date, y0=0, y1=1, xref="x", yref="paper",
                line=dict(color = palette["pink"], width=1, dash="dash"),
                name=f"ED '{date[2:]}", showlegend=True
                )


# ===============================================================
# Sentiment data plot trace
# ===============================================================

def plot_sentiment(sent_df: pd.DataFrame, fig: go.Figure) -> None:
    """
    Applies market sentiment data to a Plotly figure.
    Called by handle_plots()

    Parameters
    ----------
    See run_once() and handle_data() functions for parameter descriptions

    Complete example : plot_candlestick("MSFT", <pd.DataFrame>, "YYYY-MM-DD", ["YYYY-DD-MM", "YYYY-DD-MM"],
    "Microsoft Corporation", "USD", "1d")
    """
    # Get custom palette
    palette = get_palette()
    if not sent_df["rolling_avg"].isna().all():
    
        max_value = np.nanmax(sent_df["rolling_avg"])
        min_value = np.nanmin(sent_df["rolling_avg"])
        # Calculate upper and lower bounds
        upper_bound = min([1.0, max_value + 0.2])
        lower_bound = max([-1.0, min_value - 0.2])
        
    else:
        upper_bound = 1.0
        lower_bound = -1.0
        
    fig.update_traces(
        x=sent_df.index, y=sent_df["rolling_avg"], mode="lines+markers", line_color=palette["yellow"], 
        marker=dict(symbol="arrow", size=10, angleref="previous"),
        hovertemplate="%{x|%b %d, %Y}<br>sentiment (1wk avg): %{y:,.2f}<extra></extra>",  # <extra> code removes trace name default
        showlegend=True, selector={"name": "Sentiment"}
    )
    fig.update_yaxes(
        title_text="", tickfont=dict(color=palette["stone"]), 
        tickmode="array", 
        range=[lower_bound, upper_bound], 
        zeroline=False, showgrid=False, row=1, col=1, secondary_y=True
    )


# ===============================================================
# Handler functions
# ===============================================================

def handle_plots(sent_df: pd.DataFrame | None, raw_tick: str, tick_history: pd.DataFrame, tick_horizon: str,
                 tick_earnings_dates: list[str], tick_name: str, tick_currency: str="Currency Undefined",
                 raw_period: str="3mo", raw_interval: str="1d") -> None:
    """
    Calls plot_candlestick() to plot price and volume data
    Calls plot_sentiment() to add market sentiment data to candlestick plot
    Called by run_once()

    Parameters
    ----------
    See run_once(), handle_data(), handle_news() docstrings for parameter descriptions
    """
    # Get custom palette
    palette = get_palette()
    # Create subplots with two rows and one column
    fig = make_subplots(rows=2, cols=1, vertical_spacing=0.035, row_heights=[0.6, 0.4], specs=[[{"secondary_y": True}], [{}]])
    # Add empty trace for candlestick data on top row
    fig.add_trace(go.Candlestick(x=[], open=[], high=[], low=[], close=[], name="Prices"), row=1, col=1)
    # Add placeholder for sentiment data on same plot as candlestick, but using right-hand y-axis
    fig.add_trace(go.Scatter(x=[], y=[], name="Sentiment", line_color=palette["dark"], showlegend=False), row=1, col=1, secondary_y=True)
    # Add empty trace for volume data on bottom row
    fig.add_trace(go.Scatter(x=[], y=[], name="Volume"), row=2, col=1)

    # Add candlestick and volume plots
    plot_candlestick(fig, raw_tick, tick_history, tick_horizon, tick_earnings_dates,
                         tick_name, tick_currency, raw_period, raw_interval)
    # Add market sentiment plot
    if isinstance(sent_df, pd.DataFrame):
        plot_sentiment(sent_df, fig)

    # Show plot
    format_plot(fig)
    # fig.show()

    # STREAMLIT CHANGE
    st.plotly_chart(fig, use_container_width=True)


def run_once(raw_ticker: str, raw_period: str="3mo", raw_interval: str="1d", show_plots=False) -> None:
    """
    Master function:
        Calls handle_data() to obtain and process data
        Calls handle_news() to obtain and process news data
        Calls handle_plots() to generate plots

    Parameters
    ----------
    raw_ticker : str
        The official abbreviation of the stock
        Valid values : Any official stock ticker symbol that exists on Yahoo! Finance
        eg. "msft"

    raw_period : str
        The time period length, ending on current date minus 2 or 3 days
        Valid values : "1mo", "3mo", "6mo", "1y"

    raw_interval : str
        The interval frequency
        Valid values : "1d", "1wk"

    show_plots : bool
        Boolean flag to determine whether to call plot functions (default = False)
    """
    try:
        # Retain t_obj (Ticker object) for further use
        t_obj, t_hist, t_horizon, t_earn_dates, t_name, t_curr =  handle_data(raw_ticker, raw_period, raw_interval)

        try:
            # Get news headline sentiment data for ticker
            sentiment_df = handle_news(t_name)
        except Exception as e:
            print(f"Error getting market sentiment data: {e}")
            sentiment_df = None

        if show_plots == True:
            try:
                # Send raw_ticker to pass the string for plotting, not the Ticker object
                handle_plots(sentiment_df, raw_ticker, t_hist, t_horizon, t_earn_dates, t_name, t_curr, raw_period, raw_interval)
            except Exception as e:
                print(f"Error during plot handling: {e}")

    except Exception as e:
        print(f"Error during data handling: {e}")

# ===============================================================
# Streamlit
# ===============================================================
        
# Specify wide layout
st.set_page_config(layout = 'wide')       

col11, col12 = st.columns([1, 3])
with col12:
    st.title("Stock Price and Market Sentiment Analysis")

col13, col14 = st.columns([1, 6])
with col14:
    st.subheader(
        "Explore historical price data and general stock sentiment derived from news headlines in the last 30 days."
        )

# Create columns for input and dropdowns
col_inp_1, col_inp_2, col_inp_3, col_inp_4, col_inp_5 = st.columns(5)

with col_inp_2:
    ticker_input = st.text_input(label = "Ticker:", value = "NVDA", max_chars = None)

with col_inp_3:
    period_dd = st.selectbox(label = "Period:", options = ["Last 3 months", "Last 6 months", "Last 12 months"], index = 2)

with col_inp_4: 
    interval_dd = st.selectbox(label = "Interval:", options = ["1 day", "1 week"], index = 0)

# Create columns for run button and process messages
col_but_1, col_but_2, col_but_3 = st.columns([2, 6, 2])
col_link_1, col_link_2, col_link_3, col_link_4, col_link_5 = st.columns(5)
col_info_1, col_info_2, col_info_3, col_info_4, col_info_5 = st.columns(5)

with col_but_2:
    if st.button("Generate plot"):
        sl_ticker = ticker_input
        sl_period = "3mo" if period_dd == "Last 3 months" else "6mo" if period_dd == "Last 6 months" else "1y"
        sl_interval = "1d" if interval_dd == "1 day" else "1wk"

        with col_info_2:
            working_text = st.text("Generating plot...")

        # Plot the graph
        run_once(sl_ticker, sl_period, sl_interval, True)

        # Remove text from column 5
        with col_info_2:
            working_text.empty()

        with col_link_2:
            st.link_button("GitHub.com/essteer :arrow_right:", "https://github.com/essteer")

        with col_link_3:    
            st.link_button("GitHub.com/ndkma :arrow_right:", "https://github.com/ndkma")


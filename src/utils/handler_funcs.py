# -*- coding: utf-8 -*-
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# Import helper functions
from utils.session_funcs import get_session
from utils.data_funcs import validate_period, validate_interval, get_ticker, get_history
from utils.data_funcs import get_horizon, get_earnings_dates, get_short_name, get_currency
from utils.news_funcs import get_news, get_articles, get_nlp_predictions, get_rolling_averages
from utils.plot_funcs import get_palette, format_plot, plot_candlestick, plot_sentiment

# ===============================================================
# Handler functions
# ===============================================================

def handle_data(raw_tick: str, raw_period: str="3mo", raw_interval: str="1d") -> tuple[yf.Ticker, pd.DataFrame, str, list[str], str, str]:
    """
    Handles function calls for one API call and resultant data processing
    Called by main.run_once()
    
    Parameters
    ----------
    See main.run_once() function for parameter descriptions
    
    Returns
    -------
    tick : yf.Ticker | NOTE: output of API call in utils.data_funcs.get_ticker()
        yFinance Ticker object

    tick_history : pd.DataFrame | NOTE: output of utils.data_funcs.get_history()
        Price history for chosen ticker
    
    tick_horizon : str | NOTE: output of get_horizon()    
        Today's date + 3 months (default) as "YYYY-MM-DD"
    
    earnings_dates : list[str] | NOTE: output of utils.data_funcs.get_earnings_dates()
        List of earnings dates within range
    
    tick_name : str | NOTE: output of utils.data_funcs.get_short_name()
        short name of the ticker
    
    tick_currency : str | NOTE: output of utils.data_funcs.get_currency()
        currency of the ticker
    """
    # NOTE: validate period and interval before API call, for faster error catching
    if not validate_period(raw_period):
        print('Invalid period value! Try "1mo", "3mo", "6mo", or "1y"')
        return None
    if not validate_interval(raw_interval):
        print('Invalid interval value! Try "1d" or "1wk"')
        return None
    
    try:  # Retrieve new session
        new_session = get_session()
    except Exception as e:
        print(f"Error setting session data: {e}")
        return None
    
    # Retrieve Ticker object
    tick = get_ticker(raw_tick, current_session=new_session)
    if type(tick) != yf.Ticker:
        # NOTE: exception already printed by get_ticker()
        return None
    
    # Retrieve price history
    tick_history = get_history(tick, raw_period, raw_interval)
    if type(tick_history) != pd.DataFrame:
        # NOTE: exception already printed by get_history()
        return None
    
    try:  # Retrieve horizon date
        tick_horizon = get_horizon(tick_history, raw_period)
    except Exception as e:
        print(f"Error fixing horizon date: {e}")
        tick_horizon = ""
    
    try:  # Retrieve earnings data (if applicable)
        tick_earnings_dates = get_earnings_dates(tick, tick_history, tick_horizon)
    except Exception as e:
        print(f"Error retrieving earnings dates: {e}")
        tick_earnings_dates = []
    
    try:  # Retrieve short name of Ticker object
        tick_name = get_short_name(tick)
    except Exception as e:
        print(f"Error retrieving ticker name: {e}")
        tick_name = ""
    
    try:  # Retrieve currency of Ticker object
        tick_currency = get_currency(tick)
    except Exception as e:
        print(f"Error retrieving ticker currency: {e}")
        tick_currency = "Currency Undefined"
    
    return tick, tick_history, tick_horizon, tick_earnings_dates, tick_name, tick_currency
    

def handle_news(ticker_name: str) -> pd.DataFrame | None:
    """
    Handles function calls for one API call and resultant data processing
    Called by main.run_once()

    Parameters
    ----------
    ticker_name : str | NOTE: output of utils.data_funcs.get_short_name()
        Short name of ticker for new queries

    Returns
    -------
    dataframe : pd.DataFrame | None if empty
        DataFrame with sentiment by date and rolling averages
    """
    # Get news data based on ticker name
    news_data, query_name = get_news(ticker_name)
    # Check whether news found
    if news_data != {} and query_name != "":

        # Get lists of relevant articles and publication dates
        pub_dates, pub_titles = get_articles(news_data, query_name)
        # Check whether news contained relevant articles
        if pub_dates != [] and pub_titles != []:

            # Zip article dates and titles
            pub_data = zip(pub_dates, pub_titles)

            # Get sentiment predictions by date
            sentiment_data = get_nlp_predictions(pub_data)

            # Get DataFrame with rolling averages
            dataframe = get_rolling_averages(sentiment_data)

            return dataframe

    # Return None if no relevant news data obtained
    return None


def handle_plots(sent_df: pd.DataFrame | None, raw_tick: str, tick_history: pd.DataFrame, tick_horizon: str,
                 tick_earnings_dates: list[str], tick_name: str, tick_currency: str="Currency Undefined",
                 raw_period: str="3mo", raw_interval: str="1d") -> None:
    """
    Calls utils.plot_funcs.plot_candlestick() to plot price and volume data
    Calls utils.plot_funcs.plot_sentiment() to add market sentiment data to candlestick plot
    Called by main.run_once()

    Parameters
    ----------
    See main.run_once(), utils.handler_funcs.handle_data(), 
        and utils.handler_funcs.handle_news() docstrings for parameter descriptions
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
    fig.show()
    

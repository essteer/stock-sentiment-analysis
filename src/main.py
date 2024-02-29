# -*- coding: utf-8 -*-
import os
import random
import requests
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
import warnings
"""
Suppress Pandas future warning: 
FutureWarning: The 'unit' keyword in TimedeltaIndex construction is deprecated 
and will be removed in a future version. Use pd.to_timedelta instead.
df.index += _pd.TimedeltaIndex(dst_error_hours, 'h')
"""
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")
# Load dotenv environment
load_dotenv()
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# ===============================================================
# Header data for randomised referer and user-agent values
# ===============================================================

REFERERS = ["https://www.google.com/",
            "https://bing.com/",
            "https://search.yahoo.com/",
            "https://www.baidu.com/",
            "https://yandex.com/"]

REFERER_PROBS = [0.88, 0.03, 0.03, 0.03, 0.03]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 OPR/102.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.60",
    "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47"
]

USER_AGENT_PROBS = [
    0.205, 0.14, 0.13, 0.105, 0.055,
    0.055, 0.05, 0.045, 0.04, 0.03,
    0.025, 0.02, 0.015, 0.015, 0.015,
    0.0125, 0.0125, 0.012, 0.01, 0.008
]

# ===============================================================
# API request functions
# ===============================================================

def weighted_random_selection(sample_space: list[str], probs: list[float]) -> str:
    """
    Assigns a weighted-random selection of header data
    for API requests

    Parameters
    ----------
    sample_space : list 
        list of options to randomly select from
    
    probs : list 
        list of probabilites per sample in sample_space (sum == 1)
    
    Returns
    -------
    weighted_random_selection : str
        weighted random selection from sample_space
    """
    # k=1 to choose just one sample
    weighted_random_selection = random.choices(sample_space, weights=probs, k=1)

    return weighted_random_selection[0]


def get_session(news_api=False) -> requests.Session:
    """
    Creates a new session for an API request

    Parameters
    ----------
    news_api : bool
        Flag to add API key for News API calls

    Returns
    -------
    session : requests.Session
        New session object for API requests
    """
    # Set session data
    session = requests.Session()
    # Get weighted random referer and user-agent values
    referer = weighted_random_selection(REFERERS, REFERER_PROBS)
    user_agent = weighted_random_selection(USER_AGENTS, USER_AGENT_PROBS)
    # Assign values to session header
    session.headers["User-Agent"] = user_agent
    session.headers["Referer"] = referer
    session.headers["Upgrade-Insecure-Requests"] = "1"

    if news_api:
      session.headers["X-Api-Key"] = NEWS_API_KEY
    
    return session

# ===============================================================
# Plot palette and template
# ===============================================================

palette = {"dark": "#252b33", "grey": "#45464d", "light": "#fefeff", "stone": "#8f8f94", "blue": "#336681", 
           "green": "#089389", "red": "#d34748", "pink": "#cf82d3", "yellow": "#e6daaa", "sky": "#8ebdff"
}

def format_plot(fig) -> None:
    """
    Applies custom theme to Plotly figure in-place
    Called by plot_candlestick()
    
    Parameters
    ----------
    fig : Plotly figure
    
    Returns
    -------
    None : formats fig in-place
    """
    fig.update_layout(
        plot_bgcolor=palette["dark"], paper_bgcolor=palette["dark"],
        title_font_color=palette["light"],
        xaxis_title_font_color=palette["light"], yaxis_title_font_color=palette["light"],
        xaxis_tickfont_color=palette["stone"], yaxis_tickfont_color=palette["stone"],
        xaxis_gridcolor=palette["grey"], yaxis_gridcolor=palette["grey"],
        xaxis_linecolor=palette["stone"], yaxis_linecolor=palette["stone"],
        title={"x": 0.5},  # Center title
        xaxis={"categoryorder": "category ascending"},  # Set y-axis labels from low to high
        yaxis={
            "categoryorder": "category ascending",  # Set y-axis labels from low to high
            # Add invisible y-ticks to add space between y-axis and y-labels
            "ticks": "outside", "tickcolor": palette["dark"], "ticklen": 5,
        },
        legend_font_color=palette["stone"],
        margin=dict(l=80, r=20, t=40, b=20),
    )
    fig.update_yaxes(
        title_standoff = 5
    )


# ===============================================================
# Functions to validate input prior to API calls
# ===============================================================

def validate_period(period: str) -> bool:
    """
    Checks for valid period value prior to API calls
    Called by handle_data()
    
    Parameters
    ----------
    period : str
        The time period length, ending on current date minus 2 or 3 days
        Valid values : "3mo", "6mo", "1y"
             
    Returns
    -------
    bool : True if period valid, else False
    """
    # Selected valid arguments as per yfinance documentation
    valid_period_values = ["3mo", "6mo", "1y"]
    try:
        period = str.lower(period)
        if period not in valid_period_values:
            raise ValueError
    except ValueError:
        return False
    
    return True


def validate_interval(interval: str) -> bool:
    """
    Checks for valid interval value prior to API calls
    Called by handle_data()
    
    Parameters
    ----------
    interval : str
        The interval frequency
        Valid values : "1d", "1wk"
        
    Returns
    -------
    bool : True if interval valid, else False
    """
    # Selected valid arguments as per yfinance documentation
    valid_interval_values = ["1d", "1wk"]
    try:
        interval = str.lower(interval)
        if interval not in valid_interval_values:
            raise ValueError
    except ValueError:
        return False
    
    return True


# ===============================================================
# Functions to call and process yfinance API data
# ===============================================================

def get_ticker(ticker: str, current_session: requests.Session) -> yf.Ticker:
    """
    Gets ticker data via call to yfinance API
    Called by handle_data()
    
    Parameters
    ----------
    ticker : str
        The official abbreviation of the stock
        Valid values : Any official stock ticker symbol that exists on Yahoo! Finance
        eg. "msft"
    
    current_session : requests_cache.CachedSession
        Session data for API call to yfinance
        NOTE: set by weighted_random_selection() and handle_data()
    
    Returns
    -------
    yf_ticker : yfinance Ticker object
    """
    # Get the ticker data
    try:
        yf_ticker = yf.Ticker(str.upper(ticker), session=current_session)
    except Exception as e:
        print(e)
        return "Invalid ticker value!"
    # Confirm ticker object not empty (invalid ticker)
    try:
        _ = yf_ticker.info["symbol"]
    except KeyError:
        return "Invalid ticker value!"
    
    return yf_ticker


def get_history(ticker: yf.Ticker, period: str="3mo", interval: str="1d") -> pd.DataFrame | str:
    """
    Retrieves price history data from yfinance Ticker object
    Called by handle_data()
    
    Parameters
    ----------
    ticker : yfinance Ticker object | NOTE: output of get_ticker()
        
    period : str | NOTE: pre-validated by validate_time_ranges()
        The time period length, ending on current date minus 2 or 3 days
        Valid values : "3mo", "6mo", "1y"
        
    interval : str | NOTE: pre-validated by validate_time_ranges()
        The interval frequency
        Valid values : "1d", "1wk"
        
    Complete example : get_history(<yf.Ticker>, "6mo", "1d")
    
    Returns
    -------
    history : pd.DataFrame
    """
    valid_period = str.lower(period)
    valid_interval = str.lower(interval)
    # Pull stock price dataframe, adjusted for corporate actions (stock splits, dividends)
    try:
        history = ticker.history(period = valid_period, interval = valid_interval, auto_adjust = True)
    except Exception as e:
        return f"Error retrieving price history: {e}" 
    
    return history


def get_horizon(history: pd.DataFrame, horizon_months: int=3) -> str:
    """
    Calculates horizon beyond latest price date (defaults to 3 months ahead)
    Called by handle_data()
    
    Parameters
    ----------
    history : pd.DataFrame | NOTE: output of get_history()
        Price history for chosen ticker

    horizon_months : int
        No. months ahead to project earnings dates (default = 3)
        Must be 0 <= horizon_months <= 12
    
    Returns
    -------
    new_horizon : str
        Today's date + horizon_months as "YYYY-MM-DD"
    """
    # Failsafes to prevent negative and extreme horizons
    horizon = max(0, horizon_months)
    horizon = min(horizon, 12)
    # Get date range from ticker_history
    history_dates = history.index
    # Calculate history end date + horizon_months
    new_horizon = (list(history_dates)[-1] + pd.DateOffset(months=horizon)).strftime("%Y-%m-%d")

    return new_horizon


def get_earnings_dates(ticker: yf.Ticker, history: pd.DataFrame, horizon: str) -> list[str]:
    """
    Identifies earnings dates from start of period range to horizon
    Called by handle_data()

    Parameters
    ----------
    ticker : yfinance Ticker object | NOTE: output of get_ticker()

    history : pd.DataFrame | NOTE: output of get_history()
        Price history for chosen ticker
        
    new_horizon : str | NOTE: output of get_horizon()
        Today's date + horizon_months as "YYYY-MM-DD"

    Returns
    -------
    valid_earnings : list[str]
        List of earnings dates within range
    """
    # Extract earnings dates from Ticker object
    earnings_dates = ticker.earnings_dates.index
    # Extract YYYY-MM-DD from earnings dates as strings
    earnings_dates = [date.strftime("%Y-%m-%d") for date in earnings_dates]
    # Get date range from ticker_history
    history_dates = history.index
    # Get start date
    history_min = list(history_dates)[0].strftime("%Y-%m-%d")
    # Get list of earnings dates within history_min_max range + 3 months
    valid_earnings = [x for x in earnings_dates if x >= history_min and x <= horizon]
    
    return valid_earnings


def get_short_name(ticker: yf.Ticker) -> str:
    """
    Gets the short name from yf.Ticker.info
    Called by handle_data()

    Parameters
    ----------
    ticker : yfinance Ticker object | NOTE: output of get_ticker()
    
    Returns
    -------
    name : str
        The shortest name out of shortName and longName
    """
    short_name = ticker.info["shortName"]
    long_name = ticker.info["longName"]
    # Select shortest of the two names
    name = min([short_name, long_name], key=len)
    
    return name


def get_currency(ticker: yf.Ticker) -> str:
    """
    Gets the currency from yf.Ticker.info
    Called by handle_data()

    Parameters
    ----------
    ticker : yfinance Ticker object | NOTE: output of get_ticker()
    
    Returns
    -------
    currency : str
        The currency stored in yf.Ticker.info["currency"]
    """
    currency = ticker.info["currency"]
    
    return currency


# ===============================================================
# Candlestick plot for selected ticker, period and interval
# ===============================================================

def plot_candlestick(ticker_code: str, history: pd.DataFrame, horizon: str, earnings_dates: list=[],
                     name: str="", currency: str="Currency Undefined", period: str="3mo", interval: str="1d") -> None:
    """
    Creates a candlestick graph for a specified stock, time period and interval.
    Called by run_once()

    Parameters
    ----------
    See run_once() and handle_data() functions for parameter descriptions

    Complete example : plot_candlestick("MSFT", <pd.DataFrame>, "YYYY-MM-DD", ["YYYY-DD-MM", "YYYY-DD-MM"],
    "Microsoft Corporation", "USD", "1d")
    """
    fig = go.Figure(
        data=[go.Candlestick(x = history.index,
                             open = history["Open"],
                             high = history["High"],
                             low = history["Low"],
                             close = history["Close"],
                             name = "Price Data"
    )])
    start_date = history.index.min()
    end_date = history.index.max()

    # Get date range information for plot title
    start_date_string = start_date.strftime("%d %b. %Y")
    end_date_string = end_date.strftime("%d %b. %Y")    # here b/c end_date reassigned to horizon below
    date_range_label = f"{start_date_string} - {end_date_string}"

    # Extend x-axis to horizon
    if horizon != "":
        fig.update_layout(
            xaxis_range=[history.index.min(), horizon]
        )
        end_date = horizon

    # Calculate total mean
    mean_value = history["Close"].mean()
    # Add horizontal dashed line for mean
    fig.add_shape(
        type = "line",
        x0 = start_date, x1 = end_date,
        y0 = mean_value, y1 = mean_value,
        line = dict(color = palette["stone"], width = 2, dash = "dash"),
        name = "Mean",
        showlegend = True
    )
    # Get period to determine x-axis date display
    periods_dict = {"3mo": 7, "6mo": 7, "1y": 14}
    period_label = periods_dict[period.lower()]
    
    # Get interval label for plot title
    intervals_dict = {"1d": "Daily", "1wk": "Weekly"}
    interval_label = intervals_dict[interval.lower()]

    # Combine name, ticker, and interval for plot title
    ticker_label = f"{name} ({ticker_code.upper()}) {interval_label}"
    # Update layout
    fig.update_layout(
        title = f"{ticker_label} Close Price <br>{date_range_label}",
        xaxis_title = "Date",
        xaxis = {"tickangle": 45, "dtick": 86400000*period_label, "tickformat": "%Y-%m-%d"},
        xaxis_rangeslider_visible = False,
        yaxis_title = f"Price ({currency})",
        width=900,
        height=400,
    )
    # Add earnings dates as vertical lines
    if earnings_dates != []:
        reverse_earnings_dates = earnings_dates[::-1] # Reverse list so legend is chronological
        for date in reverse_earnings_dates:
            fig.add_shape(
                type = "line",
                x0=date, x1=date,
                y0=0, y1=1, xref="x", yref="paper",
                line = dict(color = palette["pink"], width = 2, dash = "dash"),
                name = f"ED '{date[2:]}",
                showlegend = True
                )
    # Show plot
    format_plot(fig)
    fig.show()


# ===============================================================
# Handler functions
# ===============================================================

def handle_data(raw_tick: str, raw_period: str="3mo", raw_interval: str="1d") -> tuple[yf.Ticker, pd.DataFrame, str, list[str], str, str]:
    """
    Handles function calls for one API call and resultant data processing
    Called by run_once()
    
    Parameters
    ----------
    See run_once() function for parameter descriptions
    
    Returns
    -------
    tick : yf.Ticker | NOTE: output of API call in get_ticker()
        yFinance Ticker object

    tick_history : pd.DataFrame | NOTE: output of get_history()
        Price history for chosen ticker
    
    tick_horizon : str | NOTE: output of get_horizon()    
        Today's date + 3 months (default) as "YYYY-MM-DD"
    
    earnings_dates : list[str] | NOTE: output of get_earnings_dates()
        List of earnings dates within range
    
    tick_name : str | NOTE: output of get_short_name()
        short name of the ticker
    
    tick_currency : str | NOTE: output of get_currency()
        currency of the ticker
    """
    # NOTE: validate period and interval before API call, for faster error catching
    if not validate_period(raw_period):
        print('Invalid period value! Try "3mo", "6mo", or "1y"')
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
        tick_horizon = get_horizon(tick_history)
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
    
    
def handle_plots(raw_tick: str, tick_history: pd.DataFrame, tick_horizon: str, 
                 tick_earnings_dates: list[str], tick_name: str, tick_currency: str="Currency Undefined", 
                 raw_period: str="3mo", raw_interval: str="1d") -> None:
    """
    Calls plot_candlestick() to plot price data
    Called by run_once()

    Parameters
    ----------
    See run_once() and handle_data() functions for parameter descriptions
    """
    # Create candlestick plot
    plot_candlestick(raw_tick, tick_history, tick_horizon, tick_earnings_dates,
                         tick_name, tick_currency, raw_period, raw_interval)


def run_once(raw_ticker: str, raw_period: str="3mo", raw_interval: str="1d", show_plots=False) -> None:
    """
    Master function: 
        Calls handle_data() to obtain and process data
        Calls handle_plots() to generate plots
    
    Parameters
    ----------
    raw_ticker : str
        The official abbreviation of the stock
        Valid values : Any official stock ticker symbol that exists on Yahoo! Finance
        eg. "msft"
        
    raw_period : str
        The time period length, ending on current date minus 2 or 3 days
        Valid values : "3mo", "6mo", "1y"
        
    raw_interval : str
        The interval frequency
        Valid values : "1d", "1wk"
        
    show_plots : bool
        Boolean flag to determine whether to call plot functions (default = False)
    """
    try:
        # Retain t_obj (Ticker object) for further use
        t_obj, t_hist, t_horizon, t_earn_dates, t_name, t_curr =  handle_data(raw_ticker, raw_period, raw_interval)
    
        if show_plots == True:
            try:
                # Send raw_ticker to pass the string for plotting, not the Ticker object
                handle_plots(raw_ticker, t_hist, t_horizon, t_earn_dates, t_name, t_curr, raw_period, raw_interval)
            except Exception as e:
                print(f"Error during plot handling: {e}")
    
    except Exception as e:
        print(f"Error during data handling: {e}")


# ===============================================================
# Tests - with plots
# ===============================================================

# Valid ticker, period, and interval
# run_once("AAPL", "6mo", "1d", True)
# run_once("AAPL", "1y", "1d", True)
# run_once("AZN.L", "6mo", "1d", True)

# ===============================================================
# News API test
# ===============================================================

# new_session = get_session(news_api=True)
# BASE_URL = "https://newsapi.org/v2/"
# url = BASE_URL + "top-headlines?country=us"
# response = new_session.get(url, headers=new_session.headers)
# data = response.json()
# print(data["articles"][0])

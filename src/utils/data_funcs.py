# -*- coding: utf-8 -*-
import requests, warnings
import yfinance as yf
import pandas as pd
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")

# ===============================================================
# Functions to validate input prior to API calls
# ===============================================================

def validate_period(period: str) -> bool:
    """
    Checks for valid period value prior to API calls
    Called by utils.handler_funcs.handle_data()
    
    Parameters
    ----------
    period : str
        The time period length, ending on current date minus 2 or 3 days
        Valid values : "1mo", "3mo", "6mo", "1y"
             
    Returns
    -------
    bool : True if period valid, else False
    """
    # Selected valid arguments as per yfinance documentation
    valid_period_values = ["1mo", "3mo", "6mo", "1y"]
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
    Called by utils.handler_funcs.handle_data()
    
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

def get_ticker(ticker: str, current_session: requests.Session) -> yf.Ticker | str:
    """
    Gets ticker data via call to yfinance API
    Called by utils.handler_funcs.handle_data()
    
    Parameters
    ----------
    ticker : str
        The official abbreviation of the stock
        Valid values : Any official stock ticker symbol that exists on Yahoo! Finance
        eg. "msft"
    
    current_session : requests_cache.CachedSession
        Session data for API call to yfinance
        NOTE: set by 
            utils.session_funcs.weighted_random_selection()
            utils.handler_funcs.handle_data()
    
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
    Called by utils.handler_funcs.handle_data()
    
    Parameters
    ----------
    ticker : yfinance Ticker object | NOTE: output of utils.data_funcs.get_ticker()
        
    period : str | NOTE: pre-validated by utils.data_funcs.validate_period()
        The time period length, ending on current date minus 2 or 3 days
        Valid values : "1mo", "3mo", "6mo", "1y"
        
    interval : str | NOTE: pre-validated by utils.data_funcs.validate_interval()
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
        history = ticker.history(period=valid_period, interval=valid_interval, auto_adjust=True)
    except Exception as e:
        return f"Error retrieving price history: {e}" 
    
    return history


def get_horizon(history: pd.DataFrame, period: str="3mo", horizon_months: int=3) -> str:
    """
    Calculates horizon beyond latest price date, 
    defaults to 3 months ahead or 1 month for periods of 1 month
    Called by utils.handler_funcs.handle_data()

    Parameters
    ----------
    history : pd.DataFrame | NOTE: output of utils.data_funcs.get_history()
        Price history for chosen ticker
    
    period : str
        The time period length, ending on current date minus 2 or 3 days
        Valid values : "1mo", "3mo", "6mo", "1y"

    horizon_months : int
        No. months ahead to project earnings dates (default = 3)
        Must be 0 <= horizon_months <= 12

    Returns
    -------
    new_horizon : str
        Today's date + horizon_months as "YYYY-MM-DD"
    """
    if period.lower() == "1mo":
        horizon = 1
    else:
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
    Called by utils.data_funcs.handle_data()

    Parameters
    ----------
    ticker : yfinance Ticker object | NOTE: output of utils.data_funcs.get_ticker()

    history : pd.DataFrame | NOTE: output of utils.data_funcs.get_history()
        Price history for chosen ticker

    horizon : str | NOTE: output of utils.data_funcs.get_horizon()
        Today's date + horizon_months as "YYYY-MM-DD"

    Returns
    -------
    valid_earnings : list[str]
        List of earnings dates within range
    """
    try:
        if ticker.earnings_dates is None:
            valid_earnings = []
        else:
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
    
    except AttributeError:
        # Ticker.earnings_dates non-existant for e.g. indices, currencies
        valid_earnings = []

    return valid_earnings


def get_short_name(ticker: yf.Ticker) -> str:
    """
    Gets the short name from yf.Ticker.info
    Called by utils.data_funcs.handle_data()

    Parameters
    ----------
    ticker : yfinance Ticker object | NOTE: output of utils.data_funcs.get_ticker()
    
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
    Called by utils.data_funcs.handle_data()

    Parameters
    ----------
    ticker : yfinance Ticker object | NOTE: output of utils.data_funcs.get_ticker()
    
    Returns
    -------
    currency : str
        The currency stored in yf.Ticker.info["currency"]
    """
    currency = ticker.info["currency"]
    
    return currency


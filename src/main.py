# -*- coding: utf-8 -*-
import os, random, requests, time, warnings
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
import spacy
import spacy_transformers  # required for transformer model
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
        title_standoff=5
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

def get_ticker(ticker: str, current_session: requests.Session) -> yf.Ticker | str:
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
        history = ticker.history(period=valid_period, interval=valid_interval, auto_adjust=True)
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
    try:
        if ticker.earnings_dates is None:
            valid_earnings = [""]
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
        valid_earnings = [""]

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
# Functions to call and process News API data
# ===============================================================

def get_news(short_name: str) -> tuple[dict, str]:
    """
    Makes call to News API and returns response data

    Parameters
    ----------
    short_name : str | NOTE: output of get_short_name()
        Short name of the ticker

    Returns
    -------
    data : dict
        Dictionary of JSON response from News API call
    
    name_list[0] : str
        First term of search query used
    """
    # Prepare name for search query
    name = short_name[:].lower()
    name = name.replace("-", " ")
    name_list = name.split()

    if len(name_list) == 1:
        query = name_list[0]
    # Take first two words of ticker name if applicable
    else:
        query = f"{name_list[0]} OR ({name_list[0]} AND {name_list[1]})"

    # NOTE: max URL length = 500 characters
    base_url = "https://newsapi.org/v2/everything?"
    # Break domains in half for easier code review
    domains_1 = "aljazeera.com,bbc.com,businessinsider.com,cnn.com,forbes.com,indiatimes.com,"
    domains_2 = "investing.com,marketwatch.com,marketscreener.com,wsj.com,washingtonpost.com"
    domains = domains_1 + domains_2
    # Compile query string
    query_string = {"q":query,"language":"en","domains":domains}

    # Loop with short delay to handle one-off API errors
    for i in range(3):
        try:
            # Get new session for API call
            news_session = get_session(news_api=True)
            # Make API call
            response = news_session.get(base_url, headers=news_session.headers, params=query_string)
            # Extract data from response
            data = response.json()

            check_articles = len(data["articles"])
            if check_articles >= 1:
                return data, name_list[0]

        except KeyError:
            time.sleep(1)
            continue

        except Exception as e:
            print(f"Error getting news: {e}")
            time.sleep(1)
            continue

    # Return empty dict if calls fail (or articles empty)
    return {}, name_list[0]


def get_articles(data: dict, query: str) -> tuple[list[str]]:
    """
    Extracts relevant articles from news data

    Parameters
    ----------
    data : dict | NOTE: output of get_news()
        Dictionary of JSON response from News API call

    query : str | NOTE: output of get_news()
        First word of ticker name as used for news query

    Returns
    -------
    dates : list[str]
        Dates of articles relevant to ticker as YYYY-MM-DD

    titles : list[str]
        Titles of articles relevant to ticker
    """
    articles = data["articles"]
    qry = query.lower()
    dates, titles = [], []

    for article in articles:
        try:
            # Confirm article is relevant to ticker
            art_title = article["title"].lower()
            art_desc = article["description"].lower()
            art_cont = article["content"].lower()
            if qry not in art_title and qry not in art_desc and qry not in art_cont:
                continue
            else:
                # Get YYYY-MM-DD for publish date
                dates.append(article["publishedAt"][0:10])
                titles.append(article["title"])

        except (KeyError, AttributeError):
            continue
        
        except Exception as e:
            print(f"Error getting article: {e}")
            continue

    return dates, titles


# ===============================================================
# Functions to run NLP model and process sentiment data
# ===============================================================

def get_nlp_predictions(article_data: zip) -> dict:
    """
    Loads pre-trained spaCy transformer model and produces
    sentiment predictions for headline data

    Parameters
    ----------
    article_data : zip
        Zip of article dates and article headlines

    Returns
    -------
    aggregate_sentiment : dict
        Average sentiment of article headlines grouped by date
    """
    model_path = "./models/model-best-24"
    # Load sentiment analysis model
    nlp = spacy.load(model_path)

    # Initialise dictionary for sentiment by date
    sentiment_dict = {}

    # Iterate through dates and headlines
    for date, headline in list(article_data):
        # Get sentiment predictions for headline
        prediction = nlp(headline).cats
        # Get difference between positive and negative probabilities
        sentiment_spread = prediction["positive"] - prediction["negative"]
        # Get current value list for date key if it exists, otherwise create empty list
        date_sentiment = sentiment_dict.get(date, [])
        # Append new prediction to list for that date
        date_sentiment.append(sentiment_spread)
        # Update dictionary values
        sentiment_dict[date] = date_sentiment

    # Create dict with average sentiment for each date present
    aggregate_sentiment = {k: (sum(v)/len(v)) for k, v in sentiment_dict.items()}

    return aggregate_sentiment


def get_rolling_averages(sent_data: dict) -> pd.DataFrame:
    """
    Creates DataFrame of predicted sentiments organised with date
    and rolling averages across time windows

    Parameters
    ----------
    sent_data : dict | NOTE: output of get_nlp_predictions()
        Average sentiment of article headlines grouped by date

    Returns
    -------
    df : Pandas DataFrame
        DataFrame with sentiment by date and rolling averages
    """
    # Set dates as index
    df = pd.DataFrame.from_dict(sent_data, columns=["sentiment"], orient="index")
    # Sort rows by date
    df = df.sort_index()
    # Set window size for rolling average
    window = 7
    # Add rolling average column
    df["rolling_avg"] = df["sentiment"].rolling(window=window).mean()

    return df


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
    fig.update_xaxes(range=[history.index.min(), horizon], title_text="Date", title=dict(font=dict(color=palette["light"])),
                     tickfont=dict(color=palette["stone"]), gridcolor=palette["grey"], linecolor=palette["stone"],
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
                      xaxis_rangeslider_visible=False, width=1080, height=720)

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
    max_value = np.nanmax(sent_df["rolling_avg"])
    min_value = np.nanmin(sent_df["rolling_avg"])
    # Calculate upper and lower bounds
    upper_bound = min([1.0, max_value + 0.2])
    lower_bound = max([-1.0, min_value - 0.2])
    
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
        tick_earnings_dates = [""]
    
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
    Called by run_once()

    Parameters
    ----------
    ticker_name : str | NOTE: output of get_short_name()
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
    Calls plot_candlestick() to plot price and volume data
    Calls plot_sentiment() to add market sentiment data to candlestick plot
    Called by run_once()

    Parameters
    ----------
    See run_once(), handle_data(), handle_news() docstrings for parameter descriptions
    """
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
# Tests - with plots
# ===============================================================

# Valid ticker, period, and interval
# run_once("AAPL", "6mo", "1d", True)
# run_once("SPY", "6mo", "1d", True)
run_once("BTC-USD", "6mo", "1d", True)
# run_once("MSFT", "1y", "1wk", True)
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

# demo_name = "Ford Motor Company"
# article_dates, article_titles = handle_news(demo_name)
# print(len(article_dates))
# print(len(article_titles))

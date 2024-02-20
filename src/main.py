# -*- coding: utf-8 -*-
import random
import requests_cache
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
# Random header data function
# ===============================================================

def weighted_random_selection(sample_space: list[str], probs: list[float]) -> str:
    """
    Assigns a weighted-random selection of header data
    for API requests

    Args:
        sample_space: list of options to randomly select from
        probs: list of probabilites per sample in sample_space (sum == 1)
    Returns:
        weighted random selection from sample_space
    """
    # k=1 to choose just one sample
    weighted_random_selection = random.choices(sample_space, weights=probs, k=1)

    return weighted_random_selection[0]


# ===============================================================
# Plot palette and template
# ===============================================================

palette = {"dark": "#252b33", "grey": "#45464d", "light": "#fefeff", "stone": "#8f8f94",
           "blue": "#336681", "green": "#089389", "red": "#d34748", "pink": "#cf82d3", "yellow": "#e6daaa", "sky": "#8ebdff"
}

def format_plot(fig):
    """
    Applies custom theme to Plotly figure.
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
        margin=dict(l=80, r=20, t=40, b=20)
    )
    fig.update_yaxes(
        title_standoff = 5
    )

# ===============================================================
# Function to create candlestick plot for selected ticker, period and interval
# ===============================================================
    
def get_price_history_graph(ticker, period, interval):
    """
    This function creates a candlestick graph for a specified stock for a specified time period and iterval.
    
    Parameters
    ----------
    ticker : str
        The official abbreviation of the stock
        Valid values : Any official stock ticker symbol that exists on Yahoo! Finance
        eg. "msft"
        
    period : str
        The time period length, ending on current date minus 2 or 3 days ===NEED REVIEW===
        Valid values : "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
        eg. "6mo"
        
    interval : str
        The interval frequency
        Valid values : "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"
        eg. "1d"
        
    Complete example : get_price_history_graph("nvda", "6mo", "1d")
    
    """
    
    # Valid arguments as per yfinance documentation
    valid_period_values = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    valid_interval_values = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    
    label = str.upper(ticker) # only for plot purposes
    
    # Set the ticker
    ticker = yf.Ticker(str.upper(ticker))
    
    # Set the period, with validation
    try:
        period = str.lower(period)
        if period not in valid_period_values:
            raise ValueError(
                'Invalid period value! Try "1d", "5d", "1mo", "3mo", '
                '"6mo", "1y", "2y", "5y", "10y", "ytd", "max"'
            )       
    except ValueError as e:
        print(str(e))
        return  # Exit the function when an invalid period value is encountered
    
    # Set the interval, with validation
    try:
        interval = str.lower(interval)
        if interval not in valid_interval_values:
            raise ValueError(
                'Invalid interval value! Try "1m", "2m", "5m", '
                '"15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"'
            )     
    except ValueError as e:
        print(str(e))
        return  # Exit the function when an invalid interval value is encountered

    
    # Pull stock dataframe, adjust for corporate actions (stock splits, dividends)
    full_history = ticker.history(period = period, interval = interval, auto_adjust = True)

    
    fig = go.Figure(data=[go.Candlestick(x = full_history.index,
                open = full_history["Open"],
                high = full_history["High"],
                low = full_history["Low"],
                close = full_history["Close"]
    )])
    
    # Calculate total mean
    mean_value = full_history["Close"].mean()
    
    # Add horizontal dashed line for mean
    fig.add_shape(
    type = "line", x0 = full_history.index.min(), x1 = full_history.index.max(), y0 = mean_value, y1 = mean_value,
    line = dict(color = palette["stone"], width = 2, dash = "dash"), name = "Mean"
    )
    
    # Update layout
    fig.update_layout(title = f"{label} Daily Close Price",
                  xaxis_title = "Date",
                  xaxis = {"tickangle": 45, "dtick": 86400000*7, "tickformat": "%Y-%m-%d"},
                  xaxis_rangeslider_visible = False,
                  yaxis_title = f"Close Price {label}"
    )
    
    # Show plot
    format_plot(fig)
    fig.show()

# ===============================================================
# Test
# ===============================================================
    
get_price_history_graph("aapl", "6mo", "1d")
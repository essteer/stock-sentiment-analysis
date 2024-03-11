# -*- coding: utf-8 -*-
from utils.handler_funcs import handle_data, handle_news, handle_plots

def run_once(raw_ticker: str, raw_period: str="3mo", raw_interval: str="1d", show_plots=False) -> None:
    """
    Master function:
        Calls utils.handler_funcs.handle_data() to obtain and process data
        Calls utils.handler_funcs.handle_news() to obtain and process news data
        Calls utils.handler_funcs.handle_plots() to generate plots

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
        Boolean flag to determine whether to call plot functions (default=False)
    """
    try:
        # Retain t_obj (Ticker object) for further use
        t_obj, t_hist, t_horizon, t_earn_dates, t_name, t_curr =  handle_data(
            raw_ticker, raw_period, raw_interval
        )

        try:
            # Get news headline sentiment data for ticker
            sentiment_df = handle_news(t_name)
        except Exception as e:
            print(f"Error getting market sentiment data: {e}")
            sentiment_df = None

        if show_plots == True:
            try:
                # Send raw_ticker to pass the string for plotting, not the Ticker object
                handle_plots(
                    sentiment_df, raw_ticker, t_hist, t_horizon, t_earn_dates, 
                    t_name, t_curr, raw_period, raw_interval
            )
            except Exception as e:
                print(f"Error during plot handling: {e}")

    except Exception as e:
        print(f"Error during data handling: {e}")


# ===============================================================
# Sample runs
# ===============================================================

# Valid ticker, period, and interval
# run_once("AAPL", "3mo", "1d", True)
# run_once("AAPL", "6mo", "1d", True)
# run_once("MA", "1mo", "1d", True)
# run_once("SPY", "6mo", "1d", True)
# run_once("BTC-USD", "6mo", "1d", True)
# run_once("TBCG.L", "6mo", "1d", True)
run_once("MSFT", "1y", "1wk", True)
# run_once("AZN.L", "6mo", "1d", True)

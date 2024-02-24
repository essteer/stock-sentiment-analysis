# -*- coding: utf-8 -*-
import pandas as pd
import random
import requests_cache
import time
import unittest
import warnings
import yfinance as yf
from main import weighted_random_selection, validate_period, validate_interval
from main import get_ticker, get_history, get_horizon, get_earnings_dates
"""
Suppress Pandas future warning: 
FutureWarning: The 'unit' keyword in TimedeltaIndex construction is deprecated 
and will be removed in a future version. Use pd.to_timedelta instead.
df.index += _pd.TimedeltaIndex(dst_error_hours, 'h')
"""
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")

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
# Unit tests
# ===============================================================

class UnitTestsAPI(unittest.TestCase):
    
    def test_weighted_random_selection(self):
        # Test valid referer is returned
        referer = weighted_random_selection(REFERERS, REFERER_PROBS)
        self.assertTrue(referer in REFERERS)
        # Test valid user-agent is returned
        user_agent = weighted_random_selection(USER_AGENTS, USER_AGENT_PROBS)
        self.assertTrue(user_agent in USER_AGENTS)
        
        
    def test_validate_period(self):
        # Test valid lowercase and uppercase values
        for period in ["3mo", "6mo", "1y", "3MO", "6MO", "1Y"]:
            result = validate_period(period)
            self.assertTrue(result, f"Error: valid period '{period}' rejected by validate_period()")
        # Test invalid values
        for period in ["3mon", "1d", "1wk", "1mo", "AAPL"]:
            result = validate_period(period)
            self.assertFalse(result, f"Error: invalid period '{period}' accepted by validate_period()")
        

    def test_validate_interval(self):
        # Test valid lowercase and uppercase values
        for interval in ["1d", "1wk", "1mo", "1D", "1WK", "1MO"]:
            result = validate_interval(interval)
            self.assertTrue(result, f"Error: valid interval '{interval}' rejected by validate_interval()")
        # Test invalid values
        for interval in ["1dy", "1m", "6mo", "1y", "AAPL"]:
            result = validate_interval(interval)
            self.assertFalse(result, f"Error: invalid interval '{interval}' accepted by validate_interval()")


    def test_get_ticker(self):
        # Test valid ticker values
        for ticker in ["0293.HK", "6758.T", "AAPL", "aapl", "AZN.L", "CPR.MI", "mc.Pa", "SPY"]:
            
            new_session = requests_cache.CachedSession("yfinance.cache")
            # Get weighted random referer and user-agent values
            referer = weighted_random_selection(REFERERS, REFERER_PROBS)
            user_agent = weighted_random_selection(USER_AGENTS, USER_AGENT_PROBS)
            # Assign values to new_session header
            new_session.headers["User-Agent"] = user_agent
            new_session.headers["Referer"] = referer
            new_session.headers["Upgrade-Insecure-Requests"] = "1"
            
            result = get_ticker(ticker, current_session=new_session)
            self.assertTrue(isinstance(result, yf.Ticker), 
                            f"Error: valid ticker '{ticker}' failed API call")
            time.sleep(1)
        
        # Test invalid ticker values
        for ticker in ["Lorem ipsum", "100000", "xxxxxxxxx"]:
            
            new_session = requests_cache.CachedSession("yfinance.cache")
            # Get weighted random referer and user-agent values
            referer = weighted_random_selection(REFERERS, REFERER_PROBS)
            user_agent = weighted_random_selection(USER_AGENTS, USER_AGENT_PROBS)
            # Assign values to new_session header
            new_session.headers["User-Agent"] = user_agent
            new_session.headers["Referer"] = referer
            new_session.headers["Upgrade-Insecure-Requests"] = "1"
            
            result = get_ticker(ticker, current_session=new_session)
            self.assertFalse(isinstance(result, yf.Ticker), 
                             f"Error: invalid ticker '{ticker}' passed API call")
            time.sleep(1)
            
    
    def test_get_history(self):
        # Set default session
        new_session = requests_cache.CachedSession("yfinance.cache")
        # Set baseline ticker value
        test_ticker = "AAPL"
        base_ticker = get_ticker(test_ticker, current_session=new_session)
        # Test against valid period values
        test_periods = ["3mo", "6mo", "1y"]
        # Expected durations in days
        expected_durations = {"3mo": 91, "6mo": 183, "1y": 365}
        
        for period in test_periods:
            # Get history
            test_history = get_history(base_ticker, period)
            # Calculate difference between first and last date
            duration = (test_history.index[-1] - test_history.index[0]).days
            # Confirm difference approximates expected time range
            self.assertTrue(
                abs(duration - expected_durations[period]) <= 7, 
                f"Error: date range mismatch for '{period}'"
            )



if __name__ == "__main__":
    unittest.main(verbosity=2)
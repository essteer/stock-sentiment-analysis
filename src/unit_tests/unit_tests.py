# -*- coding: utf-8 -*-
import requests
import sys
import time
import warnings

sys.path.append("..")  # Add parent directory to path
import yfinance as yf
import pandas as pd
import unittest
from masquer import masq
from utils.data_funcs import validate_period, validate_interval, get_ticker
from utils.data_funcs import get_history, get_horizon, get_earnings_dates

# NOTE: run "python -m unit_tests.unit_tests" from src directory to test
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")


class UnitTestsAPI(unittest.TestCase):
    def test_validate_period(self):
        # Test valid lowercase and uppercase values
        for period in ["1mo", "3mo", "6mo", "1y", "3MO", "6MO", "1Y"]:
            result = validate_period(period)
            self.assertTrue(
                result, f"Error: valid period '{period}' rejected by validate_period()"
            )
        # Test invalid values
        for period in ["3mon", "1d", "1wk", "AAPL"]:
            result = validate_period(period)
            self.assertFalse(
                result,
                f"Error: invalid period '{period}' accepted by validate_period()",
            )

    def test_validate_interval(self):
        # Test valid lowercase and uppercase values
        for interval in ["1d", "1wk", "1D", "1WK"]:
            result = validate_interval(interval)
            self.assertTrue(
                result,
                f"Error: valid interval '{interval}' rejected by validate_interval()",
            )
        # Test invalid values
        for interval in ["1dy", "1mo", "6mo", "1y", "AAPL"]:
            result = validate_interval(interval)
            self.assertFalse(
                result,
                f"Error: invalid interval '{interval}' accepted by validate_interval()",
            )

    def test_get_ticker(self):
        # Test valid ticker values
        for ticker in [
            "0293.HK",
            "6758.T",
            "AAPL",
            "aapl",
            "AZN.L",
            "CPR.MI",
            "mc.Pa",
            "SPY",
        ]:
            new_session = requests.Session()
            # Get weighted random referer and user-agent values
            header = masq(ua=True, rf=True)
            # Assign values to session header
            new_session.headers["User-Agent"] = header["User-Agent"]
            new_session.headers["Referer"] = header["Referer"]
            new_session.headers["Upgrade-Insecure-Requests"] = "1"

            result = get_ticker(ticker, current_session=new_session)
            self.assertTrue(
                isinstance(result, yf.Ticker),
                f"Error: valid ticker '{ticker}' failed API call",
            )
            time.sleep(1)

        # Test invalid ticker values
        for ticker in ["Lorem ipsum", "100000", "xxxxxxxxx"]:
            new_session = requests.Session()
            # Get weighted random referer and user-agent values
            header = masq(ua=True, rf=True)
            # Assign values to session header
            new_session.headers["User-Agent"] = header["User-Agent"]
            new_session.headers["Referer"] = header["Referer"]
            new_session.headers["Upgrade-Insecure-Requests"] = "1"

            result = get_ticker(ticker, current_session=new_session)
            self.assertFalse(
                isinstance(result, yf.Ticker),
                f"Error: invalid ticker '{ticker}' passed API call",
            )
            time.sleep(1)

    def test_get_history(self):
        # Set default session
        new_session = requests.Session()
        # Set baseline ticker value
        ticker_label = "AAPL"
        test_ticker = get_ticker(ticker_label, current_session=new_session)
        # Test against valid period values
        test_periods = ["3mo", "6mo", "1y"]
        # Expected durations in days
        expected_durations = {"3mo": 91, "6mo": 183, "1y": 365}

        for period in test_periods:
            # Get history
            test_history = get_history(test_ticker, period)
            # Calculate difference between first and last date
            duration = (test_history.index[-1] - test_history.index[0]).days
            # Confirm difference approximates expected time range
            self.assertTrue(
                abs(duration - expected_durations[period]) <= 7,
                f"Error: date range mismatch for '{period}'",
            )
            self.assertTrue(
                isinstance(test_history, pd.DataFrame),
                f"Error: Pandas DataFrame not obtained for '{period}'",
            )
            time.sleep(1)

    def test_get_horizon(self):
        # Set default session
        new_session = requests.Session()
        # Set baseline ticker value
        ticker_label = "AAPL"
        test_ticker = get_ticker(ticker_label, current_session=new_session)
        # Get history
        test_history = get_history(test_ticker)

        # Test against ints within valid [0, 12] horizon range
        test_horizons = [0, 5]
        for test_horizon in test_horizons:
            # Get horizon date value
            test_horizon_date = get_horizon(test_history, "3mo", test_horizon)
            # Get end date from test_history
            test_history_end_date = (test_history.index[-1]).strftime("%Y-%m-%d")
            # Get difference in months
            m_diff = abs(int(test_horizon_date[5:7]) - int(test_history_end_date[5:7]))
            # Get difference in days
            d_diff = abs(int(test_horizon_date[8:]) - int(test_history_end_date[8:]))
            days_per_month = 30
            # Combine month and day differences to get total difference in days
            total_diff = m_diff * days_per_month + d_diff
            # Calculate expected difference in days between test_history_end_date and test_horizon_date
            expected_diff = test_horizon * days_per_month

            # Confirm difference approximates expected time range
            self.assertTrue(
                abs(total_diff - expected_diff) <= 7,
                f"Error: invalid horizon for '{test_horizon}'",
            )

        # Test against values outside valid [0, 12] horizon range
        test_horizons = [-2, 15]
        for test_horizon in test_horizons:
            # Get horizon date value
            test_horizon_date = get_horizon(test_history, "3mo", test_horizon)

            # Negative horizons should be set to 0
            if test_horizon < 0:
                self.assertTrue(
                    test_horizon_date == (test_history.index[-1]).strftime("%Y-%m-%d"),
                    f"Error: invalid output for negative horizon value '{test_horizon}'",
                )

            # Horizons > 12 should be set to 12
            elif test_horizon > 12:
                test_history_end_date = (test_history.index[-1]).strftime("%Y-%m-%d")
                y_diff = int(test_horizon_date[:4]) - int(test_history_end_date[:4])
                m_diff = int(test_horizon_date[5:7]) - int(test_history_end_date[5:7])
                d_diff = int(test_horizon_date[8:]) - int(test_history_end_date[8:])
                # Confirm horizon date is approximately 1 year ahead of test_history_end_date
                self.assertTrue(
                    y_diff == 1,
                    f"Error: invalid output for > 12 month horizon value '{test_horizon}'",
                )
                self.assertTrue(
                    m_diff == 0,
                    f"Error: invalid output for > 12 month horizon value '{test_horizon}'",
                )
                self.assertTrue(
                    abs(d_diff) <= 5,
                    f"Error: invalid output for > 12 month horizon value '{test_horizon}'",
                )

    def test_get_earnings_dates(self):
        # Set default session
        new_session = requests.Session()

        # Test stock with earnings dates
        ticker_label = "AAPL"
        test_ticker = get_ticker(ticker_label, current_session=new_session)
        # Get history
        test_history = get_history(test_ticker, period="1y", interval="1wk")
        # Get horizon date value
        test_horizon = get_horizon(test_history, "3mo", horizon_months=3)
        # Get earnings dates
        test_earnings = get_earnings_dates(test_ticker, test_history, test_horizon)

        self.assertTrue(
            isinstance(test_earnings, list),
            f"Error: invalid object type returned by get_earnings_dates for '{ticker_label}'",
        )
        self.assertTrue(
            isinstance(test_earnings[0], str),
            f"Error: invalid element type in earnings_dates list for '{ticker_label}'",
        )

        # Test for security with no earnings dates
        ticker_label = "SPY"
        test_ticker = get_ticker(ticker_label, current_session=new_session)
        # Get history
        test_history = get_history(test_ticker, period="1y", interval="1wk")
        # Get horizon date value
        test_horizon = get_horizon(test_history, "3mo", horizon_months=3)
        # Get earnings dates
        test_earnings = get_earnings_dates(test_ticker, test_history, test_horizon)

        self.assertTrue(
            isinstance(test_earnings, list),
            f"Error: invalid object type returned by get_earnings_dates for '{ticker_label}'",
        )
        self.assertTrue(
            test_earnings == [],
            f"Error: earnings_dates list not empty for '{ticker_label}'",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

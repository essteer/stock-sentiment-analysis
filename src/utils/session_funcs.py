import os
import requests
from dotenv import load_dotenv
from masquer import masq

# Load dotenv environment
load_dotenv()
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")


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
    header = masq(ua=True, rf=True)
    # Assign values to session header
    session.headers["User-Agent"] = header["User-Agent"]
    session.headers["Referer"] = header["Referer"]
    session.headers["Upgrade-Insecure-Requests"] = "1"

    if news_api:
        session.headers["X-Api-Key"] = NEWS_API_KEY

    return session

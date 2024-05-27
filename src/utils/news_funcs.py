# -*- coding: utf-8 -*-
import os
import time
import pandas as pd
from dotenv import load_dotenv
import spacy

# spacy_transformers required for transformer model
import spacy_transformers  # noqa: F401
from utils.session_funcs import get_session

# Load dotenv environment
load_dotenv()
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# ===============================================================
# Functions to call and process News API data
# ===============================================================


def get_news(short_name: str) -> tuple[dict, str]:
    """
    Makes call to News API and returns response data

    Parameters
    ----------
    short_name : str | NOTE: output of utils.data_funcs.get_short_name()
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
    domains_1 = "aljazeera.com,bbc.com,biztoc.com,businessinsider.com,cnn.com,etfdailynews.com,forbes.com,indiatimes.com,"
    domains_2 = "investing.com,marketwatch.com,marketscreener.com,qz.com,seekingalpha.com,wsj.com,washingtonpost.com"
    domains = domains_1 + domains_2
    # Compile query string
    query_string = {"q": query, "language": "en", "domains": domains}

    # Loop with short delay to handle one-off API errors
    for i in range(3):
        try:
            # Get new session for API call
            news_session = get_session(news_api=True)
            # Make API call
            response = news_session.get(
                base_url, headers=news_session.headers, params=query_string
            )
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
    data : dict | NOTE: output of utils.news_funcs.get_news()
        Dictionary of JSON response from News API call

    query : str | NOTE: output of utils.news_funcs.get_news()
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
    aggregate_sentiment = {k: (sum(v) / len(v)) for k, v in sentiment_dict.items()}

    return aggregate_sentiment


def get_rolling_averages(sent_data: dict) -> pd.DataFrame:
    """
    Creates DataFrame of predicted sentiments organised with date
    and rolling averages across time windows

    Parameters
    ----------
    sent_data : dict | NOTE: output of utils.news_funcs.get_nlp_predictions()
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

import os
import requests
from dotenv import load_dotenv

load_dotenv() 

def get_news_data(ticker: str):
    key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={key}"
    r = requests.get(url)
    data = r.json()

    return data
# news_retriever.py

import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Optional, Dict, Any

from news import News 

load_dotenv()
date_format = "%Y%m%dT%H%M"

def get_news_data(ticker: str, time_from: datetime, time_to: datetime) -> List[News]:
    raw_data = fetch_raw_data(ticker, time_from, time_to)
    
    if not raw_data:
        return []
        
    return process_api_response(raw_data)

def fetch_raw_data(ticker: str, time_from: datetime, time_to: datetime) -> Optional[Dict[str, Any]]:
    url = build_url(ticker, time_from, time_to)
    
    if not url:
        return None
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error performing HTTP request: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: API did not return valid JSON response.")
        return None

def build_url(ticker: str, time_from: datetime, time_to: datetime) -> Optional[str]:
    key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    
    if not key:
        print("ERROR: ALPHA_VANTAGE_API_KEY not found in .env.")
        return None

    time_from_param = time_from.strftime(date_format)
    time_to_param = time_to.strftime(date_format)
    
    url = (
        f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
        f"&tickers={ticker}&apikey={key}"
        f"&time_from={time_from_param}&time_to={time_to_param}"
    )
    return url

def process_api_response(data: Dict[str, Any]) -> List[News]:
    raw_feed: Optional[List[dict]] = data.get("feed")
    
    if not raw_feed:
        return []
        
    news_list: List[News] = []
    
    for item in raw_feed:
        title = item.get("title", "Title Not Available")
        summary = item.get("summary", "Summary Not Available")
        published = item.get("time_published", "Date Not Available") 

        news_item = News(
            title=title,
            published_date=published,
            summary=summary
        )
        news_list.append(news_item)
        
    return news_list
# main.py

from ia_analisis import analyze_news_with_gemini
from news_retriever import get_news_data
from datetime import datetime, time
from news import News 

if __name__ == "__main__":
    ticker = "ASTS"
    
    time_from = datetime(2025, 10, 20, 0, 0, 0)
    time_to = datetime.now()
    
    news_list: list[News] = get_news_data(ticker, time_from, time_to)
    
    if not news_list:
        print(f"\n[WARNING]: No news items found for {ticker} in the specified range.")
        exit()
    
    print(f"\n--- Processing {len(news_list)} News Items for {ticker} ---")

    for i, news_item in enumerate(news_list):
        print(f"\n\n[ANALYSIS OF NEWS ITEM {i+1} of {len(news_list)}]")
        print(f"Title: {news_item.title}")
        
        summary_to_analyze = news_item.summary
        
        analysis_result = analyze_news_with_gemini(ticker, summary_to_analyze)

        if analysis_result:
            sentiment = analysis_result.get('SENTIMENT', 'Read Error')
            justification = analysis_result.get('JUSTIFICATION', 'Not Available')

            print("\n--- AI SENTIMENT REPORT ---")
            print(f"CLASSIFIED SENTIMENT: **{sentiment}**")
            print(f"JUSTIFICATION: {justification}")
            print("---------------------------")
        else:
            print("\n[FAILURE] Could not get AI analysis for this news item.")
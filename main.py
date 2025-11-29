from ia_analisis import analyze_news_with_gemini
from news_retriever import get_news_data

if __name__ == "__main__":
    ticker = "AAPL"
    
    news_data = get_news_data(ticker)
    
    if 'feed' in news_data and news_data['feed']:
        news_text_for_analysis = news_data['feed'][0].get('summary', 'No summary available.')
    else:
        news_text_for_analysis = "Apple just announced record Q4 earnings exceeding expectations."
        print("\n[ADVERTENCIA]: Usando texto de noticia de ejemplo. La API de AlphaVantage podría no haber devuelto resultados o el formato es inesperado.")

    analysis_result = analyze_news_with_gemini(ticker, news_text_for_analysis)

    if analysis_result:
        sentiment = analysis_result.get('SENTIMENT', 'Read Error')
        justification = analysis_result.get('JUSTIFICATION', 'Not Available')

        print("\n--- AI SENTIMENT REPORT ---")
        print(f"STOCK ANALYZED: {ticker}")
        print(f"CLASSIFIED SENTIMENT: **{sentiment}**")
        print(f"JUSTIFICATION: {justification}")
        print("----------------------------")
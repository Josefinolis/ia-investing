import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

try:
    client = genai.Client()
except Exception as e:
    print("FATAL ERROR: Could not initialize the Gemini client.")
    print("Ensure the GEMINI_API_KEY variable is set in your .env file.")
    exit()

def analyze_news_with_gemini(ticker: str, news_text: str):
    prompt = f"""
Act as a quantitative market analyst specialized in short-term trading. 
Evaluate the news text provided about the stock {ticker} to classify its sentiment and potential short-term price impact.

Format the response strictly as a JSON object with two fields:
1. "SENTIMENT" (Use only one of these categories: 'Highly Negative', 'Negative', 'Neutral', 'Positive', 'Highly Positive').
2. "JUSTIFICATION" (A concise 1-2 sentence summary explaining the main reason for the impact).

TEXT TO ANALYZE:
---
{news_text}
---
"""

    config = types.GenerateContentConfig(
        response_mime_type="application/json"
    )

    print(f"✅ Analyzing news for {ticker} using Gemini...")

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=config,
        )

        return json.loads(response.text)

    except json.JSONDecodeError:
        print("\n[CRITICAL ERROR] The AI did not return valid JSON. Check the prompt format.")
        return None
    except Exception as e:
        print(f"\n[ERROR] An issue occurred during API execution: {e}")
        return None

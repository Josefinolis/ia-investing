import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ==========================================================
# 1. INITIAL CONFIGURATION AND AUTHENTICATION
# ==========================================================

# Load the API key from the .env file into system environment variables
load_dotenv() 

try:
    # The client automatically initializes by looking for the GEMINI_API_KEY
    client = genai.Client()
except Exception as e:
    print("FATAL ERROR: Could not initialize the Gemini client.")
    print("Ensure the GEMINI_API_KEY variable is set in your .env file.")
    exit()

# ==========================================================
# 2. INPUT DATA AND STRATEGIC PROMPT
# ==========================================================

# Define the stock and the news text your system would scrape
STOCK_TICKER = "PRL"
NEWS_TEXT = """
Propel Holdings (PRL) today announced quarterly earnings that beat analyst expectations by 15%, 
driven by the successful expansion of its digital platform into new European markets, 
suggesting strong revenue growth for the upcoming fiscal year.
"""

# The prompt instructs the AI to act as a quantitative analyst, focusing on impact and format
ANALYSIS_PROMPT = f"""
Act as a quantitative market analyst specialized in short-term trading. 
Evaluate the news text provided about the stock {STOCK_TICKER} to classify its sentiment and potential short-term price impact.

Format the response strictly as a JSON object with two fields:
1. "SENTIMENT" (Use only one of these categories: 'Highly Negative', 'Negative', 'Neutral', 'Positive', 'Highly Positive').
2. "JUSTIFICATION" (A concise 1-2 sentence summary explaining the main reason for the impact).

TEXT TO ANALYZE:
---
{NEWS_TEXT}
---
"""

# ==========================================================
# 3. API CALL AND PROCESSING
# ==========================================================

# Configuration to force the output to be JSON (CRITICAL for automation)
config = types.GenerateContentConfig(
    response_mime_type="application/json"
)

print(f"✅ Analyzing news for {STOCK_TICKER} using Gemini...")

try:
    # Call the fast and efficient model (flash)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=ANALYSIS_PROMPT,
        config=config,
    )

    # Convert the JSON string response into a Python dictionary
    analysis_json = json.loads(response.text)

    # ==========================================================
    # 4. TRADING LOGIC AND OUTPUT
    # ==========================================================

    sentiment = analysis_json.get('SENTIMENT', 'Read Error')
    justification = analysis_json.get('JUSTIFICATION', 'Not Available')

    print("\n--- AI SENTIMENT REPORT ---")
    print(f"STOCK ANALYZED: {STOCK_TICKER}")
    print(f"CLASSIFIED SENTIMENT: **{sentiment}**")
    print(f"JUSTIFICATION: {justification}")
    print("----------------------------")

except json.JSONDecodeError:
    print("\n[CRITICAL ERROR] The AI did not return valid JSON. Check the prompt format.")
except Exception as e:
    print(f"\n[ERROR] An issue occurred during execution: {e}")
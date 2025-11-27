import os
from google import genai
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv() 

try:
    # The client automatically looks for the GEMINI_API_KEY environment variable.
    client = genai.Client()
    
except Exception as e:
    print("Error initializing Gemini client. Make sure your API key is in the .env file.")
    print(f"Details: {e}")
    exit()

# --- Core API Call ---
print("Sending test prompt to Gemini...")

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents="Explain how the internet works in one short paragraph.",
)

# Print the response text
print("\n--- AI Response ---")
print(response)
print("-------------------")


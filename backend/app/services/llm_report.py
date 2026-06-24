import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_ai_risk_report(standard_report: str)-> str:
    if not GEMINI_API_KEY:
        return (
            "Gemini API Key is not configured. "
            "Showing the standard report:\n\n"
            + standard_report
        )
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
        You are a financial risk analyst.

        Rewrite the following portfolio risk report into a clear executive-style report.
        Keep it concise, professional, and suitable for a dashboard.
        Do not invent numbers. Only use the figures provided.

        Report:
        {standard_report}
        """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text
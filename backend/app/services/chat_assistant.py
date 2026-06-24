import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def answer_portfolio_question(question: str, context: dict) -> str:
    if not GEMINI_API_KEY:
        return "Gemini API key is not configured."

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are RiskLens AI, a financial risk analysis assistant.

Answer the user's question using only the portfolio context provided.
Do not invent data. Be clear, concise, and practical.

Portfolio Context:
{context}

User Question:
{question}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
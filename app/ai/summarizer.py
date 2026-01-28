import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_VERSION = "gpt-4o-mini-v1"

def summarize_email(body: str) -> dict:
    """
    Generates a short, neutral summary for an email.
    """

    if not body or len(body.strip()) < 30:
        return {
            "summary": None,
            "model_version": MODEL_VERSION,
            "reason": "Email body too short to summarize"
        }

    prompt = f"""
You are an email summarization system.

Summarize the email in **one or two short sentences**.
Rules:
- Be neutral and factual
- Do NOT add advice
- Do NOT add urgency
- Do NOT add interpretation
- Do NOT exceed 25 words
- Return ONLY valid JSON

JSON format:
{{
  "summary": "<short summary>"
}}

Email:
\"\"\"{body}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You summarize emails for an inbox UI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=80
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return {
            "summary": result.get("summary"),
            "model_version": MODEL_VERSION,
            "reason": "success"
        }

    except Exception as e:
        return {
            "summary": None,
            "model_version": "fallback-v1",
            "reason": f"summarization failed: {str(e)}"
        }

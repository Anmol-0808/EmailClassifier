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
You are an email understanding system for an AI inbox.

Your task:
1. Summarize the email in **15–25 words**, focusing on intent.
2. Detect whether the email content references or implies:
   - charts
   - graphs
   - tables
   - numerical trends
   - structured lists or metrics
3. If such elements are present, briefly describe **what they represent**.
4. If no such elements exist, explicitly say so.

STRICT RULES:
- Base your response ONLY on the provided text.
- Do NOT assume visuals unless clearly implied by text.
- Do NOT add advice, urgency, or interpretation.
- Do NOT exceed word limits.
- Do NOT hallucinate charts or data.
- Return ONLY valid JSON.

JSON format:
{{
  "summary": "<15–25 word neutral summary>",
  "has_structured_data": true | false,
  "structured_data_description": "<short description or null>"
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
    "has_structured_data": result.get("has_structured_data"),
    "structured_data_description": result.get("structured_data_description"),
    "model_version": MODEL_VERSION,
    "reason": "success"
}


    except Exception as e:
        return {
    "summary": None,
    "has_structured_data": False,
    "structured_data_description": None,
    "model_version": "fallback-v1",
    "reason": f"summarization failed: {str(e)}"
}


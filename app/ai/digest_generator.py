import os
import json
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from app.models.email import Email

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_VERSION = "gpt-4o-mini-v1"


def generate_digest(
    emails: List[Email],
    range_str: str
) -> dict:
    """
    Generate an inbox digest for a given time window.
    """

    if not emails:
        return {
            "digest": f"No emails found in the last {range_str}.",
            "model_version": MODEL_VERSION
        }

    email_blocks = []

    for e in emails:
        email_blocks.append(
            f"""
Category: {e.ai_email_type}
Confidence: {e.confidence_score}
Content:
{e.body}
""".strip()
        )

    joined_context = "\n\n---\n\n".join(email_blocks)

    prompt = f"""
You are an inbox intelligence system.

You are analyzing emails from the last {range_str}.

Your task:
- Identify key themes and patterns
- Group insights by category
- Highlight urgent or recurring issues
- Ignore greetings, signatures, and noise

Rules:
- Do NOT summarize emails one by one
- Do NOT repeat email content
- Produce 4–6 concise, insight-driven bullet points
- Neutral, analytical tone
- Return ONLY valid JSON

JSON format:
{{
  "digest": "<digest text>"
}}

Emails:
{joined_context}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate inbox intelligence digests."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=250
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    return {
        "digest": result["digest"],
        "model_version": MODEL_VERSION
    }

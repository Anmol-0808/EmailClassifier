import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_VERSION = "gpt-4o-mini-v1"


def generate_digest(summaries: list, categories: list) -> dict:
    """
    Generates a time-window inbox digest.
    Safe, deterministic, production-ready.
    """

    if not summaries:
        return {
            "digest": "No emails found for this time period.",
            "model_version": MODEL_VERSION
        }

    joined_context = "\n".join(
        f"- [{cat}] {summary}"
        for summary, cat in zip(summaries, categories)
    )

    prompt = f"""
You are an inbox intelligence system.

Based on the following email summaries, extract patterns and trends.

Rules:
- 4 to 6 bullet points
- No email-by-email repetition
- Neutral, analytical tone
- Focus on patterns
- RETURN ONLY JSON

JSON format:
{{
  "digest": "<digest text>"
}}

Email summaries:
{joined_context}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate inbox intelligence digests."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=250
        )

        content = response.choices[0].message.content.strip()

        result = json.loads(content)

        return {
            "digest": result.get("digest", "Digest could not be generated."),
            "model_version": MODEL_VERSION
        }

    except Exception as e:
       
        return {
            "digest": "AI digest generation failed. Please retry later.",
            "model_version": "fallback-v1"
        }

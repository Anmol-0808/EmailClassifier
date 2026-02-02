import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_VERSION = "gpt-4o-mini-v1"


def generate_digest(summaries: list, categories: list) -> dict:
    email_count = len(summaries)

    if not summaries:
        return {
            "summary": "No emails found for this time period.",
            "email_count": 0,
            "model": MODEL_VERSION,
        }

    joined_context = "\n".join(
        f"- [{cat}] {summary}"
        for summary, cat in zip(summaries, categories)
    )

    prompt = f"""
You are an inbox intelligence system.

Based on the following email summaries, extract high-level patterns and trends.

Rules:
- 3 to 5 concise bullet points
- No email-by-email repetition
- Neutral, analytical tone
- Focus on trends and intent
- RETURN ONLY JSON

JSON format:
{{
  "summary": "<digest text>"
}}

Email summaries:
{joined_context}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You generate concise inbox intelligence digests."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=250
        )

        content = response.choices[0].message.content.strip()

        # 🔒 Defensive JSON extraction
        start = content.find("{")
        end = content.rfind("}") + 1

        if start == -1 or end == -1:
            raise ValueError("No JSON object found")

        result = json.loads(content[start:end])
        summary = result.get("summary", "").strip()

        if not summary:
            summary = "No significant patterns were detected in the selected emails."

        return {
            "summary": summary,
            "email_count": email_count,
            "model": MODEL_VERSION,
        }

    except Exception as e:
        print("DIGEST ERROR:", e)

        return {
            "summary": "AI digest generation failed. Please retry later.",
            "email_count": email_count,
            "model": "fallback-v1",
        }


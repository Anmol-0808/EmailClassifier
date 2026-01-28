import os
import json 
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


ALLOWED_TYPES = {"newsletter", "support", "marketing"}

def classify_email(email: str) -> dict:
    """
    Real LLM-powered email classifier.
    Returns deterministic, structured output.
    """

    prompt = f"""
You are a strict email classification system for a backend product.

Your task is to classify the email into EXACTLY ONE of the following categories:

1. newsletter
   - Informational or recurring updates
   - Blog posts, product updates, announcements
   - No direct selling or urgency

2. marketing
   - Promotional or sales-driven content
   - Discounts, offers, pricing, upgrades
   - Strong call-to-action (buy, upgrade, limited offer)

3. support
   - User asking for help or reporting an issue
   - Account problems, bugs, errors, requests
   - Conversational or problem-solving tone

Rules:
- Choose ONLY ONE category
- Do NOT invent new categories
- If unsure between newsletter and marketing:
  - choose marketing ONLY if there is a sales or conversion intent
- If the email asks for help or reports a problem, ALWAYS choose support
- Return ONLY valid JSON
- No explanations outside JSON
- Confidence must be a number between 0 and 1

Return JSON in this format:
{{
  "email_type": "<newsletter | support | marketing>",
  "confidence": <float>,
  "reason": "<short explanation referencing the rules above>"
}}

Email content:
\"\"\"{email}\"\"\"
"""

    try:
        response=client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You classify emails for a backend."},
                {"role":"user","content":prompt}
            ],
            temperature=0.2,
            max_tokens=150
        )

        content =response.choices[0].message.content
        result=json.loads(content)

        email_type=result.get("email_type")
        confidence=float(result.get("confidence",0))
        reason=result.get("reason","")


        if(email_type) not in ALLOWED_TYPES:
            raise ValueError("Invalid email type returned by model")
        
        return{
            "email_type":email_type,
            "confidence":confidence,
            "reason":reason,
            "model_version":"gpt-4o-mini-v1"
        }
    
    except Exception as e:
        return{
            "email_type":"support",
            "confidence":0.0,
            "reason":f"AI classification model failed:{str(e)}",
            "model_version":"fallback-v1"
        }

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
You are an email classification system.

Classify the email into ONE of these categories:
- newsletter
- support
- marketing

Rules:
- Return ONLY valid JSON
- No extra text
- Confidence must be a number between 0 and 1

JSON format:
{{
  "email_type": "<one of newsletter|support|marketing>",
  "confidence": <float>,
  "reason": "<short explanation>"
}}

Email:
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

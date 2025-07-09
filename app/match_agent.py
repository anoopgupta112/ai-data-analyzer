# match_agent.py

import os
from dotenv import load_dotenv
import google.generativeai as genai

import json
import re
from typing import Dict, Any

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

def evaluate_resume_against_jd(jd: str, resume_text: str):
    prompt = f"""
You are a professional HR evaluator. Your task is to strictly match the candidate's resume against a Job Description.

If the Job Description is too short, missing, or meaningless (less than 10 valid words), set `percent_match` to 0, and provide negatives explaining the issue.

Respond ONLY with a JSON object using the schema:

- percent_match: integer (0–100)
- positive: array of objects with:
    - description: string
    - keywords: array of strings
- negative: array of objects with:
    - description: string
    - keywords: array of strings
- description: overall summary of fit

Reject vague, unclear, or unrelated JD text.

---

Job Description:
{jd}

---

Resume Text:
{resume_text}
"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    print(response.text)
    data = extract_json_from_text(response.text)
    return data


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Attempts to extract and fix a partial JSON block from text.
    Returns a normalized dictionary with required keys.
    """
    # Extract the first JSON-like block
    try:
        json_str = re.search(r'\{[\s\S]*\}', text).group(0)
    except AttributeError:
        raise ValueError("No JSON block found.")

    # Optional: try to balance brackets if the JSON is cut off
    open_curly = json_str.count('{')
    close_curly = json_str.count('}')
    if open_curly > close_curly:
        json_str += '}' * (open_curly - close_curly)
    open_square = json_str.count('[')
    close_square = json_str.count(']')
    if open_square > close_square:
        json_str += ']' * (open_square - close_square)

    try:
        raw = json.loads(json_str)
    except json.JSONDecodeError as e:
        print("[ERROR] JSON parse failed:", e)
        print("Original text:\n", json_str)
        raise ValueError("Failed to parse corrected JSON.")

    # Normalize output
    percent = raw.get("percent_match", 0)
    if isinstance(percent, str):
        percent = re.sub(r"[^\d]", "", percent)
    try:
        percent = int(percent)
    except:
        percent = 0

    return {
        "percent_match": percent,
        "positive": raw.get("positive", []),
        "negative": raw.get("negative", []),
        "description": raw.get("description", "N/A")
    }
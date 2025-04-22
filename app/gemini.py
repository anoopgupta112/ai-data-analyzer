import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def get_fields_from_gemini(prompt: str) -> List[Dict[str, Any]]:
    # TODO: Implement Gemini Flash 2.0 API call
    # For now, return demo fields based on prompt keywords
    prompt = prompt.lower()
    fields = []
    if "email" in prompt:
        fields.append({"name": "email", "label": "Email", "type": "email"})
    if "name" in prompt:
        fields.append({"name": "name", "label": "Name", "type": "text"})
    if "no" in prompt or "number" in prompt or "phone" in prompt:
        fields.append({"name": "phone", "label": "Phone Number", "type": "tel"})
    if "address" in prompt:
        fields.append({"name": "address", "label": "Address", "type": "text"})
    if not fields:
        fields.append({"name": "data", "label": "Data", "type": "text"})
    return fields

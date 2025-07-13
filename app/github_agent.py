import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optional: for higher rate limits

genai.configure(api_key=GEMINI_API_KEY)

GITHUB_API = "https://api.github.com"


def fetch_github_code(url: str, max_lines: int = 200) -> str:
    """
    Fetch up to max_lines of code from a GitHub repo (public, or with token).
    """
    import re
    m = re.match(r"https://github.com/([^/]+)/([^/]+)(/|$)", url)
    if not m:
        return ""
    owner, repo = m.group(1), m.group(2)
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    # List files in repo (root only for simplicity)
    r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/contents", headers=headers)
    if r.status_code != 200:
        return ""
    files = r.json()
    code = []
    for f in files:
        if f["type"] == "file" and f["name"].endswith(('.py','.js','.ts','.java','.cpp','.c','.go','.rb','.php','.rs','.swift','.kt','.scala','.cs')):
            raw_url = f["download_url"]
            fr = requests.get(raw_url, headers=headers)
            if fr.status_code == 200:
                lines = fr.text.splitlines()
                code.extend(lines[:max_lines-len(code)])
                if len(code) >= max_lines:
                    break
    return "\n".join(code)


def generate_questions_from_github(github_urls: List[str], num_questions: int = 10) -> Dict:
    """
    Fetch code from all GitHub URLs, aggregate, and generate questions and summary.
    """
    all_code = []
    for url in github_urls:
        code = fetch_github_code(url)
        if code:
            all_code.append(code)
    code_text = "\n\n".join(all_code)
    if not code_text:
        return {"questions": [], "summary": "No code found."}
    prompt = f"""
You are a technical interviewer. Read the following code (from multiple GitHub repos, max 200 lines per file). 
Generate {num_questions} insightful technical questions about the codebase, and a short summary (like a resume) of the codebase's purpose and technologies.

Respond ONLY with a JSON object with keys:
- questions: array of strings
- summary: string

---
CODE:
{code_text}
---
"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    import re, json
    try:
        json_str = re.search(r'\{[\s\S]*\}', response.text).group(0)
        data = json.loads(json_str)
        return {"questions": data.get("questions", []), "summary": data.get("summary", "")}
    except Exception as e:
        return {"questions": [], "summary": f"Error: {e}"} 
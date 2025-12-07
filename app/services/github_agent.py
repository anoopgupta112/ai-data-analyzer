import json
import os
import re
from typing import Dict, List

import requests
from dotenv import load_dotenv

from app.services.openrouter_client import OpenRouterError, complete_chat

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optional: for higher rate limits

GITHUB_API = "https://api.github.com"


def _complete_prompt(prompt: str) -> str:
    try:
        return complete_chat(prompt)
    except OpenRouterError as exc:
        raise ValueError(f"OpenRouter request failed: {exc}") from exc


def fetch_github_code(url: str, max_lines: int = 200) -> str:
    """
    Fetch up to max_lines of code from a GitHub repo (public, or with token).
    """
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
Generate {num_questions} insightful technical basic questions about the codebase and the code not be asking like from this file
 you have used this so what it works in your project,
 make question common like suppose a person use for loop then you should not be asking like why you used for loop in you app.py
  instead of this ask like when we use for loop (general question), and a short summary (like a resume) of the codebase's purpose and technologies.
  don't use like in this project, in this file, or in this repo make it general question.
  and ask only basic questions


Respond ONLY with a JSON object with keys:
- questions: array of strings
- summary: string

---
CODE:
{code_text}
---
"""
    response_text = _complete_prompt(prompt)
    try:
        json_str = re.search(r'\{[\s\S]*\}', response_text).group(0)
        data = json.loads(json_str)
        return {"questions": data.get("questions", []), "summary": data.get("summary", "")}
    except Exception as e:
        return {"questions": [], "summary": f"Error: {e}"}

def generate_questions_from_jd(jd: str, num_questions: int = 10) -> Dict:
    """
    Generate questions based on the Job Description when no GitHub links are found.
    """
    prompt = f"""
You are a technical interviewer. Read the following Job Description.
Generate {num_questions} insightful technical basic questions based on the requirements and skills mentioned in the JD.
Make the questions general (e.g., "When would you use a microservices architecture?" instead of "Why did you use microservices in this project?").
Also provide a short summary of the key technical requirements from the JD.

Respond ONLY with a JSON object with keys:
- questions: array of strings
- summary: string

---
Job Description:
{jd}
---
"""
    response_text = _complete_prompt(prompt)
    try:
        json_str = re.search(r'\{[\s\S]*\}', response_text).group(0)
        data = json.loads(json_str)
        return {"questions": data.get("questions", []), "summary": data.get("summary", "")}
    except Exception as e:
        return {"questions": [], "summary": f"Error: {e}"}

def extract_experience_section(resume_text: str) -> str:
    """
    Extract the 'Experience' or 'Work History' section from the resume text using LLM.
    """
    print(f"[DEBUG] Extracting experience from {len(resume_text)} chars...")
    prompt = f"""
You are a resume parser. Extract the "Experience" or "Work History" section from the following resume text.
Return ONLY the text content of that section. If not found, return an empty string.

---
Resume Text:
{resume_text}
---
"""
    try:
        response_text = _complete_prompt(prompt)
        extracted = response_text.strip()
        print(f"[DEBUG] Extracted experience length: {len(extracted)}")
        
        if not extracted:
            print("[DEBUG] Experience section not found. Using full resume text as fallback.")
            return resume_text[-2000:] # Fallback to last 2000 chars as a heuristic or just return all
            
        return extracted
    except Exception as e:
        print(f"[ERROR] extract_experience_section failed: {e}")
        return ""

def generate_questions_from_experience(experience_text: str, num_questions: int = 5) -> Dict:
    """
    Generate questions based on the candidate's experience.
    """
    if not experience_text:
        return {"questions": [], "summary": ""}
        
    print(f"[DEBUG] Generating questions from experience text ({len(experience_text)} chars)...")
    prompt = f"""
You are a technical interviewer. Read the following Experience section from a candidate's resume.
Generate {num_questions} insightful technical questions based on the projects and roles described.
Focus on the technologies and challenges mentioned.
Make the questions specific to their experience but framed as technical inquiries (e.g., "You mentioned working with Kafka. How did you handle message ordering?").
Also provide a short summary of their key experience highlights.

Respond ONLY with a JSON object with keys:
- questions: array of strings (questions should be easy to answer - just a basic level of questions in simple words)
- summary: string

---
Experience Section:
{experience_text}
---
"""
    response_text = _complete_prompt(prompt)
    try:
        json_str = re.search(r'\{[\s\S]*\}', response_text).group(0)
        data = json.loads(json_str)
        print(f"[DEBUG] Generated {len(data.get('questions', []))} questions.")
        return {"questions": data.get("questions", []), "summary": data.get("summary", "")}
    except Exception as e:
        print(f"[ERROR] generate_questions_from_experience failed: {e}")
        return {"questions": [], "summary": f"Error: {e}"}

def extract_project_section(resume_text: str) -> str:
    """
    Extract the 'Projects' section from the resume text using LLM.
    """
    print(f"[DEBUG] Extracting projects from {len(resume_text)} chars...")
    prompt = f"""
You are a resume parser. Extract the "Projects" or "Academic Projects" or "Personal Projects" section from the following resume text.
Return ONLY the text content of that section. If not found, return an empty string.

---
Resume Text:
{resume_text}
---
"""
    try:
        response_text = _complete_prompt(prompt)
        extracted = response_text.strip()
        print(f"[DEBUG] Extracted projects length: {len(extracted)}")
        return extracted
    except Exception as e:
        print(f"[ERROR] extract_project_section failed: {e}")
        return ""

def generate_questions_from_projects(project_text: str) -> List[Dict]:
    """
    Generate questions for each project found in the text.
    Returns a list of dicts: [{'project_name': '...', 'questions': [], 'summary': '...'}]
    """
    if not project_text:
        return []
        
    print(f"[DEBUG] Generating questions from project text ({len(project_text)} chars)...")
    prompt = f"""
You are a technical interviewer. Read the following Projects section from a candidate's resume.
Identify each distinct project. For each project:
1. Extract the Project Name.
2. Write a short summary of the project.
3. Generate 3-5 basic, easy-to-answer technical questions specific to that project.

Respond ONLY with a JSON array of objects, where each object has:
- project_name: string
- summary: string
- questions: array of strings

---
Projects Section:
{project_text}
---
"""
    response_text = _complete_prompt(prompt)
    try:
        json_str = re.search(r'\[[\s\S]*\]', response_text).group(0)
        data = json.loads(json_str)
        print(f"[DEBUG] Generated questions for {len(data)} projects.")
        return data
    except Exception as e:
        print(f"[ERROR] generate_questions_from_projects failed: {e}")
        return []

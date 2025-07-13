import os
from app.services.ocr_engine import extract_text_from_pdf
from app.services.match_agent import evaluate_resume_against_jd
from .github_agent import generate_questions_from_github

def process_uploaded_pdfs(pdf_files: list, jd: str, save_dir: str) -> list:
    results = []

    for pdf in pdf_files:
        # Fix: Remove folder prefix in file name
        base_name = os.path.basename(pdf.filename)
        save_path = os.path.join(save_dir, base_name)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(pdf.file.read())

        resume_text, links = extract_text_from_pdf(save_path)
        match_report = evaluate_resume_against_jd(jd, resume_text)

        github_questions = []
        if links:
            import re
            github_links = [l['uri'] for l in links if isinstance(l, dict) and 'uri' in l and re.match(r'https://github.com/', l['uri'])]
            for gh_url in github_links:
                # If it's a user/org page, skip; only process repo links
                m = re.match(r'https://github.com/[^/]+/[^/]+', gh_url)
                if m:
                    qdata = generate_questions_from_github([gh_url], 10)
                    github_questions.append({
                        'repo': gh_url,
                        'questions': qdata.get('questions', []),
                        'summary': qdata.get('summary', '')
                    })
        results.append({
            "pdf_path": base_name,
            "match_report": match_report,
            "links": links,
            "github_questions": github_questions,
            "resume_text": resume_text
        })

    return results

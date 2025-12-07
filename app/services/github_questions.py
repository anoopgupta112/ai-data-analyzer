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
        
        # 1. GitHub Questions
        if links:
            import re
            github_links = [l['uri'] for l in links if isinstance(l, dict) and 'uri' in l and re.match(r'https://github.com/', l['uri'])]
            # Filter for repo links only
            repo_links = []
            for gh_url in github_links:
                if re.match(r'https://github.com/[^/]+/[^/]+', gh_url):
                    repo_links.append(gh_url)
            
            unique_repos = list(set(repo_links))
            for gh_url in unique_repos:
                qdata = generate_questions_from_github([gh_url], 10)
                if qdata.get('summary') == 'No code found.':
                    continue
                github_questions.append({
                    'repo': gh_url,
                    'questions': qdata.get('questions', []),
                    'summary': qdata.get('summary', ''),
                    'source': 'github'
                })

        # 2. Fallback: JD Questions (if no GitHub links found)
        if not github_questions:
            from .github_agent import generate_questions_from_jd
            jd_qdata = generate_questions_from_jd(jd, 10)
            if jd_qdata.get('questions'):
                github_questions.append({
                    'repo': 'Job Description',
                    'questions': jd_qdata.get('questions', []),
                    'summary': jd_qdata.get('summary', ''),
                    'source': 'jd'
                })

        # 3. Experience Questions (always try to extract)
        from .github_agent import extract_experience_section, generate_questions_from_experience
        experience_text = extract_experience_section(resume_text)
        if experience_text:
            exp_qdata = generate_questions_from_experience(experience_text, 5)
            if exp_qdata.get('questions'):
                github_questions.append({
                    'repo': 'Experience',
                    'questions': exp_qdata.get('questions', []),
                    'summary': exp_qdata.get('summary', ''),
                    'source': 'experience'
                })

        # 4. Project Questions (Resume Projects)
        from .github_agent import extract_project_section, generate_questions_from_projects
        project_text = extract_project_section(resume_text)
        if project_text:
            projects_data = generate_questions_from_projects(project_text)
            for p in projects_data:
                github_questions.append({
                    'repo': p.get('project_name', 'Project'),
                    'questions': p.get('questions', []),
                    'summary': p.get('summary', ''),
                    'source': 'project'
                })

        results.append({
            "pdf_path": base_name,
            "match_report": match_report,
            "links": links,
            "github_questions": github_questions,
            "resume_text": resume_text
        })

    return results

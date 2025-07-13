import os
from .ocr_engine import extract_text_from_pdf
from .match_agent import evaluate_resume_against_jd

def process_uploaded_pdfs(pdf_files: list, jd: str, save_dir: str) -> list:
    results = []

    for pdf in pdf_files:
        # Fix: Remove folder prefix in file name
        base_name = os.path.basename(pdf.filename)
        save_path = os.path.join(save_dir, base_name)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(pdf.file.read())

        resume_text, _ = extract_text_from_pdf(save_path)
        match_report = evaluate_resume_against_jd(jd, resume_text)

        results.append({
            "pdf_path": base_name,
            "match_report": match_report
        })

    return results

# ocr_engine.py

import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"[OCR ERROR] {pdf_path}: {e}")
    return text

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str):
    text = ""
    links_data = list()
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                # Extract visible text
                text += page.get_text()
                # Extract links
                links = page.get_links()
                for link in links:
                    if "uri" in link:
                        links_data += f"\n[LINK: {link['uri']}]\n"
    except Exception as e:
        print(f"[OCR ERROR] {pdf_path}: {e}")
    return text, links_data

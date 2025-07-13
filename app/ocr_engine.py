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
                    # Make a copy so we don't mutate the original
                    link_copy = link.copy()
                    for k, v in link_copy.items():
                        # Convert Rect or similar objects to a list of floats
                        if hasattr(v, 'is_rect') or type(v).__name__ == 'Rect':
                            link_copy[k] = list(v)
                    if "uri" in link_copy:
                        links_data.append(link_copy)
    except Exception as e:
        print(f"[OCR ERROR] {pdf_path}: {e}")
    return text, links_data

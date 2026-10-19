import pymupdf

MAX_PAGES = 200

def extract_pages(path) -> list[dict]:
    pages = []
    with pymupdf.open(path) as doc:
        if doc.page_count > MAX_PAGES:
            raise ValueError("Terlalu banyak halaman")
        for i, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if text:
                pages.append(
                    {
                        "page": i,
                        "text": text
                    }
                )
        return pages
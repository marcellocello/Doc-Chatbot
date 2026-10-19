import re

def _normalize(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\s*\n\s*", " ", text).strip()

def _split_sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+",  text) if s]

def chunk_pages(pages: list[dict], size: int = 800, overlap: int = 150) -> list[dict]:
    chunks = []

    def add(page, sentences):
        chunks.append(
            {
                "chunk_index": len(chunks),
                "page": page,
                "content": " ".join(sentences)
            }
        )
    for p in pages:
        sentences = _split_sentences(_normalize(p["text"]))
        current, length = [], 0

        for s in sentences:
            if current and length + len(s) + 1 > size:
                add(p["page"], current)
                tail, tail_len = [], 0
                for prev in reversed(current):
                    if tail_len + len(prev) > overlap:
                        break
                    tail.insert(0, prev)
                    tail_len += len(prev) + 1
                current, length = tail, tail_len
                
            current.append(s)
            length += len(s) + 1
        if current:
            add(p["page"], current)

    return chunks
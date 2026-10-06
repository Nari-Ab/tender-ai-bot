from typing import List
import re


class DocumentChunker:
    @staticmethod
    def chunk_tz(text: str, max_chunk_chars: int = 1500, overlap_chars: int = 200) -> List[str]:
        """
        Split a procurement specification or contract into semantically meaningful chunks.
        Prefers splitting by numbered section headings, paragraphs, and sentence boundaries.
        """
        if not text or not text.strip():
            return []

        # Split on double newlines or numbered sections like "1.", "1.1.", "Статья 5"
        raw_paragraphs = re.split(r'\n{2,}|\n(?=\d+\.\s|\d+\.\d+\.\s|Раздел\s|Статья\s)', text)
        chunks: List[str] = []
        current_chunk = ""

        for para in raw_paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 1 <= max_chunk_chars:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If a single paragraph is longer than max_chunk_chars, split by sentences
                if len(para) > max_chunk_chars:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    sub_chunk = ""
                    for s in sentences:
                        if len(sub_chunk) + len(s) + 1 <= max_chunk_chars:
                            sub_chunk = f"{sub_chunk} {s}".strip()
                        else:
                            if sub_chunk:
                                chunks.append(sub_chunk)
                            sub_chunk = s
                    if sub_chunk:
                        current_chunk = sub_chunk
                    else:
                        current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

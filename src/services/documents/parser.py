import io
import os
from typing import Union
from pypdf import PdfReader
from docx import Document
from src.core.logger import get_logger

logger = get_logger("document_parser")


class DocumentParser:
    @staticmethod
    def extract_text(file_input: Union[bytes, str, io.BytesIO], filename: str = "doc.txt") -> str:
        """Extract plain text from .txt, .pdf, or .docx file inputs."""
        ext = os.path.splitext(filename)[1].lower()
        logger.info(f"Extracting text from file '{filename}' (extension: {ext})")

        try:
            if ext in [".txt", ".md", ""]:
                if isinstance(file_input, bytes):
                    return file_input.decode("utf-8", errors="replace")
                elif isinstance(file_input, io.BytesIO):
                    return file_input.getvalue().decode("utf-8", errors="replace")
                elif isinstance(file_input, str) and os.path.exists(file_input):
                    with open(file_input, "r", encoding="utf-8", errors="replace") as f:
                        return f.read()
                return str(file_input)

            elif ext == ".pdf":
                stream = file_input if isinstance(file_input, (io.BytesIO, bytes)) else None
                if stream is None and isinstance(file_input, str) and os.path.exists(file_input):
                    reader = PdfReader(file_input)
                else:
                    bio = file_input if isinstance(file_input, io.BytesIO) else io.BytesIO(file_input)
                    reader = PdfReader(bio)

                pages_text = []
                for i, page in enumerate(reader.pages):
                    extracted = page.extract_text()
                    if extracted:
                        pages_text.append(extracted)
                return "\n\n".join(pages_text)

            elif ext in [".docx", ".doc"]:
                bio = file_input if isinstance(file_input, io.BytesIO) else io.BytesIO(file_input) if isinstance(file_input, bytes) else None
                doc = Document(file_input if bio is None else bio)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                return "\n".join(paragraphs)

            else:
                logger.warning(f"Unsupported extension {ext}, treating as UTF-8 text")
                if isinstance(file_input, bytes):
                    return file_input.decode("utf-8", errors="replace")
                return str(file_input)

        except Exception as e:
            logger.error(f"Error parsing document {filename}: {e}", exc_info=True)
            return f"Ошибка при чтении файла {filename}: {str(e)}"

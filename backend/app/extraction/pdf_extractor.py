"""
TRACE - PDF & Text Document Extractor
Extracts page-by-page text, blocks, and line snippets using PyMuPDF (fitz) or fallback.
"""

import os
from typing import Dict, List, Any

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

class DocumentExtractor:
    @staticmethod
    def extract(file_path: str) -> Dict[str, Any]:
        """
        Extracts raw text, pages, and structured snippets from a PDF or text file.
        Returns:
            {
                "raw_text": str,
                "page_count": int,
                "pages": List[Dict[str, Any]],  # each with page_num, text, lines
            }
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt" or ext == ".json":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            return {
                "raw_text": content,
                "page_count": 1,
                "pages": [{"page_number": 1, "text": content, "lines": lines}]
            }

        if ext == ".pdf":
            if PYMUPDF_AVAILABLE:
                try:
                    doc = fitz.open(file_path)
                    pages_data = []
                    full_text_parts = []

                    for page_idx in range(len(doc)):
                        page = doc[page_idx]
                        page_text = page.get_text("text")
                        page_lines = [l.strip() for l in page_text.split("\n") if l.strip()]
                        
                        pages_data.append({
                            "page_number": page_idx + 1,
                            "text": page_text,
                            "lines": page_lines
                        })
                        full_text_parts.append(page_text)

                    doc.close()
                    return {
                        "raw_text": "\n\n".join(full_text_parts),
                        "page_count": len(pages_data),
                        "pages": pages_data
                    }
                except Exception as e:
                    print(f"PyMuPDF error, trying fallback: {e}")

            if PYPDF_AVAILABLE:
                reader = PdfReader(file_path)
                pages_data = []
                full_text_parts = []
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    pages_data.append({
                        "page_number": idx + 1,
                        "text": text,
                        "lines": lines
                    })
                    full_text_parts.append(text)
                return {
                    "raw_text": "\n\n".join(full_text_parts),
                    "page_count": len(pages_data),
                    "pages": pages_data
                }

        if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
            if PYMUPDF_AVAILABLE:
                try:
                    doc = fitz.open(file_path)
                    pages_data = []
                    full_text_parts = []
                    for page_idx in range(len(doc)):
                        page = doc[page_idx]
                        page_text = page.get_text("text") or ""
                        page_lines = [l.strip() for l in page_text.split("\n") if l.strip()]
                        pages_data.append({
                            "page_number": page_idx + 1,
                            "text": page_text,
                            "lines": page_lines
                        })
                        full_text_parts.append(page_text)
                    doc.close()
                    return {
                        "raw_text": "\n\n".join(full_text_parts),
                        "page_count": max(1, len(pages_data)),
                        "pages": pages_data if pages_data else [{"page_number": 1, "text": "", "lines": []}]
                    }
                except Exception as e:
                    print(f"PyMuPDF image extract error: {e}")

            return {
                "raw_text": "",
                "page_count": 1,
                "pages": [{"page_number": 1, "text": "", "lines": []}]
            }

        # Fallback for plain text or unexpected formats
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {
            "raw_text": content,
            "page_count": 1,
            "pages": [{"page_number": 1, "text": content, "lines": content.splitlines()}]
        }

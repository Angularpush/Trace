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
    @staticmethod
    def split_pdf_pages(file_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """
        Splits a multi-page PDF into independent single-page PDF files and extracts text per page.
        Returns a list of dicts:
        [
            {
                "page_number": int,
                "file_path": str,
                "raw_text": str,
                "lines": List[str],
                "page_count": 1
            }
        ]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext != ".pdf":
            # Single non-PDF file
            single_ext = DocumentExtractor.extract(file_path)
            return [{
                "page_number": 1,
                "file_path": file_path,
                "raw_text": single_ext["raw_text"],
                "lines": single_ext["pages"][0]["lines"] if single_ext["pages"] else [],
                "page_count": 1
            }]

        out_dir = output_dir or os.path.dirname(file_path)
        os.makedirs(out_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        results = []

        if PYMUPDF_AVAILABLE:
            try:
                src_doc = fitz.open(file_path)
                total_pages = len(src_doc)

                for page_idx in range(total_pages):
                    page_num = page_idx + 1
                    page = src_doc[page_idx]
                    page_text = page.get_text("text") or ""
                    page_lines = [l.strip() for l in page_text.split("\n") if l.strip()]

                    # Save single page to separate PDF if multi-page
                    if total_pages > 1:
                        single_doc = fitz.open()
                        single_doc.insert_pdf(src_doc, from_page=page_idx, to_page=page_idx)
                        page_pdf_name = f"{base_name}_page_{page_num}.pdf"
                        page_pdf_path = os.path.join(out_dir, page_pdf_name)
                        single_doc.save(page_pdf_path)
                        single_doc.close()
                    else:
                        page_pdf_path = file_path

                    results.append({
                        "page_number": page_num,
                        "file_path": page_pdf_path,
                        "raw_text": page_text,
                        "lines": page_lines,
                        "page_count": 1
                    })

                src_doc.close()
                return results
            except Exception as e:
                print(f"[DocumentExtractor] PyMuPDF split error: {e}")

        if PYPDF_AVAILABLE:
            from pypdf import PdfWriter
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                page_text = page.extract_text() or ""
                page_lines = [l.strip() for l in page_text.split("\n") if l.strip()]

                if total_pages > 1:
                    writer = PdfWriter()
                    writer.add_page(page)
                    page_pdf_name = f"{base_name}_page_{page_num}.pdf"
                    page_pdf_path = os.path.join(out_dir, page_pdf_name)
                    with open(page_pdf_path, "wb") as f_out:
                        writer.write(f_out)
                else:
                    page_pdf_path = file_path

                results.append({
                    "page_number": page_num,
                    "file_path": page_pdf_path,
                    "raw_text": page_text,
                    "lines": page_lines,
                    "page_count": 1
                })
            return results

        # Fallback to standard extract
        single_ext = DocumentExtractor.extract(file_path)
        return [{
            "page_number": 1,
            "file_path": file_path,
            "raw_text": single_ext["raw_text"],
            "lines": single_ext["pages"][0]["lines"] if single_ext["pages"] else [],
            "page_count": 1
        }]

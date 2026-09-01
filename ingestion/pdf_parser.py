# ingestion/pdf_parser.py
"""
PDF parser for AMFI/SEBI regulatory documents.

Phase 2 will implement full parsing. This stub defines the interface.
"""
from pathlib import Path


def parse_pdf(pdf_path: str | Path) -> str:
    """
    Extract plain text from a PDF file.

    Args:
        pdf_path: Absolute or relative path to the PDF.

    Returns:
        Extracted text as a single string.
    """
    # TODO (Phase 2): implement using pdfplumber or PyMuPDF
    raise NotImplementedError("PDF parsing will be implemented in Phase 2.")

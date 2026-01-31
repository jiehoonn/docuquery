"""
app/services/text_extractor.py - Text Extraction Service

Extracts plain text from various document formats (PDF, DOCX, TXT).
This is the first step in the document processing pipeline.

Pipeline: Extract Text → Chunk → Embed → Store in Qdrant
          ^^^^^^^^^^^^
          (this file)

Supported formats:
- PDF: Uses PyPDF2 to read each page
- DOCX: Uses python-docx to read paragraphs
- TXT: Plain file read
"""

from docx import Document
from PyPDF2 import PdfReader


def extract_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        All text content from the PDF concatenated together

    Note:
        PyPDF2 extracts text page by page. Some PDFs (especially scanned
        documents) may not have extractable text - they would need OCR.
    """

    res = ""
    reader = PdfReader(file_path)

    # Iterate through each page and extract text
    for page in reader.pages:
        res += page.extract_text()
    return res


def extract_from_docx(file_path: str) -> str:
    """
    Extract text from a Microsoft Word (DOCX) file.

    Args:
        file_path: Path to the DOCX file

    Returns:
        All text content with paragraphs separated by newlines

    Note:
        This extracts paragraph text only. Tables, headers, footers,
        and text boxes are not included in this simple implementation.
    """

    doc = Document(file_path)
    # Each paragraph is a separate object, join them with new lines
    # Join them with new lines to preserve document structure
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])


def extract_from_txt(file_path: str) -> str:
    """
    Extract text from a plain text file.

    Args:
        file_path: Path to the TXT file

    Returns:
        The entire file contents as a string
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text(file_path: str) -> str:
    """
    Extract text from a file based on its extension.

    This is the main entry point for text extraction. It determines
    the file type and calls the appropriate extraction function.

    Args:
        file_path: Path to the document file

    Returns:
        Extracted text content as a string

    Raises:
        ValueError: If the file type is not supported

    Example:
        text = extract_text("uploads/tenant123/doc456/original.pdf")
    """
    # Get file extension (e.g., "report.pdf" -> "pdf")
    extension = file_path.rsplit(".", 1)[-1].lower()

    if extension == "pdf":
        return extract_from_pdf(file_path)
    elif extension == "txt":
        return extract_from_txt(file_path)
    elif extension == "docx":
        return extract_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {extension}")

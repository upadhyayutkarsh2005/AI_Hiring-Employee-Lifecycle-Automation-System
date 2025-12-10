import os
from pypdf import PdfReader
from pdfminer.high_level import extract_text
import docx

def extract_from_pdf(filepath: str) -> str:
    """Extract text from a PDF file using PDFMiner (more accurate)."""
    try:
        text = extract_text(filepath)
        if text.strip():
            return text
    except:
        pass

    # Fallback: PyPDF
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return ""

def extract_from_docx(filepath: str) -> str:
    """Extract text from a Word file."""
    doc = docx.Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def parse_resume_file(filepath: str) -> str:
    """Auto-detect file type and return extracted text."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return extract_from_pdf(filepath)
    elif ext in [".doc", ".docx"]:
        return extract_from_docx(filepath)
    else:
        raise ValueError("Unsupported file type. Upload PDF or Word resume.")

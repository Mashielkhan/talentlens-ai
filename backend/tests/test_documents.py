import io
import zipfile

import pymupdf
import pytest

from app.nlp.documents import DocumentError, extract_text, validate_file


def test_pdf_extracts_real_text(pdf):
    assert validate_file(pdf, "resume.pdf", "application/pdf") == ".pdf"
    assert "FastAPI" in extract_text(pdf, ".pdf")


def test_docx_includes_tables_and_headers(docx_bytes):
    validate_file(
        docx_bytes, "resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    text = extract_text(docx_bytes, ".docx")
    assert all(term in text for term in ["Synthetic Candidate", "ReactJS", "C++", "C#"])


@pytest.mark.parametrize(
    "data,filename,mime,error",
    [
        (b"hello", "r.exe", "application/pdf", "UNSUPPORTED_FORMAT"),
        (b"%PDF-test", "r.pdf", "image/png", "MIME_MISMATCH"),
        (b"not-pdf", "r.pdf", "application/pdf", "INVALID_PDF_SIGNATURE"),
        (b"", "r.pdf", "application/pdf", "FILE_SIZE_INVALID"),
        (b"x" * (10 * 1024 * 1024 + 1), "r.pdf", "application/pdf", "FILE_SIZE_INVALID"),
    ],
)
def test_upload_validation(data, filename, mime, error):
    with pytest.raises(DocumentError, match=error):
        validate_file(data, filename, mime)


def test_corrupted_pdf_is_explicit():
    with pytest.raises(DocumentError, match="CORRUPT_DOCUMENT"):
        extract_text(b"%PDF-1.5 corrupted", ".pdf")


def test_scanned_or_blank_pdf_requires_ocr():
    with pymupdf.open() as doc:
        doc.new_page()
        data = doc.tobytes()
    with pytest.raises(DocumentError, match="OCR_REQUIRED"):
        extract_text(data, ".pdf")


def test_encrypted_pdf():
    with pymupdf.open() as doc:
        doc.new_page().insert_text((40, 40), "A private resume with skills and experience")
        data = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secret", owner_pw="secret")
    with pytest.raises(DocumentError, match="ENCRYPTED_PDF"):
        extract_text(data, ".pdf")


def test_docx_zip_bomb():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", "a" * 1000000)
    with pytest.raises(DocumentError, match="COMPRESSION_LIMIT"):
        validate_file(
            buffer.getvalue(),
            "r.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


def test_pdf_multiple_columns_keeps_both_columns():
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((40, 50), "Skills\nPython FastAPI Docker")
        page.insert_text((300, 50), "Experience\nBuilt PostgreSQL applications")
        data = doc.tobytes()
    text = extract_text(data, ".pdf")
    assert "Python" in text and "PostgreSQL" in text

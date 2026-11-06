import io
import re
import zipfile
from pathlib import Path

import pymupdf
from docx import Document

MAX_SIZE = 10 * 1024 * 1024
MIMES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DocumentError(ValueError):
    pass


def validate_file(data: bytes, filename: str, mime: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in MIMES:
        raise DocumentError("UNSUPPORTED_FORMAT")
    if mime != MIMES[suffix]:
        raise DocumentError("MIME_MISMATCH")
    if not data or len(data) > MAX_SIZE:
        raise DocumentError("FILE_SIZE_INVALID")
    if suffix == ".pdf" and not data.startswith(b"%PDF-"):
        raise DocumentError("INVALID_PDF_SIGNATURE")
    if suffix == ".docx":
        if not data.startswith(b"PK\x03\x04"):
            raise DocumentError("INVALID_DOCX_SIGNATURE")
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 1000 or sum(i.file_size for i in entries) > 40 * 1024 * 1024:
                    raise DocumentError("DOCX_EXPANSION_LIMIT")
                if any(i.file_size > max(i.compress_size, 1) * 200 for i in entries):
                    raise DocumentError("DOCX_COMPRESSION_LIMIT")
                names = archive.namelist()
                if not {"[Content_Types].xml", "word/document.xml"}.issubset(names):
                    raise DocumentError("INVALID_DOCX")
                if any("vbaproject" in n.lower() or "embeddings/" in n.lower() for n in names):
                    raise DocumentError("ACTIVE_CONTENT_UNSUPPORTED")
                # Disallow entity declarations before the XML parser sees the archive.
                for item in entries:
                    if item.filename.endswith((".xml", ".rels")):
                        xml = archive.read(item).upper()
                        if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
                            raise DocumentError("XML_ENTITIES_UNSUPPORTED")
        except zipfile.BadZipFile as exc:
            raise DocumentError("CORRUPT_DOCX") from exc
    return suffix


def extract_text(data: bytes, suffix: str) -> str:
    try:
        if suffix == ".pdf":
            with pymupdf.open(stream=data, filetype="pdf") as doc:
                if doc.needs_pass:
                    raise DocumentError("ENCRYPTED_PDF")
                if len(doc) > 30:
                    raise DocumentError("PAGE_LIMIT_EXCEEDED")
                pages = [page.get_text(sort=True) for page in doc]
                if any(len(page.strip()) < 20 for page in pages):
                    raise DocumentError("OCR_REQUIRED_OR_EMPTY_PAGE")
                text = "\n\n".join(pages)
        else:
            doc = Document(io.BytesIO(data))
            blocks = []
            for section in doc.sections:
                blocks.extend(p.text for p in section.header.paragraphs)
            # Preserve the order of body paragraphs and tables.
            for block in doc.iter_inner_content():
                if hasattr(block, "text"):
                    blocks.append(block.text)
                else:
                    blocks.extend(" | ".join(c.text for c in row.cells) for row in block.rows)
            text = "\n".join(blocks)
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("CORRUPT_DOCUMENT") from exc
    text = re.sub(r"[ \t]+", " ", text.replace("\x00", "")).strip()
    if len(text) < 30:
        raise DocumentError("EMPTY_DOCUMENT")
    if len(text) > 150000:
        raise DocumentError("TEXT_LIMIT_EXCEEDED")
    return text

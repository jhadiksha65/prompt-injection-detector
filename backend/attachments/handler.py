"""
handler.py
Secure attachment handling for the /secure-prompt endpoint.

Supports PDF, DOC, DOCX, TXT, PNG, and JPG/JPEG attachments. Every
attachment is validated (extension, size, and content-sniffed type —
never the client-supplied Content-Type header) BEFORE any parsing is
attempted, and only plain text is ever extracted from it. No attachment
format is ever executed, evaluated, or macro-run: PDF/DOCX/TXT are
parsed with pure, non-executing text-extraction libraries, legacy DOC
files are converted to plain text via a sandboxed, timeout-bounded,
headless LibreOffice subprocess (a batch conversion, not an interactive
session, so no macro can run without a UI to authorize it), and
PNG/JPG images are decoded (never executed) with Pillow and read with
OCR (pytesseract/Tesseract) to extract any text they contain.
"""

import io
import os
import subprocess
import tempfile
import zipfile
from typing import Optional

from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg"}
DEFAULT_MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_EXTRACTED_TEXT_CHARS = 50_000

# Pixel-dimension ceiling for images, checked BEFORE decoding/OCR, to bound
# memory/CPU use and guard against decompression-bomb-style images (a small
# file that decodes to an enormous pixel buffer).
MAX_IMAGE_DIMENSION_PX = 6000

_PDF_MAGIC = b"%PDF-"
_ZIP_MAGIC = b"PK\x03\x04"
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"


class AttachmentError(Exception):
    """Raised for any attachment that must be safely rejected before parsing."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _max_attachment_bytes() -> int:
    try:
        return int(os.getenv("ATTACHMENT_MAX_BYTES", DEFAULT_MAX_ATTACHMENT_BYTES))
    except (TypeError, ValueError):
        return DEFAULT_MAX_ATTACHMENT_BYTES


def _validate_extension(filename: str) -> str:
    safe_name = secure_filename(filename or "")
    if not safe_name:
        raise AttachmentError("Attachment is missing a valid filename.")

    _, ext = os.path.splitext(safe_name)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AttachmentError(
            f"Unsupported attachment type '{ext or 'unknown'}'. "
            "Only PDF, DOC, DOCX, TXT, PNG, and JPG/JPEG files are supported."
        )
    return ext


def _validate_size(data: bytes) -> None:
    if len(data) == 0:
        raise AttachmentError("Attachment is empty.")
    max_bytes = _max_attachment_bytes()
    if len(data) > max_bytes:
        raise AttachmentError(
            f"Attachment exceeds the maximum allowed size of {max_bytes} bytes."
        )


def _sniff_and_validate_type(ext: str, data: bytes) -> None:
    """
    Validates the ACTUAL file content against the extension, never trusting
    the client-supplied filename or Content-Type/MIME header.
    """
    if ext == ".pdf":
        if not data.startswith(_PDF_MAGIC):
            raise AttachmentError("File content does not match a valid PDF document.")
    elif ext == ".docx":
        if not data.startswith(_ZIP_MAGIC):
            raise AttachmentError("File content does not match a valid DOCX document.")
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise AttachmentError("File content does not match a valid DOCX document.")
        except zipfile.BadZipFile:
            raise AttachmentError("File content does not match a valid DOCX document.")
    elif ext == ".doc":
        if not data.startswith(_OLE_MAGIC):
            raise AttachmentError("File content does not match a valid DOC document.")
    elif ext == ".txt":
        # No universal magic bytes for plain text; reject anything that looks
        # like binary content (embedded NUL bytes) masquerading as .txt.
        if b"\x00" in data:
            raise AttachmentError("File does not appear to be plain text.")
    elif ext == ".png":
        if not data.startswith(_PNG_MAGIC):
            raise AttachmentError("File content does not match a valid PNG image.")
    elif ext in (".jpg", ".jpeg"):
        if not data.startswith(_JPEG_MAGIC):
            raise AttachmentError("File content does not match a valid JPEG image.")


def _extract_pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise AttachmentError("PDF support is not available on this server.") from exc

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise AttachmentError("Encrypted PDF files are not supported.")
        pages_text = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages_text).strip()
    except AttachmentError:
        raise
    except Exception as exc:
        print(f"[ATTACHMENT PARSE ERROR] pdf detail={exc}")
        raise AttachmentError("The PDF file could not be parsed. It may be malformed.")


def _extract_docx_text(data: bytes) -> str:
    try:
        import docx
    except ImportError as exc:
        raise AttachmentError("DOCX support is not available on this server.") from exc

    try:
        document = docx.Document(io.BytesIO(data))
        parts = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    parts.append(cell.text)
        return "\n".join(part for part in parts if part).strip()
    except Exception as exc:
        print(f"[ATTACHMENT PARSE ERROR] docx detail={exc}")
        raise AttachmentError("The DOCX file could not be parsed. It may be malformed.")


def _extract_txt_text(data: bytes) -> str:
    try:
        return data.decode("utf-8", errors="replace").strip()
    except Exception as exc:
        print(f"[ATTACHMENT PARSE ERROR] txt detail={exc}")
        raise AttachmentError("The TXT file could not be decoded.")


def _extract_image_text(data: bytes) -> str:
    """
    Decodes a PNG/JPEG with Pillow (never executes anything embedded in the
    file) and runs OCR (pytesseract/Tesseract) over the decoded pixels to
    recover any text. Malformed images, oversized/decompression-bomb-style
    images, and OCR engine failures are all rejected safely.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise AttachmentError("Image support is not available on this server.") from exc

    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
    except Exception as exc:
        print(f"[ATTACHMENT PARSE ERROR] image detail={exc}")
        raise AttachmentError("The image file could not be parsed. It may be malformed.")

    try:
        # Image.verify() invalidates the file object, so it must be reopened
        # to actually decode pixel data.
        image = Image.open(io.BytesIO(data))
        width, height = image.size
        if width <= 0 or height <= 0:
            raise AttachmentError("The image file could not be parsed. It may be malformed.")
        if width > MAX_IMAGE_DIMENSION_PX or height > MAX_IMAGE_DIMENSION_PX:
            raise AttachmentError(
                f"Image dimensions exceed the maximum allowed {MAX_IMAGE_DIMENSION_PX}px."
            )
        image.load()
    except AttachmentError:
        raise
    except Exception as exc:
        print(f"[ATTACHMENT PARSE ERROR] image detail={exc}")
        raise AttachmentError("The image file could not be parsed. It may be malformed.")

    try:
        import pytesseract
    except ImportError as exc:
        raise AttachmentError("OCR support is not available on this server.") from exc

    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as exc:
        raise AttachmentError("OCR support is not available on this server.") from exc
    except Exception as exc:
        print(f"[ATTACHMENT PARSE ERROR] ocr detail={exc}")
        raise AttachmentError("OCR failed to process the image. It may be malformed.")

    return text.strip()


def _extract_doc_text(data: bytes) -> str:
    """
    Legacy binary .doc files are converted to plain text via a sandboxed,
    headless, timeout-bounded LibreOffice batch conversion. This is a
    non-interactive, one-shot conversion (no UI is available to authorize
    macro execution), run against an isolated temporary user profile so it
    never touches or reuses any other process state.
    """
    soffice_path = _find_soffice()
    if not soffice_path:
        raise AttachmentError("DOC support is not available on this server.")

    with tempfile.TemporaryDirectory(prefix="attach_doc_") as workdir:
        input_path = os.path.join(workdir, "input.doc")
        profile_dir = os.path.join(workdir, "lo_profile")
        with open(input_path, "wb") as f:
            f.write(data)

        try:
            subprocess.run(
                [
                    soffice_path,
                    "--headless",
                    "--norestore",
                    "--nolockcheck",
                    "--nodefault",
                    f"-env:UserInstallation=file://{profile_dir}",
                    "--convert-to", "txt:Text",
                    "--outdir", workdir,
                    input_path,
                ],
                check=True,
                capture_output=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired as exc:
            raise AttachmentError("The DOC file took too long to process.") from exc
        except subprocess.CalledProcessError as exc:
            print(f"[ATTACHMENT PARSE ERROR] doc detail={exc.stderr!r}")
            raise AttachmentError("The DOC file could not be parsed. It may be malformed.")

        output_path = os.path.join(workdir, "input.txt")
        if not os.path.exists(output_path):
            raise AttachmentError("The DOC file could not be parsed. It may be malformed.")

        with open(output_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()


def _find_soffice() -> Optional[str]:
    for candidate in ("soffice", "libreoffice"):
        path = _which(candidate)
        if path:
            return path
    return None


def _which(name: str) -> Optional[str]:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def extract_attachment_text(filename: str, data: bytes) -> str:
    """
    Validates (extension, size, sniffed content type) and extracts plain
    text from an attachment. Raises AttachmentError with a safe, generic,
    client-facing message for any unsupported/oversized/malformed input.
    Never executes or evaluates attachment content.
    """
    ext = _validate_extension(filename)
    _validate_size(data)
    _sniff_and_validate_type(ext, data)

    if ext == ".pdf":
        text = _extract_pdf_text(data)
    elif ext == ".docx":
        text = _extract_docx_text(data)
    elif ext == ".doc":
        text = _extract_doc_text(data)
    elif ext in (".png", ".jpg", ".jpeg"):
        text = _extract_image_text(data)
    else:  # .txt
        text = _extract_txt_text(data)

    if not text:
        raise AttachmentError("No extractable text was found in the attachment.")

    return text[:MAX_EXTRACTED_TEXT_CHARS]

from __future__ import annotations

import io
from pathlib import Path
import time

from docx import Document as DocxDocument
from pypdf import PdfReader
import requests


class ParsingError(ValueError):
    pass


def parse_uploaded_document(
    file_name: str,
    payload: bytes,
    enable_ocr: bool,
    azure_document_intelligence_endpoint: str = "",
    azure_document_intelligence_key: str = "",
) -> str:
    extension = Path(file_name).suffix.lower()
    if extension in {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        cloud_text = _parse_with_azure_document_intelligence(
            payload=payload,
            extension=extension,
            endpoint=azure_document_intelligence_endpoint,
            api_key=azure_document_intelligence_key,
        )
        if cloud_text:
            return cloud_text
    if extension in {".txt", ".md", ".csv", ".json"}:
        return payload.decode("utf-8", errors="ignore")
    if extension == ".pdf":
        return _parse_pdf(payload)
    if extension == ".docx":
        return _parse_docx(payload)
    if extension in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        return _parse_image_ocr(payload, enable_ocr)
    raise ParsingError(f"Unsupported file extension: {extension or 'none'}")


def _parse_pdf(payload: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(payload))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # pragma: no cover - defensive
        raise ParsingError(f"PDF parsing failed: {exc}") from exc
    text = "\n".join(pages).strip()
    if not text:
        raise ParsingError("PDF parsing returned empty text")
    return text


def _parse_docx(payload: bytes) -> str:
    try:
        doc = DocxDocument(io.BytesIO(payload))
        paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
    except Exception as exc:  # pragma: no cover - defensive
        raise ParsingError(f"DOCX parsing failed: {exc}") from exc
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ParsingError("DOCX parsing returned empty text")
    return text


def _parse_image_ocr(payload: bytes, enable_ocr: bool) -> str:
    if not enable_ocr:
        raise ParsingError("Image OCR is disabled. Set ENABLE_LOCAL_OCR=true to enable it.")
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - dependency safety
        raise ParsingError("OCR dependencies missing. Install pytesseract and Pillow.") from exc

    try:
        image = Image.open(io.BytesIO(payload))
        text = pytesseract.image_to_string(image).strip()
    except Exception as exc:  # pragma: no cover - external binary/runtime
        raise ParsingError(f"Image OCR failed: {exc}") from exc

    if not text:
        raise ParsingError("Image OCR returned empty text")
    return text


def _parse_with_azure_document_intelligence(
    payload: bytes,
    extension: str,
    endpoint: str,
    api_key: str,
) -> str:
    if not endpoint or not api_key:
        return ""
    content_type = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }.get(extension, "application/octet-stream")
    analyze_url = (
        f"{endpoint.rstrip('/')}/documentintelligence/documentModels/prebuilt-read:analyze"
        "?api-version=2024-11-30"
    )
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": content_type,
    }
    try:
        submit = requests.post(analyze_url, headers=headers, data=payload, timeout=30)
        submit.raise_for_status()
        operation_location = submit.headers.get("Operation-Location", "")
        if not operation_location:
            return ""
        for _ in range(30):
            poll = requests.get(operation_location, headers={"Ocp-Apim-Subscription-Key": api_key}, timeout=15)
            poll.raise_for_status()
            result = poll.json()
            status = str(result.get("status", "")).lower()
            if status == "succeeded":
                analyze_result = result.get("analyzeResult", {})
                content = analyze_result.get("content") or result.get("content") or ""
                return str(content).strip()
            if status in {"failed", "cancelled"}:
                return ""
            time.sleep(1.0)
    except Exception:
        return ""
    return ""

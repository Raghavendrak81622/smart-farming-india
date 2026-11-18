"""Extract a small set of readings without retaining the farmer's report."""
from io import BytesIO
import asyncio
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from fastapi import HTTPException, Request

LIMIT = 8 * 1024 * 1024
FIELDS = {
    "ph": r"p\s*\.?\s*h",
    "n": r"(?:available\s+)?nitrogen(?:\s*\(\s*n\s*\))?|n",
    "p": r"(?:available\s+)?phosphor(?:us|ous)(?:\s*\(\s*p\s*\))?|p",
    "k": r"(?:available\s+)?potassium(?:\s*\(\s*k\s*\))?|k",
}
UNIT = r"(?:\(\s*)?(?:kg\s*/\s*ha|kg\s*ha[-⁻]?1|mg\s*/\s*kg|ppm)(?:\s*\))?"


def parse_readings(text):
    values = {}
    for name, label in FIELDS.items():
        pattern = rf"^\s*(?:\d+[.)]\s*)?(?:{label})(?:[ \t]+{UNIT})?[ \t]*[:=|]?[ \t]*(?:\n[ \t]*)?(\d+(?:\.\d+)?)(?=[ \t\n]|$)"
        candidates = {float(result) for result in re.findall(pattern, text, re.I | re.M)}
        if len(candidates) == 1:
            value = candidates.pop()
            if value <= (14 if name == "ph" else 100000):
                values[name] = value
    return values


def ocr_image(image):
    from PIL import ImageOps
    with TemporaryDirectory() as folder:
        path = Path(folder) / "soil-report.png"
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((2400, 2400))
        image.save(path)
        return asyncio.run(asyncio.wait_for(recognize(path), timeout=20))


async def recognize(path):
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage import StorageFile

    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise ValueError("Install an OCR language using Windows language settings.")
    file = await StorageFile.get_file_from_path_async(str(path))
    with await file.open_read_async() as stream:
        decoder = await BitmapDecoder.create_async(stream)
        with await decoder.get_software_bitmap_async() as bitmap:
            result = await engine.recognize_async(bitmap)
            return "\n".join(line.text for line in result.lines)


def read_report(body):
    if body.startswith(b"%PDF-"):
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(body))
        pages = min(3, len(reader.pages))
        raw = "\n".join(reader.pages[i].extract_text(extraction_mode="layout") or "" for i in range(pages))
        if len(parse_readings(raw)) == 4:
            return raw
        try:
            import pypdfium2
            with pypdfium2.PdfDocument(body) as pdf:
                scans = [ocr_image(pdf[i].render(scale=1.65).to_pil()) for i in range(pages)]
            return raw + "\n" + "\n".join(scans)
        except (ImportError, OSError, RuntimeError, ValueError):
            return raw
    from PIL import Image
    with Image.open(BytesIO(body)) as image:
        if image.format not in {"PNG", "JPEG", "WEBP"} or image.width * image.height > 25_000_000:
            raise ValueError("Unsupported image.")
        return ocr_image(image)


async def import_report(request: Request):
    from starlette.concurrency import run_in_threadpool
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > LIMIT:
            raise HTTPException(413, "Choose a report smaller than 8 MB.")
    try:
        readings = parse_readings(await run_in_threadpool(read_report, bytes(body)))
    except Exception as error:
        raise HTTPException(422, "The report could not be read. Try a clear PDF, PNG or JPEG, or enter the readings manually.") from error
    if not readings:
        raise HTTPException(422, "No clear pH or NPK readings were found. Enter the values from the report manually.")
    return {"readings": readings}

import asyncio
import sys
from pathlib import Path

from nbconvert import WebPDFExporter

NOTEBOOK = "Fantasy Football Metrics Core Analysis.ipynb"
OUT_DIR = Path("PDFs")
OUT_NAME = "fantasy-football-narrative"

# Set this AFTER imports, right before converting, so nothing overrides it
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

exporter = WebPDFExporter()
exporter.exclude_input = True  # same as --no-input

body, resources = exporter.from_filename(NOTEBOOK)

OUT_DIR.mkdir(exist_ok=True)
out_path = OUT_DIR / f"{OUT_NAME}.pdf"
out_path.write_bytes(body)
print(f"Wrote {out_path}")
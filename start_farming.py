"""Start or rebuild the local Smart Farming application."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
vendor = ROOT / ".deps"
if vendor.is_dir():
    import pandas
    sys.path.append(str(vendor))

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", nargs="?", default="start", choices=("start", "prepare"))
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()
if args.action == "prepare":
    from smartfarm.prepare import prepare
    prepare()
else:
    import uvicorn
    uvicorn.run("smartfarm.app:app", host="127.0.0.1", port=args.port)

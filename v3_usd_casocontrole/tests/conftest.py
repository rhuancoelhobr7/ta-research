import pathlib
import sys

V3 = pathlib.Path(__file__).resolve().parents[1]
for p in (V3 / "src", V3.parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

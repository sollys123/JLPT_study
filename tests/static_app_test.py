from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "sw.js").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
VERSION = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))

assert VERSION["version"] == "4.1.0"
assert VERSION["schedulerReference"] == "FSRS-6 public formulas + Anki learning-step rules"
assert "jlpt-wisteria-v4.1.0" in SW
assert "python tests/static_app_test.py" in WORKFLOW
assert "python tools/fetch_jmdict.py both" in WORKFLOW

# Every local linked shell asset exists.
refs = set(re.findall(r'''(?:src|href)=["']([^"'#?]+)["']''', INDEX))
refs |= set(re.findall(r'''["'](\./[^"']+)["']''', SW))
for ref in refs:
    if ref.startswith(("http://", "https://", "data:")):
        continue
    rel = ref.removeprefix("./")
    if not rel or rel == "./":
        continue
    path = ROOT / rel
    assert path.exists(), f"Missing local asset: {rel}"

for required in [
    "assets/js/db.js",
    "assets/js/fsrs6.js",
    "assets/js/dictionary.js",
    "assets/js/srs-app.js",
    "assets/css/srs.css",
    "manifest.webmanifest",
]:
    assert required in SW, f"Service worker does not cache {required}"

# Deployment must publish only the clean application surface, not tests/tools.
assert "cp -R assets data _site/" in WORKFLOW
assert "tests" not in re.search(r"Build clean Pages artifact[\s\S]+?uses: actions/configure-pages", WORKFLOW).group(0)

print("STATIC APP TESTS PASSED")

from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / "index.html").read_text(encoding="utf-8")
start = html.rfind("<script>")
end = html.rfind("</script>")
if start < 0 or end <= start:
    raise SystemExit("Uygulama JavaScript bloğu bulunamadı.")
output = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/panorix_app.js")
output.write_text(html[start + len("<script>") : end], encoding="utf-8")
print(output)

r"""Render an .ico's frames side by side so the small ones can actually be looked at.

    python preview_ico.py path\to\app.ico --out preview.png

Each frame is upscaled with nearest-neighbour, so the real pixel grid stays
visible — a 16px frame shown at 16px on a high-DPI screen tells you nothing.
Exits non-zero when a size required by `ui-project` (16/32/48/256) is missing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

REQUIRED = {16, 32, 48, 256}
SHOWN = [256, 48, 32, 16]
BOX = {256: 256, 48: 192, 32: 160, 16: 128}
PAD = 16
BG = (245, 245, 245, 255)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ico", type=Path)
    parser.add_argument("--out", type=Path, default=Path("preview.png"))
    args = parser.parse_args()

    with Image.open(args.ico) as probe:
        available = {w for w, _ in probe.ico.sizes()}
    print("frames:", sorted(available))

    missing = REQUIRED - available
    if missing:
        print(f"FAIL: missing required size(s): {sorted(missing)}", file=sys.stderr)
        return 1

    shown = [s for s in SHOWN if s in available]
    width = sum(BOX[s] + PAD for s in shown) + PAD
    height = max(BOX[s] for s in shown) + PAD * 2
    sheet = Image.new("RGBA", (width, height), BG)

    x = PAD
    for size in shown:
        with Image.open(args.ico) as frame:
            frame.size = (size, size)
            frame.load()
            box = BOX[size]
            sheet.alpha_composite(
                frame.convert("RGBA").resize((box, box), Image.Resampling.NEAREST),
                (x, PAD),
            )
        x += box + PAD

    sheet.save(args.out)
    print(f"saved: {args.out}  {sheet.width}x{sheet.height}  (sizes shown: {shown})")
    print("Now open it. Check: shapes still separate at 16px, same silhouette as 256px,")
    print("not mistakable for a Wi-Fi / gear / folder icon.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

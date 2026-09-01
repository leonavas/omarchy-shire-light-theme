#!/usr/bin/env python3
"""Regenerate unlock.png and preview-unlock.png for the Shire Light theme.

unlock.png is the logo Plymouth draws on the boot screen (and SDDM on the
login screen). preview-unlock.png is the thumbnail the Style -> Unlock
selector shows; omarchy-plymouth-list only lists a theme that has one.

Nothing here is committed except this script: the wordmark is recoloured from
Omarchy's own logo.png, and the font is fetched on demand into tools/.cache/.

    python3 tools/build-unlock-art.py
"""

import base64
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "tools" / ".cache"
PLY = pathlib.Path("/usr/share/omarchy/default/plymouth")

# colors.toml
LOAM = "#20261A"       # background
PARCHMENT = "#EAE2C9"  # foreground
PASTURE = "#A3C46E"
LAMPLIGHT = "#E0B44F"
OAK = "#8A6A48"
BOARD = "#2E2619"      # board face, a touch warmer than loam so it reads

FONT_NAME = "MedievalSharp"
FONT_FILE = "MedievalSharp.ttf"
FONT_URL = ("https://github.com/google/fonts/raw/main/ofl/medievalsharp/"
            "MedievalSharp.ttf")

W, H = 900, 440        # keep H under ~550: the password entry sits below it


def run(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)


def fetch_font():
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / FONT_FILE
    if not dest.exists():
        print(f"fetching {FONT_NAME}...")
        urllib.request.urlretrieve(FONT_URL, dest)
    # fontconfig picks up $XDG_DATA_HOME/fonts
    fontroot = CACHE / "fontroot" / "fonts"
    fontroot.mkdir(parents=True, exist_ok=True)
    target = fontroot / FONT_FILE
    if not target.exists():
        target.write_bytes(dest.read_bytes())
    return str(CACHE / "fontroot")


def wordmark_b64(tmp):
    """Omarchy's wordmark, recoloured to pasture and scaled for the board."""
    out = tmp / "wordmark.png"
    run(["magick", str(PLY / "logo.png"),
         "-channel", "RGB", "+level-colors", f"{PASTURE},{PASTURE}",
         "-resize", "520x", f"PNG32:{out}"])
    return base64.b64encode(out.read_bytes()).decode()


def build_unlock(tmp, fontroot):
    b64 = wordmark_b64(tmp)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <radialGradient id="glow">
      <stop offset="0%"   stop-color="{LAMPLIGHT}" stop-opacity="0.16"/>
      <stop offset="45%"  stop-color="{LAMPLIGHT}" stop-opacity="0.07"/>
      <stop offset="78%"  stop-color="{LAMPLIGHT}" stop-opacity="0.015"/>
      <stop offset="100%" stop-color="{LAMPLIGHT}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <!-- Lamplight behind the sign. The ellipse reaches zero opacity inside the
       canvas; a full-bleed rect left ~1% alpha at the edges, which shows as a
       rectangular seam against Plymouth's flat background. -->
  <ellipse cx="450" cy="222" rx="444" ry="214" fill="url(#glow)"/>

  <rect x="140" y="26" width="620" height="13" rx="6" fill="{OAK}"/>
  <rect x="246" y="36" width="6" height="58" fill="{OAK}"/>
  <rect x="648" y="36" width="6" height="58" fill="{OAK}"/>

  <rect x="90" y="90" width="720" height="300" rx="14"
        fill="{BOARD}" stroke="{OAK}" stroke-width="5"/>
  <rect x="104" y="104" width="692" height="272" rx="8"
        fill="none" stroke="{OAK}" stroke-width="1.5" stroke-opacity="0.55"/>

  <image x="190" y="132" width="520" height="122"
         xlink:href="data:image/png;base64,{b64}"/>

  <line x1="210" y1="276" x2="690" y2="276"
        stroke="{OAK}" stroke-width="1.5" stroke-opacity="0.7"/>

  <g font-family="{FONT_NAME}" text-anchor="middle" fill="{PARCHMENT}">
    <text x="450" y="316" font-size="36" letter-spacing="1.5">No Admittance</text>
    <text x="450" y="352" font-size="24" letter-spacing="1.0"
          fill-opacity="0.72">except on party business</text>
  </g>
</svg>'''
    src = tmp / "unlock.svg"
    src.write_text(svg)
    run(["rsvg-convert", "-o", str(ROOT / "unlock.png"), str(src)],
        env={"XDG_DATA_HOME": fontroot, "PATH": "/usr/bin:/bin", "HOME": str(tmp)})


def build_preview(tmp):
    """Mirrors the geometry in /usr/share/omarchy/default/plymouth/omarchy.script."""
    SW, SH = 1920, 1080
    lx, ly = SW // 2 - W // 2, SH // 2 - H // 2       # omarchy.script:8-9
    ew, eh = 286, 48
    ex = SW // 2 - ew // 2                            # :111
    ey = ly + H + 40                                  # :112
    lh = eh * 0.8                                     # :118
    lw = 84 * (lh / 96)                               # :120
    lkx = ex - lw - 15                                # :124
    lky = ey + eh / 2 - lh / 2                        # :125

    def tint(name):
        out = tmp / name
        run(["magick", str(PLY / name), "-channel", "RGB",
             "+level-colors", f"{PARCHMENT},{PARCHMENT}", str(out)])
        return str(out)

    entry, lock, bullet = tint("entry.png"), tint("lock.png"), tint("bullet.png")

    cmd = ["magick", "-size", f"{SW}x{SH}", f"xc:{LOAM}",
           str(ROOT / "unlock.png"), "-geometry", f"+{lx}+{ly}", "-composite",
           entry, "-geometry", f"+{ex}+{ey}", "-composite",
           "(", lock, "-resize", f"{round(lw)}x{round(lh)}!", ")",
           "-geometry", f"+{round(lkx)}+{round(lky)}", "-composite"]
    for i in range(4):                                # :167-171
        cmd += ["(", bullet, "-resize", "7x7!", ")",
                "-geometry",
                f"+{ex + 20 + i * 12}+{round(ey + eh / 2 - 3.5)}", "-composite"]
    cmd += [str(ROOT / "preview-unlock.png")]
    run(cmd)


def main():
    if not PLY.exists():
        sys.exit(f"{PLY} not found - run this on an Omarchy system")
    fontroot = fetch_font()
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        build_unlock(tmp, fontroot)
        build_preview(tmp)
    for f in ("unlock.png", "preview-unlock.png"):
        print(subprocess.run(["identify", str(ROOT / f)],
                             capture_output=True, text=True).stdout.strip())


if __name__ == "__main__":
    main()

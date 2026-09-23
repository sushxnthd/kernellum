"""Generate original, deterministic research artwork for the Kernellum site."""

from pathlib import Path
import math
import random

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)


def artwork(name: str, seed: int, accent: str, mode: str) -> None:
    rng = random.Random(seed)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" role="img">',
        '<defs>',
        f'<radialGradient id="wash"><stop stop-color="{accent}" stop-opacity=".23"/><stop offset=".58" stop-color="{accent}" stop-opacity=".035"/><stop offset="1" stop-color="#070b0a" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="ground" x2="1" y2="1"><stop stop-color="#172620"/><stop offset=".48" stop-color="#0b1411"/><stop offset="1" stop-color="#040807"/></linearGradient>',
        f'<linearGradient id="metal" x2="1" y2="1"><stop stop-color="#234339"/><stop offset=".45" stop-color="#0d1a17"/><stop offset="1" stop-color="{accent}" stop-opacity=".15"/></linearGradient>',
        f'<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="8"/></filter>',
        '<pattern id="mesh" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0H0V34" fill="none" stroke="#8fbaa4" stroke-opacity=".095" stroke-width="1"/></pattern>',
        '<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#8bc6a4" fill-opacity=".22"/></pattern>',
        '</defs>',
        '<rect width="1600" height="1100" fill="url(#ground)"/>',
        '<rect width="1600" height="1100" fill="url(#mesh)"/>',
        f'<ellipse cx="{1050 if mode == "die" else 750}" cy="450" rx="850" ry="680" fill="url(#wash)"/>',
        '<path d="M0 0h1600v1100H0z" fill="url(#dots)" opacity=".27"/>',
        '<g font-family="monospace" font-size="13" letter-spacing="3" fill="#d0e8d7" fill-opacity=".55">',
        '<text x="62" y="76">KERNELLUM  /  PHYSICAL DESIGN SYSTEM</text>',
        f'<text x="62" y="1024">{name.upper().replace("-", " ")}  /  ROUTE FIELD 001</text>',
        '<text x="1315" y="76">42° 18′ 07″</text></g>',
        '<path d="M62 94H1538M62 997H1538" stroke="#a2d7b7" stroke-opacity=".26"/>',
    ]

    # Parallel trace families have separate curvature and spacing on each image.
    for i in range(32):
        y = 95 + i * 31
        offset = rng.randint(-85, 85)
        bend = rng.randint(-110, 110)
        op = .11 + (i % 7 == 0) * .31
        width = 1.1 + (i % 7 == 0) * .9
        lines.append(
            f'<path d="M-90 {y} H{245+offset} Q{420+offset} {y} {505+offset} {y+bend} '
            f'H{1040+offset} Q{1180+offset} {y+bend} {1260+offset} {y+bend-110} H1690" '
            f'fill="none" stroke="{accent}" stroke-opacity="{op:.2f}" stroke-width="{width:.1f}"/>'
        )
    for j in range(26):
        x = 160 + j * 52 + rng.randint(-9, 9)
        y = 120 + rng.randint(0, 780)
        lines.append(f'<circle cx="{x}" cy="{y}" r="{2 if j % 5 else 4}" fill="{accent}" opacity="{.26 if j % 5 else .75}"/>')

    if mode == "die":
        # Tilted chip and etched interconnect, as an abstract board rendering.
        lines += [
            '<g transform="translate(930 505) rotate(-19) skewX(-10)">',
            f'<rect x="-385" y="-316" width="770" height="632" rx="21" fill="{accent}" opacity=".17" filter="url(#glow)"/>',
            '<rect x="-385" y="-316" width="770" height="632" rx="21" fill="#101b17" stroke="#9dd6b4" stroke-opacity=".55" stroke-width="2"/>',
            '<rect x="-345" y="-276" width="690" height="552" rx="9" fill="url(#metal)" stroke="#96c9aa" stroke-opacity=".5"/>',
        ]
        for row in range(8):
            for col in range(11):
                x, y = -312 + col * 60, -244 + row * 65
                if (row + col) % 7 == 0:
                    lines.append(f'<rect x="{x}" y="{y}" width="48" height="50" rx="2" fill="{accent}" fill-opacity=".20" stroke="{accent}" stroke-opacity=".48"/>')
                else:
                    lines.append(f'<rect x="{x}" y="{y}" width="48" height="50" rx="2" fill="#0b1713" stroke="#8dbca1" stroke-opacity=".27"/>')
        lines += [
            '<rect x="-140" y="-112" width="280" height="224" rx="5" fill="#10241b" stroke="#d6fbbb" stroke-width="2"/>',
            f'<rect x="-111" y="-83" width="222" height="166" fill="{accent}" opacity=".16"/>',
            '<path d="M-95 0H95M0-68V68" stroke="#d6fbbb" stroke-opacity=".6"/>',
            '<text x="0" y="152" fill="#d9f5e0" font-family="monospace" font-size="18" letter-spacing="7" text-anchor="middle">K / 01</text>',
            '</g>',
        ]
    elif mode == "routes":
        lines.append('<g transform="translate(170 105)">')
        for row in range(10):
            for col in range(15):
                x, y = col * 89, row * 87
                size = 5 if (col + row) % 4 else 10
                lines.append(f'<circle cx="{x}" cy="{y}" r="{size}" fill="{accent}" fill-opacity="{.2 + (col % 4) * .12:.2f}"/>')
        for k in range(14):
            x1, y1 = rng.randrange(15) * 89, rng.randrange(10) * 87
            x2, y2 = rng.randrange(15) * 89, rng.randrange(10) * 87
            lines.append(f'<path d="M{x1} {y1} H{x2} V{y2}" fill="none" stroke="{accent}" stroke-opacity=".55" stroke-width="{2 if k % 3 else 4}"/>')
        lines.append('</g>')
        lines.append('<circle cx="850" cy="540" r="260" fill="none" stroke="#d8f7d2" stroke-opacity=".23" stroke-dasharray="3 13"/>')
    elif mode == "timing":
        for k in range(9):
            y = 190 + k * 88
            points = [f'{x},{y + 65 * math.sin(x / (73 + 5*k) + k*.5) * math.exp(-abs(x-800)/1250):.1f}' for x in range(0, 1601, 10)]
            lines.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{accent}" stroke-opacity="{.14 + k * .055:.2f}" stroke-width="{1 if k % 3 else 2}"/>')
        lines.append('<path d="M138 805H1465" stroke="#dcf5dc" stroke-opacity=".4" stroke-dasharray="8 10"/>')
        for k in range(16):
            x = 170 + k * 82
            h = 65 + rng.randint(0, 240)
            lines.append(f'<rect x="{x}" y="{805-h}" width="28" height="{h}" fill="{accent}" opacity="{.10+k*.014:.2f}"/>')
    else:  # measurement
        for k in range(12):
            x = 145 + k * 114
            top = 220 + rng.randrange(10) * 33
            lines.append(f'<rect x="{x}" y="{top}" width="78" height="{850-top}" rx="4" fill="{accent}" fill-opacity="{.05 + k*.012:.2f}" stroke="{accent}" stroke-opacity=".3"/>')
            lines.append(f'<path d="M{x+12} {top+90}h54M{x+12} {top+180}h54" stroke="{accent}" stroke-opacity=".5"/>')
        lines.append('<path d="M120 764C310 745 410 820 570 610S790 720 940 450 1120 540 1460 250" fill="none" stroke="#d6f8c2" stroke-width="3"/>')
    lines += ['<rect width="1600" height="1100" fill="#070907" opacity=".08"/>', '</svg>']
    (OUT / f"{name}.svg").write_text("\n".join(lines), encoding="utf-8")


for args in [
    ("architecture-die", 8, "#b9f35d", "die"),
    ("route-topology", 21, "#79d8c1", "routes"),
    ("timing-field", 13, "#b9f35d", "timing"),
    ("measurement-array", 34, "#a1e9af", "measurement"),
]:
    artwork(*args)

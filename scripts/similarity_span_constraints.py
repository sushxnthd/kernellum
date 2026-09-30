# Executed by nextpnr through --pre-place.
# The nextpnr Python hook provides a global `ctx`.

import os

MODE = os.environ.get("KERNELLUM_SPAN_MODE", "auto")
EXPECTED = int(os.environ.get("KERNELLUM_DSP_COUNT", "49"))


def _name(x):
    return str(x)


dsp_cells = sorted(
    [(cell, info) for cell, info in ctx.cells if _name(info.type) == "MULT18X18D"],
    key=lambda x: _name(x[0]),
)
dsp_bels = []
for bel in ctx.getBels():
    if _name(ctx.getBelType(bel)) != "MULT18X18D":
        continue
    loc = ctx.getBelLocation(bel)
    dsp_bels.append((bel, int(loc.x), int(loc.y), int(loc.z)))

print("[span-hook] mode=%s dsp_cells=%d dsp_bels=%d" % (MODE, len(dsp_cells), len(dsp_bels)))

if len(dsp_cells) != EXPECTED:
    raise RuntimeError("expected %d DSP cells, found %d" % (EXPECTED, len(dsp_cells)))

if MODE == "auto":
    print("[span-hook] unconstrained automatic placement")
elif MODE == "compact":
    xs = sorted(set(x for _, x, _, _ in dsp_bels))
    ys = sorted(set(y for _, _, y, _ in dsp_bels))
    best = None
    for yi, y0 in enumerate(ys):
        for y1 in ys[yi:]:
            for xi, x0 in enumerate(xs):
                for x1 in xs[xi:]:
                    count = sum(1 for _, x, y, _ in dsp_bels if x0 <= x <= x1 and y0 <= y <= y1)
                    if count < EXPECTED:
                        continue
                    span = (x1 - x0) + (y1 - y0)
                    area = (x1 - x0 + 1) * (y1 - y0 + 1)
                    candidate = (span, area, count, x0, y0, x1, y1)
                    if best is None or candidate < best:
                        best = candidate
    if best is None:
        raise RuntimeError("no compact rectangle contains enough DSP BELs")
    _, _, count, x0, y0, x1, y1 = best
    ctx.createRectangularRegion("dsp_compact", x0, y0, x1, y1)
    for cell, _ in dsp_cells:
        ctx.constrainCellToRegion(cell, "dsp_compact")
    print("[span-hook] compact rect=(%d,%d)-(%d,%d) bels=%d span=%d" %
          (x0, y0, x1, y1, count, (x1-x0)+(y1-y0)))
elif MODE == "elongated":
    rows = {}
    for bel, x, y, z in dsp_bels:
        rows.setdefault(y, []).append((x, bel, z))
    viable = [(len(v), y, sorted(v)) for y, v in rows.items() if len(v) >= EXPECTED]
    if not viable:
        raise RuntimeError("no single DSP row can host %d cells" % EXPECTED)
    _, y, row = max(viable)
    # Use 49 sites spread across the entire viable row. Seven logical cell
    # groups are each constrained to a distinct seven-site window.
    if EXPECTED != 49:
        raise RuntimeError("elongated pilot assumes 49 DSP cells")
    pick_idx = [round(i * (len(row)-1) / (EXPECTED-1)) for i in range(EXPECTED)]
    chosen = [row[i] for i in pick_idx]
    if len(set((x, z) for x, _, z in chosen)) != EXPECTED:
        raise RuntimeError("row sampling did not produce 49 unique DSP sites")
    for g in range(7):
        chunk = chosen[g*7:(g+1)*7]
        x0 = min(x for x, _, _ in chunk)
        x1 = max(x for x, _, _ in chunk)
        rname = "dsp_long_%d" % g
        ctx.createRectangularRegion(rname, x0, y, x1, y)
        for cell, _ in dsp_cells[g*7:(g+1)*7]:
            ctx.constrainCellToRegion(cell, rname)
        print("[span-hook] elongated group=%d rect=(%d,%d)-(%d,%d)" % (g,x0,y,x1,y))
    print("[span-hook] elongated row=%d span=%d sites=%d" %
          (y, max(x for x,_,_ in chosen)-min(x for x,_,_ in chosen), len(chosen)))
else:
    raise RuntimeError("unknown KERNELLUM_SPAN_MODE=%s" % MODE)

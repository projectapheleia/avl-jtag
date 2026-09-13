"""
Render example waveforms for the documentation.

Reads the VCD produced by each example (run ``make sim`` in examples first) and renders
the configured time windows to doc/source/images/<name>.png.

Usage (from the repository root):
    python3 doc/gen_waveforms.py
"""

import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

EXAMPLES = "examples/jtag"
IMAGES = "doc/source/images"

TAP_STATES = [
    "RESET", "IDLE",
    "DRSELECT", "DRCAPTURE", "DRSHIFT", "DREXIT1", "DRPAUSE", "DREXIT2", "DRUPDATE",
    "IRSELECT", "IRCAPTURE", "IRSHIFT", "IREXIT1", "IRPAUSE", "IREXIT2", "IRUPDATE",
]

# (label, signal, format) - format: "bit", "hex" or "state"
ROWS = [
    ("trst_n",   "example_hdl.jtag_if.trst_n", "bit"),
    ("tck",      "example_hdl.jtag_if.tck",    "bit"),
    ("tms",      "example_hdl.jtag_if.tms",    "bit"),
    ("tdi",      "example_hdl.jtag_if.tdi",    "bit"),
    ("tdo",      "example_hdl.jtag_if.tdo",    "bit"),
    ("state",    "example_hdl.tap.state",      "state"),
    ("ir",       "example_hdl.tap.ir",         "hex"),
    ("ir_sr",    "example_hdl.tap.ir_sr",      "hex"),
    ("dr_sr",    "example_hdl.tap.dr_sr",      "hex"),
    ("user_reg", "example_hdl.tap.user_reg",   "hex"),
]

# (image name, example, start ns, end ns, title)
WINDOWS = [
    ("jtag_init",      "directed", 6800, 7260, "OpenOCD init - end of chain examination, reset, IR length probe"),
    ("jtag_idcode",    "directed", 7140, 7630, "irscan avl.tap 0x1 ; drscan avl.tap 32 0  (IDCODE = 0xdeadbeef)"),
    ("jtag_user",      "directed", 7720, 8120, "drscan avl.tap 32 0xcafebabe  (USER register write)"),
    ("jtag_pause",     "directed", 8860, 9290, "drscan ... -endstate DRPAUSE ; pathmove DRPAUSE DREXIT2 DRUPDATE IDLE"),
    ("jtag_bypass",    "directed", 9650, 9920, "irscan avl.tap 0xf ; drscan avl.tap 8 0xa5  (BYPASS)"),
    ("jtag_trst",      "commands", 7120, 7390, "adapter assert trst ; adapter deassert trst ; runtest 5 ; irscan avl.tap 0x1"),
    ("jtag_user_proc", "commands", 8620, 9130, "user_rw 0x01234567  (Tcl proc: irscan + drscan)"),
]

UNITS = {"s": 1e9, "ms": 1e6, "us": 1e3, "ns": 1.0, "ps": 1e-3, "fs": 1e-6}


def parse_vcd(path: str, wanted: set[str]) -> dict[str, list[tuple[float, str]]]:
    """
    Minimal VCD parser.

    :param path: VCD file
    :param wanted: Full hierarchical signal names (without bit ranges) to extract
    :return: Mapping of signal name to list of (time ns, binary value string)
    """
    ids: dict[str, list[str]] = {}
    changes: dict[str, list[tuple[float, str]]] = {w: [] for w in wanted}
    scope: list[str] = []
    scale = 1e-3
    now = 0.0

    with open(path) as f:
        text = f.read()

    header, _, body = text.partition("$enddefinitions")

    m = re.search(r"\$timescale\s*(\d+)\s*(\w+)\s*\$end", header)
    if m:
        scale = int(m.group(1)) * UNITS[m.group(2)]

    for tok in re.finditer(r"\$(scope|upscope|var)\b(.*?)\$end", header, re.S):
        kind, args = tok.group(1), tok.group(2).split()
        if kind == "scope":
            scope.append(args[1])
        elif kind == "upscope":
            scope.pop()
        else:
            name = ".".join(scope + [args[3]])
            if name in wanted:
                ids.setdefault(args[2], []).append(name)

    tokens = iter(body.split())
    next(tokens)  # $end of $enddefinitions
    for tok in tokens:
        c = tok[0]
        if c == "#":
            now = int(tok[1:]) * scale
        elif c in "bBrR":
            ident = next(tokens)
            for name in ids.get(ident, []):
                changes[name].append((now, tok[1:].lower()))
        elif c in "01xXzZ" and len(tok) > 1:
            for name in ids.get(tok[1:], []):
                changes[name].append((now, c.lower()))
    return changes


def value_at(changes: list[tuple[float, str]], t: float) -> str:
    v = "x"
    for ct, cv in changes:
        if ct > t:
            break
        v = cv
    return v


def fmt(value: str, kind: str) -> str:
    if any(c not in "01" for c in value):
        return "x"
    n = int(value, 2)
    if kind == "state":
        return TAP_STATES[n]
    return f"{n:x}"


def render(changes, start: float, end: float, title: str, out: str) -> None:
    row_h = 1.0
    fig_h = 0.42 * len(ROWS) + 1.0
    fig, ax = plt.subplots(figsize=(16, fig_h))
    fig.subplots_adjust(left=0.07, right=0.995, top=1 - 0.45 / fig_h, bottom=0.6 / fig_h)
    ax_px = fig.get_figwidth() * fig.dpi * (0.995 - 0.07)
    ns_per_char = (end - start) / ax_px * 6.2

    for i, (label, sig, kind) in enumerate(ROWS):
        y = (len(ROWS) - 1 - i) * row_h
        ch = [(t, v) for t, v in changes[sig] if start < t < end]
        points = [(start, value_at(changes[sig], start))] + ch + [(end, None)]
        ax.text(start - (end - start) * 0.005, y + 0.35, label, ha="right", va="center", fontsize=9, family="monospace")

        for (t0, v), (t1, _) in zip(points, points[1:], strict=False):
            if kind == "bit":
                lvl = y + (0.7 if v == "1" else 0.0)
                color = "#d62728" if v not in ("0", "1") else "#1f77b4"
                ax.plot([t0, t1], [lvl, lvl], color=color, lw=1.2)
            else:
                d = min((t1 - t0) * 0.15, (end - start) * 0.002)
                xs = [t0, t0 + d, t1 - d, t1, t1 - d, t0 + d, t0]
                ys = [y + 0.35, y + 0.7, y + 0.7, y + 0.35, y, y, y + 0.35]
                ax.fill(xs, ys, facecolor="#e8f0fa", edgecolor="#1f77b4", lw=1.0)
                text = fmt(v, kind)
                if (t1 - t0) > ns_per_char * (len(text) + 1):
                    ax.text((t0 + t1) / 2, y + 0.35, text, ha="center", va="center", fontsize=7, family="monospace")
                elif (t1 - t0) > ns_per_char * 2 and kind == "state":
                    ax.text((t0 + t1) / 2, y + 0.35, text[:2 if text.startswith(("DR", "IR")) else 1], ha="center", va="center", fontsize=6, family="monospace")

        if kind == "bit":
            for t, _v in ch:
                ax.plot([t, t], [y, y + 0.7], color="#1f77b4", lw=1.2)

    ax.set_xlim(start, end)
    ax.set_ylim(-0.3, len(ROWS) * row_h)
    ax.set_yticks([])
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    ax.set_xlabel("time (ns)", fontsize=9)
    ax.tick_params(axis="x", labelsize=8)
    ax.grid(axis="x", color="#dddddd", lw=0.5)
    ax.set_axisbelow(True)
    ax.set_title(title, fontsize=10, family="monospace", loc="left")
    fig.savefig(out, dpi=100)
    plt.close(fig)


def main() -> int:
    cache = {}
    wanted = {sig for _, sig, _ in ROWS}
    for name, example, start, end, title in WINDOWS:
        vcd = os.path.join(EXAMPLES, example, "dump.vcd")
        if not os.path.exists(vcd):
            print(f"Missing {vcd} - run 'make sim' in {os.path.dirname(vcd)} first", file=sys.stderr)
            return 1
        if vcd not in cache:
            cache[vcd] = parse_vcd(vcd, wanted)
        out = os.path.join(IMAGES, f"{name}.png")
        render(cache[vcd], start, end, title, out)
        print(f"Generated {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

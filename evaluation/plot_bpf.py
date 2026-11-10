"""Plot hairpin bandpass-filter results from Touchstone (.s2p) files.

Per filter: |S11|, |S21| vs f/f0 (bpf_<N>GHz.png) and the curves as CSV in the format of the
thesis figure (images/bpf_curves/bpf_s11_<N>GHz.csv, bpf_s21_<N>GHz.csv: x = f/f0, mag_db,
phase_deg with unwrapped phase). Across filters: metrics at each design frequency
(bpf_summary.png / .csv):

    insertion_loss  -|S21| at f0 (dB)
    return_loss     |S11| at f0 (dB)
    peak_s21        max |S21| (dB) and f_peak / f0 (passband centre)
    bw3db_pct       -3 dB bandwidth below the S21 peak, in % of f0 (design: 5 %)

Port roles: 1 = input, 2 = output. Prefers the de-embedded files; --raw uses the raw Palace
results (what the thesis S-parameter figures show).

Usage:
    python plot_bpf.py gds/bpf
    python plot_bpf.py gds/bpf --raw
"""

import argparse
import csv
import os
import re
import sys
from glob import glob

import matplotlib
import numpy as np
import skrf as rf

# pinned: letting matplotlib probe for a GUI backend can hang on headless/VNC setups
matplotlib.use("Agg")

from matplotlib import pyplot as plt
from plot_wpd import C_OUT_A, C_RETURN, INK, MUTED, OUT_DIR  # noqa: E402  (also sets the rcParams)

FREQ_RE = re.compile(r"bpf[_-]?(\d+(?:\.\d+)?)\s*GHz", re.IGNORECASE)
CURVE_DIR = os.path.join(OUT_DIR, "bpf_curves")


def design_freq_ghz(path: str) -> float | None:
    """Design frequency (GHz) from a bpf_<N>GHz tag anywhere in the path, or None."""
    m = FREQ_RE.search(path)
    return float(m.group(1)) if m else None


def find_bpf_touchstone(paths, prefer_deembedded=True):
    """One .s2p per design frequency (de-embedded or raw, drops _dc), as sorted (GHz, path)."""
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += glob(os.path.join(p, "**", "*.s2p"), recursive=True)
        elif os.path.isfile(p):
            files.append(p)
        else:
            print(f"skipping {p!r} (not a file or directory)")

    best: dict[float, tuple[int, str]] = {}
    for f in files:
        fghz = design_freq_ghz(f)
        if fghz is None:
            print(f"skipping {f!r} (no bpf_<N>GHz tag in path)")
            continue
        base = os.path.basename(f)[: -len(".s2p")]
        if base.endswith("_dc"):
            continue
        rank = (2 if prefer_deembedded else 0) if base.endswith("_deembedded") else 1
        if fghz not in best or rank > best[fghz][0]:
            best[fghz] = (rank, f)
    return sorted((fghz, f) for fghz, (_, f) in best.items())


def _sdb(ntwk, a, b):
    """|S[a][b]| in dB over frequency (0-based port indices)."""
    return 20 * np.log10(np.abs(ntwk.s[:, a, b]))


def metrics(ntwk, fghz):
    """Metrics at / around the design frequency (see module docstring)."""
    x = ntwk.frequency.f / (fghz * 1e9)
    s21 = _sdb(ntwk, 1, 0)
    i0 = int(np.argmin(np.abs(x - 1)))
    ip = int(np.argmax(s21))
    above = np.where(s21 >= s21[ip] - 3)[0]
    # contiguous -3 dB band around the peak; nan if it touches the edge of the sweep
    lo, hi = ip, ip
    while lo - 1 in above:
        lo -= 1
    while hi + 1 in above:
        hi += 1
    if lo == 0 or hi == len(x) - 1:
        bw = float("nan")
    else:

        def cross(i, j):  # linear interpolation of the -3 dB crossing between samples i and j
            return x[i] + (s21[ip] - 3 - s21[i]) * (x[j] - x[i]) / (s21[j] - s21[i])

        bw = (cross(hi, hi + 1) - cross(lo - 1, lo)) * 100
    return {
        "insertion_loss": float(-s21[i0]),
        "return_loss": float(_sdb(ntwk, 0, 0)[i0]),
        "peak_s21": float(s21[ip]),
        "f_peak_rel": float(x[ip]),
        "bw3db_pct": bw,
    }


def write_curves(ntwk, fghz):
    """bpf_s11_<N>GHz.csv / bpf_s21_<N>GHz.csv (x = f/f0, mag_db, unwrapped phase_deg)."""
    os.makedirs(CURVE_DIR, exist_ok=True)
    x = ntwk.frequency.f / (fghz * 1e9)
    for tag, (a, b) in (("s11", (0, 0)), ("s21", (1, 0))):
        mag = _sdb(ntwk, a, b)
        ph = np.degrees(np.unwrap(np.angle(ntwk.s[:, a, b])))
        out = os.path.join(CURVE_DIR, f"bpf_{tag}_{fghz:g}GHz.csv")
        with open(out, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["x", "mag_db", "phase_deg"])
            for row in zip(x, mag, ph):
                w.writerow([f"{v:.10g}" for v in row])
    print(f"wrote {CURVE_DIR}/bpf_{{s11,s21}}_{fghz:g}GHz.csv")


def plot_one(ntwk, fghz, m):
    """|S11| and |S21| over f/f0 for one filter."""
    x = ntwk.frequency.f / (fghz * 1e9)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(x, _sdb(ntwk, 0, 0), color=C_RETURN, label="input match  S11")
    ax.plot(x, _sdb(ntwk, 1, 0), color=C_OUT_A, label="transmission  S21")
    ax.axvline(1, color=INK, lw=0.8, alpha=0.35)
    ax.axhline(-3, color=MUTED, ls=":", lw=1)
    ax.set_xlabel("f / f0")
    ax.set_ylabel("magnitude  (dB)")
    ax.set_ylim(bottom=max(-60, ax.get_ylim()[0]))
    ax.legend(fontsize=9, loc="lower right")
    ax.set_title(
        f"IL {m['insertion_loss']:.2f} dB, RL {m['return_loss']:.1f} dB at f0, "
        f"peak at {m['f_peak_rel']:.3f} f0, BW(-3 dB) {m['bw3db_pct']:.2f} %",
        fontsize=10,
        color=MUTED,
    )
    fig.suptitle(f"hairpin bandpass filter  @ design {fghz:g} GHz", fontsize=14, color=INK)
    fig.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"bpf_{fghz:g}GHz.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def summary(rows):
    """bpf_summary.png / .csv: metrics vs design frequency."""
    rows = sorted(rows, key=lambda r: r["design_ghz"])
    cols = ["design_ghz", "insertion_loss", "return_loss", "peak_s21", "f_peak_rel", "bw3db_pct"]
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "bpf_summary.csv")
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([f"{r[c]:.4f}" for c in cols])
    print(f"wrote {out}")

    f = [r["design_ghz"] for r in rows]
    fig, (axl, axr) = plt.subplots(1, 2, figsize=(12, 4.5))
    axl.plot(f, [r["insertion_loss"] for r in rows], "-o", color=C_OUT_A, label="insertion loss at f0")
    axl.plot(f, [r["return_loss"] for r in rows], "-o", color=C_RETURN, label="return loss at f0")
    axl.set_xlabel("design frequency  (GHz)")
    axl.set_ylabel("(dB)")
    axl.legend(fontsize=9)
    axr.plot(f, [r["bw3db_pct"] for r in rows], "-o", color=C_OUT_A, label="-3 dB bandwidth (% of f0)")
    axr.plot(f, [(r["f_peak_rel"] - 1) * 100 for r in rows], "-o", color=C_RETURN, label="centre shift (% of f0)")
    axr.axhline(5, color=MUTED, ls="--", lw=1)
    axr.axhline(0, color=MUTED, ls=":", lw=1)
    axr.set_xlabel("design frequency  (GHz)")
    axr.set_ylabel("(%)")
    axr.legend(fontsize=9)
    fig.suptitle("hairpin bandpass filter performance vs design frequency", fontsize=14, color=INK)
    fig.tight_layout()
    out = os.path.join(OUT_DIR, "bpf_summary.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main():
    """CLI entry point."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("paths", nargs="+", help="Touchstone .s2p files or directories")
    p.add_argument("--raw", action="store_true", help="use the raw (not de-embedded) results")
    args = p.parse_args()

    found = find_bpf_touchstone(args.paths, prefer_deembedded=not args.raw)
    if not found:
        sys.exit("no BPF .s2p files found")

    rows = []
    for fghz, path in found:
        ntwk = rf.Network(path)
        if ntwk.nports != 2 or ntwk.frequency.npoints < 3:
            print(f"skipping {path!r}: expected a 2-port sweep")
            continue
        print(f"{fghz:g} GHz: {path}")
        m = metrics(ntwk, fghz)
        plot_one(ntwk, fghz, m)
        write_curves(ntwk, fghz)
        rows.append({"design_ghz": fghz, **m})

    if rows:
        summary(rows)


if __name__ == "__main__":
    main()

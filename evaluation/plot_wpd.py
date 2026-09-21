"""Plot Wilkinson-power-divider results from Touchstone (.s3p) files.

Per divider: |S| vs f, amplitude imbalance and output phase difference (wpd_<N>GHz.png).
Across dividers: figures of merit at each design frequency (wpd_summary.png / .csv).
Port roles are fixed (1 = input, 2/3 = outputs); the PDK cell has no isolation
resistor - see README.md, "How the extraction works".

Usage:
    python plot_wpd.py gds/wpd
    python plot_wpd.py a.s3p b.s3p --rl-spec 15

Paths may be Touchstone files or directories (searched recursively).
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

PALETTE = [
    "#2a78d6",
    "#1baf7a",
    "#eda100",
    "#008300",
    "#4a3aa7",
    "#e34948",
    "#e87ba4",
    "#eb6834",
]
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e5e5e2", "#fcfcfb"

C_RETURN, C_OUT_A, C_OUT_B, C_ISO = PALETTE[5], PALETTE[0], PALETTE[1], PALETTE[2]

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.size": 11,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "lines.linewidth": 2,
        "lines.markersize": 6,
        "legend.frameon": False,
    }
)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

FREQ_RE = re.compile(r"wpd[_-]?(\d+(?:\.\d+)?)\s*GHz", re.IGNORECASE)


def design_freq_ghz(path: str) -> float | None:
    """Design frequency (GHz) from a wpd_<N>GHz tag anywhere in the path, or None."""
    m = FREQ_RE.search(path)
    return float(m.group(1)) if m else None


def find_wpd_touchstone(paths, prefer_deembedded=True):
    """One .s3p per design frequency (prefers _deembedded, drops _dc), as sorted (GHz, path)."""
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += glob(os.path.join(p, "**", "*.s3p"), recursive=True)
        elif os.path.isfile(p):
            files.append(p)
        else:
            print(f"skipping {p!r} (not a file or directory)")

    best: dict[float, tuple[int, str]] = {}
    for f in files:
        fghz = design_freq_ghz(f)
        if fghz is None:
            print(f"skipping {f!r} (no wpd_<N>GHz tag in path)")
            continue
        base = os.path.basename(f)[: -len(".s3p")]
        variant = "raw"
        if base.endswith("_deembedded"):
            variant = "deembedded"
        elif base.endswith("_dc"):
            variant = "dc"
        rank = {"deembedded": 2 if prefer_deembedded else 0, "raw": 1, "dc": 0}[variant]
        if fghz not in best or rank > best[fghz][0]:
            best[fghz] = (rank, f)
    return sorted((fghz, f) for fghz, (_, f) in best.items())


def _freq_index(ntwk: rf.Network, fghz: float | None) -> int:
    """Index of the frequency sample nearest fghz (or the middle sample if None)."""
    if fghz is None:
        return ntwk.frequency.npoints // 2
    return int(np.argmin(np.abs(ntwk.frequency.f - fghz * 1e9)))


def _sdb(ntwk, a, b):
    """|S[a][b]| in dB over frequency (0-based port indices)."""
    return 20 * np.log10(np.abs(ntwk.s[:, a, b]))


def _wrap180(deg):
    """Wrap an angle (or array of angles) in degrees to the range (-180, 180]."""
    return (deg + 180) % 360 - 180


def metrics_at_design(ntwk, fghz):
    """Return loss, isolation |S32|, excess loss, imbalance and output phase error (dB / deg)."""
    i = _freq_index(ntwk, fghz)
    a = ntwk.s[i, 1, 0]
    b = ntwk.s[i, 2, 0]
    a_db, b_db = 20 * np.log10(np.abs(a)), 20 * np.log10(np.abs(b))
    phase = _wrap180(np.degrees(np.angle(a) - np.angle(b)))
    return {
        "return_loss": float(_sdb(ntwk, 0, 0)[i]),
        "isolation": float(_sdb(ntwk, 2, 1)[i]),
        "excess_loss": float(-10 * np.log10(np.abs(a) ** 2 + np.abs(b) ** 2)),
        "imbalance": float(a_db - b_db),
        "phase_err": float(phase),
    }


def plot_one(ntwk, fghz, rl_spec):
    """3-panel detail figure for one divider: magnitudes, imbalance, phase difference."""
    fg = ntwk.frequency.f / 1e9

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(7.5, 9), sharex=True)

    ax1.plot(fg, _sdb(ntwk, 0, 0), color=C_RETURN, label="return loss  S11")
    ax1.plot(fg, _sdb(ntwk, 1, 0), color=C_OUT_A, label="output  S21")
    ax1.plot(fg, _sdb(ntwk, 2, 0), color=C_OUT_B, label="output  S31")
    ax1.plot(fg, _sdb(ntwk, 2, 1), color=C_ISO, label="isolation  S32")
    ax1.axhline(-3.01, color=MUTED, ls=":", lw=1)
    ax1.axhline(-rl_spec, color=MUTED, ls="--", lw=1)
    ax1.text(fg[0], -3.01, " -3 dB", va="bottom", ha="left", color=MUTED, fontsize=9)
    ax1.set_ylabel("magnitude  (dB)")
    ax1.set_ylim(bottom=max(-40, ax1.get_ylim()[0]))
    ax1.legend(ncol=2, fontsize=9)

    imb = _sdb(ntwk, 1, 0) - _sdb(ntwk, 2, 0)
    ax2.plot(fg, imb, color=C_OUT_A)
    ax2.axhline(0, color=MUTED, ls=":", lw=1)
    ax2.set_ylabel("imbalance  |S21|-|S31|  (dB)")

    dphi = _wrap180(np.degrees(np.angle(ntwk.s[:, 1, 0]) - np.angle(ntwk.s[:, 2, 0])))
    ax3.plot(fg, dphi, color=C_OUT_B)
    ax3.axhline(0, color=MUTED, ls="--", lw=1)
    ax3.text(fg[0], 0, " ideal 0 deg", va="bottom", ha="left", color=MUTED, fontsize=9)
    ax3.set_ylabel("phase diff  (deg)")
    ax3.set_xlabel("frequency  (GHz)")

    if fghz is not None:
        for ax in (ax1, ax2, ax3):
            ax.axvline(fghz, color=INK, ls="-", lw=0.8, alpha=0.35)
        ax1.text(
            fghz,
            ax1.get_ylim()[1],
            f" design {fghz:g} GHz",
            va="top",
            ha="left",
            color=INK,
            fontsize=9,
        )

    tag = f"{fghz:g}GHz" if fghz is not None else "unknown"
    fig.suptitle(f"Wilkinson power divider  @ design {tag}", fontsize=14, color=INK)
    fig.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"wpd_{tag}.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def plot_summary(rows, rl_spec):
    """Metrics vs design frequency across all dividers (dB left, phase error right)."""
    rows = sorted(rows, key=lambda r: r["design_ghz"])
    f = [r["design_ghz"] for r in rows]

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(12, 4.5))

    axl.plot(f, [r["return_loss"] for r in rows], "-o", color=C_RETURN, label="return loss")
    axl.plot(f, [r["isolation"] for r in rows], "-o", color=C_ISO, label="isolation")
    axl.plot(f, [r["excess_loss"] for r in rows], "-o", color=C_OUT_A, label="excess loss")
    axl.plot(f, [r["imbalance"] for r in rows], "-o", color=C_OUT_B, label="amp imbalance")
    axl.axhline(-rl_spec, color=MUTED, ls="--", lw=1)
    axl.set_xlabel("design frequency  (GHz)")
    axl.set_ylabel("(dB)")
    axl.set_title("power metrics at design frequency", fontsize=12, color=INK)
    axl.legend(fontsize=9)

    axr.plot(f, [r["phase_err"] for r in rows], "-o", color=C_OUT_B)
    axr.axhline(0, color=MUTED, ls=":", lw=1)
    axr.set_xlabel("design frequency  (GHz)")
    axr.set_ylabel("phase error from 0 deg  (deg)")
    axr.set_title("output phase balance at design frequency", fontsize=12, color=INK)

    fig.suptitle(
        "Wilkinson power divider performance vs design frequency",
        fontsize=14,
        color=INK,
    )
    fig.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "wpd_summary.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def dump_summary_csv(rows):
    """Write the per-divider summary metrics to images/wpd_summary.csv."""
    rows = sorted(rows, key=lambda r: r["design_ghz"])
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "wpd_summary.csv")
    cols = [
        "design_ghz",
        "return_loss",
        "isolation",
        "excess_loss",
        "imbalance",
        "phase_err",
    ]
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([f"{r[c]:.4f}" for c in cols])
    print(f"wrote {out}")


def main():
    """CLI entry point."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("paths", nargs="+", help="Touchstone .s3p files or directories")
    p.add_argument(
        "--rl-spec",
        type=float,
        default=15.0,
        help="return-loss / isolation guide line in dB (default 15)",
    )
    args = p.parse_args()

    found = find_wpd_touchstone(args.paths)
    if not found:
        sys.exit("no WPD .s3p files found")

    rows = []
    for fghz, path in found:
        ntwk = rf.Network(path)
        if ntwk.nports != 3:
            print(f"skipping {path!r}: expected 3 ports, got {ntwk.nports}")
            continue
        plot_one(ntwk, fghz, args.rl_spec)
        m = metrics_at_design(ntwk, fghz)
        rows.append({"design_ghz": fghz if fghz is not None else 0.0, **m})

    if rows:
        plot_summary(rows, args.rl_spec)
        dump_summary_csv(rows)


if __name__ == "__main__":
    main()

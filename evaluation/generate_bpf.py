"""Generate the hairpin coupled-line bandpass filter sweep (gds/bpf).

The filter of the SPARX chip (SG13G2_SPARX160, scripts/six_port_gen.py): Butterworth, order 3,
fixed 1 GHz bandwidth, TopMetal2 over Metal5. Unlike the chip (connection_length=10), no feed
lines (connection_length=0), as in the BLC/WPD sweeps. The 5 % fractional-bandwidth design of
the NorCAS paper, simulated on 2026-11-10, is kept in gds/bpf_5pct. Port k of the cell (e<k>)
is marked on GDS layer 200+k. palace_sim.py sweeps 0.5-1.5 f0 in 0.01 f0 steps.

    python generate_bpf.py                # 60, 160 and 300 GHz (the thesis figure)
    python generate_bpf.py 60 80 100 ...  # other design frequencies (GHz)
"""

import os
import sys

import gdsfactory as gf

import ihp

# activate the IHP PDK
ihp.PDK.activate()

# resolve output directory relative to this script, not the current working directory
GDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gds", "bpf")

ORDER = 3
BANDWIDTH = 1e9  # absolute bandwidth (Hz), the same for every f0
FILTER_TYPE = "butter"

freqs_ghz = [int(a) for a in sys.argv[1:]] or [60, 160, 300]
os.makedirs(GDS_DIR, exist_ok=True)

for f_ghz in freqs_ghz:
    f = f_ghz * 1e9
    name = f"bpf_{f_ghz}GHz"
    c = gf.Component(name)
    bpf = c.add_ref(
        ihp.cells.hairpin_coupled_line_bandpass_filter(
            order=ORDER,
            frequency=f,
            bandwidth=BANDWIDTH,
            connection_length=0.0,
            filter_type=FILTER_TYPE,
        )
    )

    for k, pname in ((1, "e1"), (2, "e2")):
        p = bpf.ports[pname]
        horizontal = p.orientation in (0, 180)
        size = (0.1, p.width) if horizontal else (p.width, 0.1)
        mark = c.add_ref(gf.components.rectangle(size=size, layer=(200 + k, 0)))
        mark.center = p.center
        # shift the 0.1 um marker half its length into the line, as in generate_blc.py
        dx, dy = {0: (-0.05, 0), 180: (0.05, 0), 90: (0, -0.05), 270: (0, 0.05)}[round(p.orientation) % 360]
        mark.move((dx, dy))

    gds_path = os.path.join(GDS_DIR, f"{name}.gds")
    c.write_gds(gds_path, with_metadata=False)
    print(f"wrote {gds_path}")

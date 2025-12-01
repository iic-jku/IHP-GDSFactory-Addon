"""Via stack components for IHP PDK. Also includes NoFillerStack."""
#TODO prbably not the right place for NoFillerStack
import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

from sg13g2_pycell_lib.ihp.via_stack_code import via_stack as via_stackIHP
from sg13g2_pycell_lib.ihp.NoFillerStack_code import NoFillerStack as no_filler_stackIHP


import gdsfactory as gf

from .utils import *
from functools import partial
from .. import tech


@gf.cell
def via_stack(
    bottom_layer: str = "Metal1",
    top_layer: str = "Metal2",
    vn_columns: int = 2,
    vn_rows: int = 2,
    vt1_columns: int = 1,
    vt1_rows: int = 1,
    vt2_columns: int = 1,
    vt2_rows: int = 1,
) -> gf.Component:
    """Create a via stack test component.

    Args:
        bottom_layer: Bottom metal layer name.
        top_layer: Top metal layer name.
        vn_columns: Number of columns for normal vias (Via1-Via4).
        vn_rows: Number of rows for normal vias.
        vt1_columns: Number of columns for TopVia1.
        vt1_rows: Number of rows for TopVia1.
        vt2_columns: Number of columns for TopVia2.
        vt2_rows: Number of rows for TopVia2.

    Returns:
        Component with via stack test.
    """

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'b_layer': bottom_layer,
        't_layer': top_layer,
        'vn_columns': vn_columns,
        'vn_rows': vn_rows,
        'vt1_columns': vt1_columns,
        'vt1_rows': vt1_rows,
        'vt2_columns': vt2_columns,
        'vt2_rows': vt2_rows
    }

    c = generate_gf_from_ihp(cell_name="via_stack", cell_params=params, function_name=via_stackIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def no_filler_stack(
    width: int = 10,
    length: int = 10,
    noAct: str = "Yes",   # no active filler
    noGP: str = "Yes",    # no GatePoly filler
    noM1: str = "Yes",    # no M1 filler
    noM2: str = "Yes",    # no M2 filler
    noM3: str = "Yes",    # no M3 filler
    noM4: str = "Yes",    # no M4 filler
    noM5: str = "Yes",    # no M5 filler
    noTM1: str = "Yes",   # no TM1 filler
    noTM2: str = "Yes",   # no TM2 filler
) -> gf.Component:
    """Create a NoFiller via stack test component.

    Interface mirrors the provided GUI (except minLW).

    Args:
        bottom_layer: Bottom metal layer name.
        top_layer: Top metal layer name.
        width: device width (string with units, e.g. '100u').
        length: device length (string with units).
        noAct..noTM2: booleans to enable/disable filler for each layer.

    Returns:
        gdsfactory.Component with NoFiller via stack.
    """

    params = {
        "cdf_version": tech.techParams['CDFVersion'],
        "Display": "Selected",
        "w": width*1e-6,
        "l": length*1e-6,
        "minLW": 10e-9, # hardcoded not in tech file
        "noAct": noAct,
        "noGP": noGP,
        "noM1": noM1,
        "noM2": noM2,
        "noM3": noM3,
        "noM4": noM4,
        "noM5": noM5,
        "noTM1": noTM1,
        "noTM2": noTM2,
    }

    c = generate_gf_from_ihp(cell_name="no_filler_stack", cell_params=params, function_name=no_filler_stackIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c



if __name__ == "__main__":
    # Test the components
    c = via_stack(bottom_layer="Metal1", top_layer="Metal5")
    c.show()


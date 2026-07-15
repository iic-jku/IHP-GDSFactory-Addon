"""Diode components for IHP PDK."""

import os
import sys

pdk_root = os.environ.get("PDK_ROOT", "/foss/pdks")
sys.path.append(f"{pdk_root}/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append(
    f"{pdk_root}/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/"
)

import gdsfactory as gf
from sg13g2_pycell_lib.ihp.schottky_code import schottky as schottkyIHP

from .. import tech
from .utils import *


@gf.cell
def schottky(
    width: float = 1,
    length: float = 0.3,
    Nx: int = 1,
    Ny: int = 1,
) -> gf.Component:
    """Returns the IHP Schottky diode as a gdsfactory Component.

    Args:
        width: Width of a single diode cell in micrometers.
        length: Length of a single diode cell in micrometers.
        Nx: Number of diode cells in the x-direction.
        Ny: Number of diode cells in the y-direction.

    Returns:
        gdsfactory.Component: The generated Schottky diode layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "Display": "Selected",
        "model": tech.techParams["dschottky_model"],
        "w": width * 1e-6,
        "l": length * 1e-6,
        "Nx": Nx,
        "Ny": Ny,
        "m": 1,
    }

    c = generate_gf_from_ihp(
        cell_name="schottky", cell_params=params, function_name=schottkyIHP()
    )

    # add ports to the component
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal1pin),
        port_type="electrical",
        ports_on_short_side=False,
    )
    c.ports["e2"].center = (
        round(c.ports["e2"].center[0], 2),
        round(c.ports["e2"].center[1], 2),
    )
    gf.add_ports.add_ports_from_boxes(
        c,
        pin_layer=(tech.LAYER.Metal2pin),
        port_name_prefix="E",
        port_type="electrical",
        ports_on_short_side=False,
    )

    return c

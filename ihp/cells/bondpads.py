"""Bondpad components for IHP PDK."""

import os
import sys

pdk_root = os.environ.get("PDK_ROOT", "/foss/pdks")
sys.path.append(f"{pdk_root}/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append(
    f"{pdk_root}/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/"
)

from typing import Literal

import gdsfactory as gf
from sg13g2_pycell_lib.ihp.bondpad_code import bondpad as bondpadIHP

from ihp.cells.passives import guard_ring

from .. import tech
from .utils import *


@gf.cell
def bondpad(
    shape: Literal["octagon", "square", "circle"] = "octagon",
    stack: Literal["t", "nil"] = "t",
    fillMetals: Literal["t", "nil"] = "nil",
    flipChip: Literal["yes", "no"] = "no",
    diameter: float = 80.0,
    hwQuota: float = 1,
    topMetal: Literal["TM1", "TM2"] = "TM2",
    bottomMetal: Literal["1", "2", "3", "4", "5", "TM1"] = "3",
    addFillerEx: Literal["t", "nil"] = "nil",
    passEncl: float = 2.1,
    padType: Literal["bondpad", "probepad"] = "bondpad",
    ground_connection: Literal["psub", "nwell", False] = False,
) -> gf.Component:
    """Create a bondpad for wire bonding or flip-chip connection.

    This function generates a parametric bondpad with configurable shape,
    metal stack, size, passivation, filler, and flip-chip options.

    Args:
        shape: Shape of the bondpad. Options: 'octagon', 'square', 'circle'.
        stack: Stack all metal layers from bottom to top ('t' or 'nil').
        fillMetals: Add metal fill patterns ('t' for yes, 'nil' for no).
        flipChip: Enable flip-chip configuration ('yes' or 'no').
        diameter: Diameter or size of the bondpad in micrometers.
        hwQuota: Height/width quota for pad design rules.
        topMetal: Name of the top metal layer. Options: 'TM1', 'TM2'.
        bottomMetal: Name of the bottom metal layer. Options: '1', '2', '3', '4', '5', 'TM1'.
        addFillerEx: Exclude metal filler ('t' or 'nil').
        passEncl: Passivation enclosure around the pad, in micrometers.
        padType: Type of pad. Options: 'bondpad', 'probepad'.
        ground_connection: Add a guard ring under the pad to connect it to
            'psub' or 'nwell'. False adds no guard ring.

    Returns:
        gdsfactory.Component: The generated bondpad layout.
    """

    params = {
        "cdf_version": tech.techParams["CDFVersion"],
        "model": "bondpad",  # hardcoded for bondpad
        "Display": "Selected",
        "shape": shape,
        "stack": stack,
        "fill": fillMetals,
        "FlipChip": flipChip,
        "diameter": diameter * 1e-6,
        "hwquota": hwQuota,
        "topMetal": topMetal,
        "bottomMetal": bottomMetal,
        "addFillerEx": addFillerEx,
        "passEncl": passEncl * 1e-6,
        "padType": padType,
        "padPin": "PAD",
    }
    spacing_from_edge = 1.885  # manual measurement from the pad layout
    width = diameter * hwQuota - 2 * spacing_from_edge
    height = diameter - 2 * spacing_from_edge
    c = generate_gf_from_ihp(
        cell_name="bondpad", cell_params=params, function_name=bondpadIHP()
    )

    if ground_connection in ["psub", "nwell"]:
        # Add guard ring to connect ground to substrate
        c.center = c.center
        sub_ring = c.add_ref(
            guard_ring(width=height, height=width, guardRingType=ground_connection)
        )
        sub_ring.center = c.center
    return c


@gf.cell
def bondpad_array(
    width_signal: float = 85.0,
    width_ground: float = 85.0,
    length_signal: float = 85.0,
    length_ground: float = 85.0,
    pitch: float | list[float] = 125.0,
    config: str = "GSG",
    shape: Literal["octagon", "square", "circle"]
    | list[Literal["octagon", "square", "circle"]] = "square",
    signal_cross_section: str = "topmetal2_routing",
    ground_cross_section: str = "metal5_routing",
    padType: Literal["bondpad", "probepad"] = "bondpad",
    ground_connection: Literal["psub", "nwell", False] = False,
) -> gf.Component:
    """Create a linear array of bond or probe pads (e.g. a GSG configuration).

    One pad is placed per character in config. Signal pads ('S') use the
    signal dimensions and cross-section, all other pads use the ground
    dimensions and cross-section. Each pad is labeled with its config
    character and all ports face downwards.

    Args:
        width_signal: Width of the signal pads in micrometers.
        width_ground: Width of the ground pads in micrometers.
        length_signal: Length of the signal pads in micrometers.
        length_ground: Length of the ground pads in micrometers.
        pitch: Pad spacing in micrometers. A single value spaces all pads
            uniformly, a list gives the individual spacings between
            neighboring pads and must have one entry less than config.
        config: Pad sequence, one character per pad (e.g. "GSG").
        shape: Shape for all pads, or a list with one shape per pad.
        signal_cross_section: Cross-section connected to the signal pads.
        ground_cross_section: Cross-section connected to the ground pads.
        padType: Type of pad. Options: 'bondpad', 'probepad'.
        ground_connection: Add a guard ring under the ground pads to
            connect them to 'psub' or 'nwell'. False adds no guard ring.

    Returns:
        gdsfactory.Component: The generated pad array layout.
    """
    layer_dict = {
        tech.LAYER.TopMetal2drawing: "TM2",
        tech.LAYER.TopMetal1drawing: "TM1",
        tech.LAYER.Metal5drawing: "5",
        tech.LAYER.Metal4drawing: "4",
        tech.LAYER.Metal3drawing: "3",
        tech.LAYER.Metal2drawing: "2",
        tech.LAYER.Metal1drawing: "1",
    }

    c = gf.Component()
    pad_refs = []
    for i, conf in enumerate(config):
        # preprocess parameters
        # determine the width based on pad type
        width = width_signal if conf == "S" else width_ground
        length = length_signal if conf == "S" else length_ground
        hwQuota = length / width

        # Handle shape as a list of shapes or a single shape
        if isinstance(shape, list):
            shape_i = shape[i]
        else:
            shape_i = shape

        # Handle Layers
        if conf == "S":
            topMetal = layer_dict[tech.LAYER.TopMetal2drawing]
            if signal_cross_section == "topmetal2_routing":
                bottomMetal = layer_dict[tech.LAYER.TopMetal1drawing]
            else:
                bottomMetal = layer_dict[
                    gf.get_cross_section(signal_cross_section).layer
                ]
        else:
            topMetal = layer_dict[tech.LAYER.TopMetal2drawing]
            bottomMetal = layer_dict[gf.get_cross_section(ground_cross_section).layer]

        # handle pitch as a list of floats
        if isinstance(pitch, list):
            if len(pitch) + 1 != len(config):
                raise ValueError(
                    "Pitch must be a list of length one less than the number of pads in the config."
                )

            pad = bondpad(
                shape=shape_i,
                stack="t",
                diameter=width,
                hwQuota=hwQuota,
                topMetal=topMetal,
                bottomMetal=bottomMetal,
                padType=padType,
                ground_connection=ground_connection if config[i] == "G" else False,
            )
            pad_refs.append(c.add_ref(pad))
            if i > 0:
                pad_refs[-1].movey(sum(pitch[:i]))

        # handle pitch as a single float
        else:
            pad = bondpad(
                shape=shape_i,
                stack="t",
                diameter=width,
                hwQuota=hwQuota,
                topMetal=topMetal,
                bottomMetal=bottomMetal,
                padType=padType,
                ground_connection=ground_connection if config[i] == "G" else False,
            )
            pad_refs.append(c.add_ref(pad))
            if i > 0:
                pad_refs[-1].movex(i * pitch)

        c.add_ref(
            gf.components.text(config[i], size=length / 2, layer=tech.LAYER.TEXTdrawing)
        ).center = pad_refs[-1].center

    gf.add_ports.add_ports_from_boxes(
        c, pin_layer=tech.LAYER.TopMetal2drawing, port_type="electrical"
    )

    for port in c.ports:
        port.orientation = 270
        port.center = (
            port.center[0],
            port.center[1] - length_signal / 2,
        )  # move the port from the pad center to the lower pad edge
    return c


if __name__ == "__main__":
    # Test the components
    c1 = bondpad(shape="octagon")
    c1.show()

    c2 = bondpad(shape="square", flipChip="yes")
    c2.show()

    c3 = bondpad_array(config="GSGSG")
    c3.show()

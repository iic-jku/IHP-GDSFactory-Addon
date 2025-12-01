"""Bondpad components for IHP PDK."""

import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

from sg13g2_pycell_lib.ihp.bondpad_code import bondpad as bondpadIHP


import gdsfactory as gf

from .utils import *
from functools import partial
from .. import tech



@gf.cell
def bondpad(
    padType: str = "bondpad",
    diameter: float = 80.0,
    passEncl: float = 2.1,
    hwQuota: float = 1,
    shape: str = "octagon",
    topMetal: str = "TM2",
    bottomMetal: str = "3",
    stack: str = 't',
    fill: str = 'nil',
    flipChip: str = 'no',
    addFillerEx: str = 'nil',
) -> gf.Component:
    """Create a bondpad for wire bonding or flip-chip connection.

    Args:
        shape: Shape of the bondpad ("octagon", "square", or "circle").
        stack_metals: Stack all metal layers from bottom to top.
        fill_metals: Add metal fill patterns.
        flip_chip: Enable flip-chip configuration.
        diameter: Diameter or size of the bondpad in micrometers.
        top_metal: Top metal layer name.
        bottom_metal: Bottom metal layer name.

    Returns:
        Component with bondpad layout.
    """
    
    params = {
        'cdf_version': 8, 
        'model': "bondpad", # hardcoded for bondpad
        'Display': 'Selected',
        'shape': shape,
        'stack': stack,
        'fill': fill,
        'FlipChip': flipChip,
        'diameter': diameter*1e-6,
        'hwquota': hwQuota,
        'topMetal': topMetal,
        'bottomMetal': bottomMetal,
        'addFillerEx': addFillerEx,
        'passEncl': passEncl*1e-6,
        'padType' : padType,
        'padPin': 'PAD'   
    }

    c = generate_gf_from_ihp(cell_name="bondpad", cell_params=params, function_name=bondpadIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def bondpad_array(
    n_pads: int = 4,
    pad_pitch: float = 100.0,
    pad_diameter: float = 68.0,
    shape: str = "octagon",
    stack_metals: bool = True,
) -> gf.Component:
    """Create an array of bondpads.

    Args:
        n_pads: Number of bondpads.
        pad_pitch: Pitch between bondpad centers in micrometers.
        pad_diameter: Diameter of each bondpad in micrometers.
        shape: Shape of the bondpads.
        stack_metals: Stack all metal layers.

    Returns:
        Component with bondpad array.
    """
    c = gf.Component()

    for i in range(n_pads):
        pad = bondpad(
            shape=shape,
            stack=stack_metals,
            diameter=pad_diameter,
        )
        pad_ref = c.add_ref(pad)
        pad_ref.movex(i * pad_pitch)

        

    

    return c


if __name__ == "__main__":
    # Test the components
    c1 = bondpad(shape="octagon")
    c1.show()

    c2 = bondpad(shape="square", flip_chip=True)
    c2.show()

    c3 = bondpad_array(n_pads=6)
    c3.show()

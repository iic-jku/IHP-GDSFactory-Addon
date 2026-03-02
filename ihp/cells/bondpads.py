"""Bondpad components for IHP PDK."""

import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

from sg13g2_pycell_lib.ihp.bondpad_code import bondpad as bondpadIHP


import gdsfactory as gf
from typing import Literal

from .utils import *
from functools import partial
from .. import tech



@gf.cell
def bondpad(
    shape: Literal['octagon', 'square', 'circle'] = 'octagon',
    stack: Literal['t', 'nil'] = 't',
    fillMetals: Literal['t', 'nil'] = 'nil',
    flipChip: Literal['yes', 'no'] = 'no',
    diameter: float = 80.0,
    hwQuota: float = 1,
    topMetal: Literal['TM1', 'TM2'] = 'TM2',
    bottomMetal: Literal['1', '2', '3', '4', '5', 'TM1'] = '3',
    addFillerEx: Literal['t', 'nil'] = 'nil',
    passEncl: float = 2.1,
    padType: Literal['bondpad', 'probepad'] = 'bondpad',
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

    Returns:
        gdsfactory.Component: The generated bondpad layout.
    """

    
    params = {
        'cdf_version': tech.techParams['CDFVersion'], 
        'model': "bondpad", # hardcoded for bondpad
        'Display': 'Selected',
        'shape': shape,
        'stack': stack,
        'fill': fillMetals,
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
    shape: Literal['octagon', 'square', 'circle'] = "octagon",
    stack_metals: Literal['t', 'nil'] = 't'
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

    
@gf.cell
def probe_pads(
    width_signal: float = 85.0, 
    width_ground: float = 85.0, 
    length: float = 85.0,
    spacing: float | list[float] = 125.0,
    config: str = "GSG",
    shape: Literal['octagon', 'square', 'circle'] | list[Literal['octagon', 'square', 'circle']] = "square",
    signal_cross_section: str = "topmetal2_routing",
    ground_cross_section: str = "metal5_routing"
    ) -> gf.Component:
    
    
    
    layer_dict = {
        tech.LAYER.TopMetal2drawing: 'TM2',
        tech.LAYER.TopMetal1drawing: 'TM1',
        tech.LAYER.Metal5drawing: '5',
        tech.LAYER.Metal4drawing: '4',
        tech.LAYER.Metal3drawing: '3',
        tech.LAYER.Metal2drawing: '2',
        tech.LAYER.Metal1drawing: '1',
    }
    
    
    c = gf.Component()
    
    for i, pad_type in enumerate(config):
        
        ## Preprocessing parameters
        # Determine the width based on pad type
        width = width_signal if pad_type == 'S' else width_ground
        hwQuota = length / width
        
        # Handle shape as a list of shapes or a single shape
        if isinstance(shape, list):
            shape_i = shape[i]
        else:
            shape_i = shape
        
        # Handle Layers
        if pad_type == 'S':
            topMetal = layer_dict[tech.LAYER.TopMetal2drawing]
            if signal_cross_section == "topmetal2_routing":
                bottomMetal = layer_dict[tech.LAYER.TopMetal1drawing]
            else:
                bottomMetal = layer_dict[gf.get_cross_section(signal_cross_section).layer]
        else:
            topMetal = layer_dict[tech.LAYER.TopMetal2drawing]
            bottomMetal = layer_dict[gf.get_cross_section(ground_cross_section).layer]
            
        # handle spacing as a list of floats
        if isinstance(spacing, list):
            if len(spacing)+1 != len(config):
                raise ValueError("Spacing must be a list of length one less than the number of pads in the config.")
            
            pad = bondpad(
                shape=shape_i,
                stack='t',
                diameter=length* 1/hwQuota,
                hwQuota=hwQuota,
                topMetal=topMetal,
                bottomMetal=bottomMetal,
                padType='probepad',
            )
            pad_ref = c.add_ref(pad)
            if i > 0:
                pad_ref.movex(sum(spacing[:i]))
                       
        # handle spacing as a single float
        else:
            pad = bondpad(
                shape=shape_i,
                stack='t',
                diameter=length* 1/hwQuota,
                hwQuota=hwQuota,
                topMetal=topMetal,
                bottomMetal=bottomMetal,
                padType='probepad'
            )
            pad_ref = c.add_ref(pad)
            if i > 0:
                pad_ref.movex(i* spacing)
                
        prev_pad_ref = pad_ref
        # c.add_label(text=config[i], position=pad_ref.center)
        c.add_ref(gf.components.text(config[i], size=length/2, layer=tech.LAYER.TEXTdrawing)).center = pad_ref.center
        
    return c


if __name__ == "__main__":
    # Test the components
    c1 = bondpad(shape="octagon")
    c1.show()

    c2 = bondpad(shape="square", flip_chip=True)
    c2.show()

    c3 = bondpad_array(n_pads=6)
    c3.show()

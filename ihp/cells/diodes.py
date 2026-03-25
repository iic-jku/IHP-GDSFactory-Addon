"""Diode components for IHP PDK."""
import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

# from sg13g2_pycell_lib.ihp.utility_functions import eng_string_to_float, CbCapCalc

from sg13g2_pycell_lib.ihp.schottky_code import schottky as schottkyIHP


import gdsfactory as gf
# from typing import Literal

from .utils import *
# from functools import partial
from .. import tech



@gf.cell
def schottky(
    width: float = 1,
    length: float = 0.3,
    Nx: int = 1,
    Ny: int = 1,
) -> gf.Component:
    """Returns the IHP schottky diode as a gdsfactory Component.

    Returns:
        gdsfactory.Component: The generated schottky diode layout.
    """

    
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'model': tech.techParams['dschottky_model'],
        'w': width*1e-6,    
        'l': length*1e-6,  
        'Nx': Nx,
        'Ny': Ny, 
        'm': 1,
    }

    # add ports to the component
    c = generate_gf_from_ihp(cell_name="schottky", cell_params=params, function_name=schottkyIHP())
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.Metal1pin), port_type="electrical", ports_on_short_side=False)
    c.ports["e2"].center = (round(c.ports["e2"].center[0], 2), round(c.ports["e2"].center[1], 2))
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.Metal2pin), port_name_prefix="E", port_type="electrical", ports_on_short_side=False)
    # c.ports["e1"].name = "B"
    # c.ports["e2"].name = "C"
    # c.ports["e3"].name = "E"
    
    return c



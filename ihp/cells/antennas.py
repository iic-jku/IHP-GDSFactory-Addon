"""Antenna components for IHP PDK."""
import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

from sg13g2_pycell_lib.ihp.dantenna_code import dantenna as dantennaIHP
from sg13g2_pycell_lib.ihp.dpantenna_code import dpantenna as dpantennaIHP


import gdsfactory as gf

from .utils import *
from functools import partial
from .. import tech


@gf.cell
def dantenna(
    width: float = 0.78,
    length: float = 0.78,
    addRecLayer: str = 't',
    guardRingType: str = 'none',
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a 

    

    Args:
        

    Returns:
        gdsfactory.Component 
    """

    area = width*1e-6 * length*1e-6
    perimeter = 2 * (width*1e-6 + length*1e-6)
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': "Selected",
        'model': tech.techParams['dantenna_model'],
        'Calculate': 'a',
        'w': width*1e-6,
        'l': length*1e-6,
        'a': area,
        'p': perimeter,
        'addRecLayer': addRecLayer,
        'bn' : "sub!",
        'off' : False,
        'Vd' : '',
        'perim' : '',
        'm' : 1,
        'trise' : '',
        'region' : '',
        'dtemp' : '',
        'mode' : 'No',
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="dantenna", cell_params=params, function_name=dantennaIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def dpantenna(
    width: float = 0.78,
    length: float = 0.78,
    addRecLayer: str = 't',
    guardRingType: str = 'none',
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a 

    

    Args:
        

    Returns:
        gdsfactory.Component 
    """

    area = width*1e-6 * length*1e-6
    perimeter = 2 * (width*1e-6 + length*1e-6)
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': "Selected",
        'model': tech.techParams['dpantenna_model'],
        'Calculate': 'a',
        'w': width*1e-6,
        'l': length*1e-6,
        'a': area,
        'p': perimeter,
        'addRecLayer': addRecLayer,
        'bn' : "sub!",
        'off' : False,
        'Vd' : '',
        'perim' : '',
        'm' : 1,
        'trise' : '',
        'region' : '',
        'dtemp' : '',
        'mode' : 'No',
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="dpantenna", cell_params=params, function_name=dpantennaIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c

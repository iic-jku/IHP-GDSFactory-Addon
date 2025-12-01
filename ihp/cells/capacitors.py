"""Capacitor components for IHP PDK."""
import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

from sg13g2_pycell_lib.ihp.utility_functions import eng_string_to_float, CbCapCalc

from sg13g2_pycell_lib.ihp.cmim_code import cmim as cmimIHP
from sg13g2_pycell_lib.ihp.rfcmim_code import rfcmim as rfcmimIHP
from sg13g2_pycell_lib.ihp.SVaricap_code import SVaricap as SVaricapIHP


import gdsfactory as gf

from .utils import *
from functools import partial
from .. import tech

@gf.cell
def cmim(
    width = 6.99,
    length = 6.99,
    guardRingType = 'none',
    guardRingDistance = 1,
) -> gf.Component:
    """Create a MIM (Metal-Insulator-Metal) capacitor.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        #TODO

    Returns:
        Component with MIM capacitor layout.
    """

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'Calculate': "w&l",
        'model': tech.techParams['cmim_model'],
        'C': CbCapCalc('C', 0, width*1e-6, length*1e-6, 'cmim'),    # TODO Is this used?
        'w': width*1e-6,    # Width in μm
        'l': length*1e-6,   # Length in μm
        'Cspec': eng_string_to_float(tech.techParams['cmim_caspec']),     # Number of gates
        'Wmin': eng_string_to_float(tech.techParams['cmim_minLW']),
        'Lmin': eng_string_to_float(tech.techParams['cmim_minLW']),
        'Cmax': eng_string_to_float(tech.techParams['cmim_maxC']),
        'ic': "",
        'm': 1,      # Multiplier
        'trise': "",
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="cmim", cell_params=params, function_name=cmimIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def rfcmim(
    width: float = 7,
    length: float = 7,
    capacitance: float = 74.8,
    feed_width: float = 3,
    guardRingType: str = 'none',
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create an RF MIM capacitor with optimized layout.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        capacitance: Target capacitance in fF (optional).
        #TODO

    Returns:
        Component with RF MIM capacitor layout.
    """

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'Calculate': "C",
        'model': tech.techParams['rfcmim_model'],
        'C': CbCapCalc('C', 0, width*1e-6, length*1e-6, 'rfcmim'),    # TODO Is this used?
        'w': width*1e-6,    # Width in μm
        'l': length*1e-6,   # Length in μm
        'wfeed': feed_width*1e-6,
        'Cspec': eng_string_to_float(tech.techParams['rfcmim_caspec']),     # Number of gates
        'Wmin': eng_string_to_float(tech.techParams['rfcmim_minLW']),
        'Lmin': eng_string_to_float(tech.techParams['rfcmim_minLW']),
        'Cmax': eng_string_to_float(tech.techParams['rfcmim_maxC']),
        'ic': "",
        'm': 1,      # Multiplier
        'trise': "",
    }

    c = generate_gf_from_ihp(cell_name="rfcmim", cell_params=params, function_name=rfcmimIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def svaricap(
    width: float = '9.74u',
    length: float = '0.8u',
    Nx: int = 1,
    guardRingType: str = 'none',
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a MOS varicap (variable capacitor).

    Args:
        width: Width of the varicap in micrometers.
        length: Length of the varicap in micrometers.
        nf: Number of fingers.
        model: Device model name.

    Returns:
        Component with varicap layout.
    """

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'model': tech.techParams['SVaricap_model'],
        'w': width,    # Width in μm
        'l': length,   # Length in μm
        'Nx': Nx,
        'bn': "sub!",      
        'trise': "",
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="svaricap", cell_params=params, function_name=SVaricapIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


if __name__ == "__main__":
    # Test the components
    c1 = cmim(width=10, length=10)
    c1.show()

    c2 = rfcmim(width=20, length=20)
    c2.show()

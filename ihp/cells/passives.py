"""Passive components (varicaps, ESD, taps, seal rings) for IHP PDK."""
import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

from sg13g2_pycell_lib.ihp.utility_functions import eng_string_to_float, CbTapCalc

from sg13g2_pycell_lib.ihp.esd_code import esd as esdIHP
from sg13g2_pycell_lib.ihp.ptap1_code import ptap1 as ptap1IHP
from sg13g2_pycell_lib.ihp.ntap1_code import ntap1 as ntap1IHP
from sg13g2_pycell_lib.ihp.sealring_code import sealring as sealringIHP


import gdsfactory as gf

from .utils import *
from functools import partial
from .. import tech



@gf.cell
def esd(
    model: str = "diodevdd_2kv",
) -> gf.Component:
    """Create an ESD protection NMOS device.

    Args:
        model: Device model name.

    Returns:
        Component with ESD NMOS layout.
    """

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'model': model
    }

    c = generate_gf_from_ihp(cell_name="esd", cell_params=params, function_name=esdIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c



@gf.cell
def ptap1(
    width = 0.78,
    length = 0.78,
    ) -> gf.Component:
    """Create a P+ substrate tap.

    Args:
        width: Width of the tap in micrometers.
        length: Length of the tap in micrometers.
        rows: Number of contact rows.
        cols: Number of contact columns.

    Returns:
        Component with P+ tap layout.
    """
    area = width * length
    perimeter = 2 * (width + length)
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'Calculate': "R,A",
        'R': CbTapCalc('R', 0, length*1e-6, width*1e-6, 'ptap1'),    # TODO Is this used?
        'w': width*1e-6,    # Length in μm
        'l': length*1e-6,   # Length in μm
        'A': area,
        'Perim': perimeter,
        'Rspec': 0.980*1e-9,    # hardcoded in the PCell
        'Wmin': eng_string_to_float(tech.techParams['ptap1_minLW']),
        'Lmin': eng_string_to_float(tech.techParams['ptap1_minLW']),
        'm': 1
        
    }

    c = generate_gf_from_ihp(cell_name="ptap1", cell_params=params, function_name=ptap1IHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def ntap1(
    width = 0.78,
    length = 0.78,
) -> gf.Component:
    """Create an N+ substrate tap.

    Args:
        width: Width of the tap in micrometers.
        length: Length of the tap in micrometers.
        rows: Number of contact rows.
        cols: Number of contact columns.

    Returns:
        Component with N+ tap layout.
    """
    area = width * length
    perimeter = 2 * (width + length)
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'Calculate': "R,A",
        'R': CbTapCalc('R', 0, length*1e-6, width*1e-6, 'ntap1'),    # TODO Is this used?
        'w': width*1e-6,    # Length in μm
        'l': length*1e-6,   # Length in μm
        'A': area,
        'Perim': perimeter,
        'Rspec': 0.980*1e-9,    # hardcoded in the PCell
        'Wmin': eng_string_to_float(tech.techParams['ntap1_minLW']),
        'Lmin': eng_string_to_float(tech.techParams['ntap1_minLW']),
        'm': 1
        
    }

    c = generate_gf_from_ihp(cell_name="ntap1", cell_params=params, function_name=ntap1IHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c



@gf.cell
def sealring(
    width: float = 400.0,
    height: float = 400.0,
    addLabel: str = "nil",
    addSlit: str = "nil",
    edgeBox: float = 25.0,
) -> gf.Component:
    """Create a seal ring for die protection.

    Args:
        width: Inner width of the seal ring in micrometers.
        height: Inner height of the seal ring in micrometers.
        ring_width: Width of the seal ring metal in micrometers.

    Returns:
        Component with seal ring layout.
    """

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'l': width*1e-6,    # Length in μm
        'w': height*1e-6,   # Length in μm
        'addLabel': addLabel,
        'addSlit': addSlit,
        'Wmin': eng_string_to_float(tech.techParams['sealring_complete_minW']),
        'Lmin': eng_string_to_float(tech.techParams['sealring_complete_minL']),
        'edgeBox': edgeBox*1e-6
    }

    c = generate_gf_from_ihp(cell_name="sealring", cell_params=params, function_name=sealringIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


if __name__ == "__main__":
    # Test the components

    c2 = esd(width=100.0, length=0.5, nf=20)
    c2.show()

    c3 = ptap1(width=2.0, length=2.0, rows=2, cols=2)
    c3.show()

    c4 = sealring(width=500, height=500, ring_width=10)
    c4.show()

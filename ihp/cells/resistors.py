"""Resistor components for IHP PDK."""
import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

from sg13g2_pycell_lib.ihp.utility_functions import eng_string_to_float, CbResCalc, CbResCurrent

from sg13g2_pycell_lib.ihp.rhigh_code import rhigh as rhighIHP
from sg13g2_pycell_lib.ihp.rppd_code import rppd as rppdIHP
from sg13g2_pycell_lib.ihp.rsil_code import rsil as rsilIHP


import gdsfactory as gf

from .utils import *
from functools import partial
from .. import tech


@gf.cell
def rhigh(
    length = 0.96,
    width = 0.5,
    bends = 0,
    polySpace = 0.18,
    numberOfSegments = 1,
    segmentConnection = 'Serial',
    segmentSpacing = 2,
    guardRingType = 'none',
    guardRingDistance = 1,
) -> gf.Component:
    """Create a high-resistance polysilicon resistor.

    Args:
        width: Width of the resistor in micrometers.
        length: Length of the resistor in micrometers.
        #TODO

    Returns:
        Component with high-resistance poly resistor layout.
    """
    

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'Calculate': 'l',       # TODO check what to do
        'Recommendation': "No",
        'model': tech.techParams['rhigh_model'],
        'R': CbResCalc('R', 0, length*1e-6, width*1e-6, bends, polySpace*1e-6, 'rhigh'),    # TODO Is this used?
        'w': width*1e-6,    # Length in μm
        'l': length*1e-6,   # Length in μm
        'b': bends,
        'ps': polySpace*1e-6,
        'Imax': CbResCurrent(width*1e-6, tech.techParams['epsilon2'], 'rhighG2'), # TODO Is this used?
        'bn': "sub!",
        'Wmin': eng_string_to_float(tech.techParams['rhigh_minW'])*1e-6,
        'Lmin': eng_string_to_float(tech.techParams['rhigh_minL'])*1e-6,
        'PSmin': eng_string_to_float(tech.techParams['rhigh_minPS'])*1e-6,
        'Rspec': tech.techParams['rhigh_rspec'],
        'Rkspec': tech.techParams['rhigh_rkspec'],
        'Rzspec': tech.techParams['rhigh_rzspec'],
        'tc1': -2300e-6,    # hardcoded in the PCell
        'tc2': 2.1e-6,    # hardcoded in the PCell
        'PWB': "No",
        'm': 1,      # Multiplier
        'trise': 0,
        'NumberOfSegments': numberOfSegments,
        'SegmentConnection': segmentConnection,
        'SegmentSpacing': segmentSpacing*1e-6,
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="rhigh", cell_params=params, function_name=rhighIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def rppd(
    length = 0.5,
    width = 0.5,
    bends = 0,
    polySpace = 0.18,
    numberOfSegments = 1,
    segmentConnection = 'Serial',
    segmentSpacing = 2,
    guardRingType = 'none',
    guardRingDistance = 1, 
) -> gf.Component:
    """Create a high-resistance polysilicon resistor.

    Args:
        width: Width of the resistor in micrometers.
        length: Length of the resistor in micrometers.
        #TODO

    Returns:
        Component with high-resistance poly resistor layout.
    """
    

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'Calculate': 'l',       # TODO check what to do
        'Recommendation': "No",
        'model': tech.techParams['rppd_model'],
        'R': CbResCalc('R', 0, length*1e-6, width*1e-6, bends, polySpace*1e-6, 'rppd'),    # TODO Is this used?
        'w': width*1e-6,    # Length in μm
        'l': length*1e-6,   # Length in μm
        'b': bends,
        'ps': polySpace*1e-6,
        'Imax': CbResCurrent(width*1e-6, tech.techParams['epsilon2'], 'rppdG2'), # TODO Is this used?
        'bn': "sub!",
        'Wmin': eng_string_to_float(tech.techParams['rppd_minW'])*1e-6,
        'Lmin': eng_string_to_float(tech.techParams['rppd_minL'])*1e-6,
        'PSmin': eng_string_to_float(tech.techParams['rppd_minPS'])*1e-6,
        'Rspec': tech.techParams['rppd_rspec'],
        'Rkspec': tech.techParams['rppd_rkspec'],
        'Rzspec': tech.techParams['rppd_rzspec'],
        'tc1': -170e-6,    # hardcoded in the PCell
        'tc2': 0.4e-6,    # hardcoded in the PCell
        'PWB': "No",
        'm': 1,      # Multiplier
        'trise': 0,
        'NumberOfSegments': numberOfSegments,
        'SegmentConnection': segmentConnection,
        'SegmentSpacing': segmentSpacing*1e-6,
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="rppd", cell_params=params, function_name=rppdIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def rsil(
    length = 0.5,
    width = 0.5,
    polySpace = 0.18,
    resistance = 24.9,
    numberOfSegments = 1,
    segmentConnection = 'Serial',
    segmentSpacing = 2,
    guardRingType = 'none',
    guardRingDistance = 1, 
) -> gf.Component:
    

    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'Display': 'Selected',
        'Calculate': 'l',       # TODO check what to do
        'Recommendation': "No",
        'model': tech.techParams['rsil_model'],
        'R': resistance,    # TODO IHP function defines it as user parameter but also calculates it
        'w': width*1e-6,    # Length in μm
        'l': length*1e-6,   # Length in μm
        'ps': polySpace*1e-6,
        'Imax': CbResCurrent(width*1e-6, tech.techParams['epsilon2'], 'rsilG2'), # TODO Is this used?
        'bn': "sub!",
        'Wmin': eng_string_to_float(tech.techParams['rsil_minW'])*1e-6,
        'Lmin': eng_string_to_float(tech.techParams['rsil_minL'])*1e-6,
        'PSmin': eng_string_to_float(tech.techParams['rsil_minPS'])*1e-6,
        'Rspec': tech.techParams['rsil_rspec'],
        'Rkspec': tech.techParams['rsil_rkspec'],
        'Rzspec': tech.techParams['rsil_rzspec'],
        'tc1': -170e-6,    # hardcoded in the PCell
        'tc2': 0.4e-6,    # hardcoded in the PCell
        'PWB': "No",
        'm': 1,      # Multiplier
        'trise': 0,
        'NumberOfSegments': numberOfSegments,
        'SegmentConnection': segmentConnection,
        'SegmentSpacing': segmentSpacing*1e-6,
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="rsil", cell_params=params, function_name=rsilIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


if __name__ == "__main__":
    # Test the components
    c1 = rsil(width=1.0, length=10.0)
    c1.show()

    c2 = rppd(width=0.8, length=20.0)
    c2.show()

    c3 = rhigh(width=1.4, length=50.0)
    c3.show()

import sys
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python")
sys.path.append("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/")

from sg13g2_pycell_lib.ihp.utility_functions import eng_string_to_float

from sg13g2_pycell_lib.ihp.nmos_code import nmos as nmosIHP
from sg13g2_pycell_lib.ihp.nmosHV_code import nmosHV as nmosHVIHP
from sg13g2_pycell_lib.ihp.pmos_code import pmos as pmosIHP
from sg13g2_pycell_lib.ihp.pmosHV_code import pmosHV as pmosHVIHP
from sg13g2_pycell_lib.ihp.rfnmos_code import rfnmos as rfnmosIHP
from sg13g2_pycell_lib.ihp.rfnmosHV_code import rfnmosHV as rfnmosHVIHP
from sg13g2_pycell_lib.ihp.rfpmos_code import rfpmos as rfpmosIHP
from sg13g2_pycell_lib.ihp.rfpmosHV_code import rfpmosHV as rfpmosHVIHP


import gdsfactory as gf
from typing import Literal

from .utils import *
from functools import partial
from .. import tech


@gf.cell
def nmos(
    w: float = 0.15, 
    l: float = 0.13, 
    ng: int = 1,
    guardRingType: Literal['none', 'psub'] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create an NMOS transistor layout.

    This function generates a parametric NMOS transistor with configurable
    width, length, number of gates/fingers, and optional P-substrate guard ring.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Spacing between the transistor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated NMOS transistor layout.
    """
   
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'model': tech.techParams['nmos_model'],
        'w': w*1e-6,    # Width in μm
        'ws': eng_string_to_float(tech.techParams['nmos_defW'])/eng_string_to_float(tech.techParams['nmos_defNG']),   # Single Width in nm
        'l': l*1e-6,   # Length in μm
        'ng': ng,     # Number of gates
        'm': 1,      # Multiplier
        'Wmin': eng_string_to_float(tech.techParams['nmos_minW']),
        'Lmin': eng_string_to_float(tech.techParams['nmos_minL']),
        'trise': '',
        'Display': 'Selected',
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="nmos", cell_params=params, function_name=nmosIHP())
    
    # add ports
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.Metal1drawing), port_type="electrical", port_name_prefix='DS_', ports_on_short_side=True, auto_rename_ports=False)
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.GatPolydrawing), port_type="electrical", port_name_prefix="G_", ports_on_short_side=True, auto_rename_ports=False)
    return c

@gf.cell
def nmosHV(
    w: float = 0.60, 
    l: float = 0.45, 
    ng: int = 1, 
    guardRingType: Literal['none', 'psub'] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a high-voltage NMOS transistor layout.

    This function generates a parametric high-voltage NMOS transistor with
    configurable width, length, number of gates/fingers, and optional
    P-substrate guard ring.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Spacing between the transistor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated high-voltage NMOS transistor layout.
    """
    
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'model': tech.techParams['nmosHV_model'],
        'w': w*1e-6,    # Width in μm
        'ws': eng_string_to_float(tech.techParams['nmosHV_defW'])/eng_string_to_float(tech.techParams['nmosHV_defNG']),   # Single Width in nm
        'l': l*1e-6,   # Length in μm
        'ng': ng,     # Number of gates
        'm': 1,      # Multiplier
        'Wmin': eng_string_to_float(tech.techParams['nmosHV_minW']),
        'Lmin': eng_string_to_float(tech.techParams['nmosHV_minL']),
        'trise': '',
        'Display': 'Selected',
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="nmosHV", cell_params=params, function_name=nmosHVIHP())
    
    # add ports
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.Metal1drawing), port_type="electrical", port_name_prefix='DS_', ports_on_short_side=True, auto_rename_ports=False)
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.GatPolydrawing), port_type="electrical", port_name_prefix="G_", ports_on_short_side=True, auto_rename_ports=False)
    
    return c



@gf.cell
def pmos(
    w: float = 0.15, 
    l: float = 0.13, 
    ng: int = 1,
    guardRingType: Literal['none', 'nwell'] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a PMOS transistor layout.

    This function generates a parametric PMOS transistor with configurable
    width, length, number of gates/fingers, and optional guard ring.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'nwell': N-well guard ring.
        guardRingDistance: Spacing between the transistor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated PMOS transistor layout.
    """
    
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'model': tech.techParams['pmos_model'],
        'w': w*1e-6,    # Width in μm
        'ws': eng_string_to_float(tech.techParams['pmos_defW'])/eng_string_to_float(tech.techParams['pmos_defNG']),   # Single Width in nm
        'l': l*1e-6,   # Length in μm
        'ng': ng,     # Number of gates
        'm': 1,      # Multiplier
        'Wmin': eng_string_to_float(tech.techParams['pmos_minW']),
        'Lmin': eng_string_to_float(tech.techParams['pmos_minL']),
        'trise': '',
        'Display': 'Selected',
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="pmos", cell_params=params, function_name=pmosIHP())
    
    # add ports
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.Metal1drawing), port_type="electrical", port_name_prefix='DS_', ports_on_short_side=True, auto_rename_ports=False)
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.GatPolydrawing), port_type="electrical", port_name_prefix="G_", ports_on_short_side=True, auto_rename_ports=False)
    return c


@gf.cell
def pmosHV(
    w: float = 0.30, 
    l: float = 0.40, 
    ng: int = 1,
    guardRingType: Literal['none', 'psub'] = "none",
    guardRingDistance: float = 1,
) -> gf.Component:
    """Create a high-voltage PMOS (PMOSHV) transistor layout.

    This function generates a parametric high-voltage PMOS transistor with
    configurable width, length, number of gates/fingers, and optional
    P-substrate guard ring.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        guardRingType: Type of guard ring to include. Options:
            - 'none': No guard ring.
            - 'psub': P-substrate guard ring.
        guardRingDistance: Spacing between the transistor and the guard ring, in micrometers.

    Returns:
        gdsfactory.Component: The generated high-voltage PMOS transistor layout.
    """
    
    params = {
        'cdf_version': tech.techParams['CDFVersion'],
        'model': tech.techParams['pmosHV_model'],
        'w': w*1e-6,    # Width in μm
        'ws': eng_string_to_float(tech.techParams['pmosHV_defW'])/eng_string_to_float(tech.techParams['pmosHV_defNG']),   # Single Width in nm
        'l': l*1e-6,   # Length in μm
        'ng': ng,     # Number of gates
        'm': 1,      # Multiplier
        'Wmin': eng_string_to_float(tech.techParams['pmosHV_minW']),
        'Lmin': eng_string_to_float(tech.techParams['pmosHV_minL']),
        'trise': '',
        'Display': 'Selected',
        'guardRingType': guardRingType,
        'guardRingDistance': guardRingDistance*1e-6,
    }

    c = generate_gf_from_ihp(cell_name="pmosHV", cell_params=params, function_name=pmosHVIHP())
    
    # add ports
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.Metal1drawing), port_type="electrical", port_name_prefix='DS_', ports_on_short_side=True, auto_rename_ports=False)
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.GatPolydrawing), port_type="electrical", port_name_prefix="G_", ports_on_short_side=True, auto_rename_ports=False)
    return c    


@gf.cell
def rfnmos(
    w: float = 1.0,
    l: float = 0.72,
    ng: int = 1,
    cnt_rows: int = 1,
    Met2Cont: Literal['Yes', 'No'] = "Yes",
    gat_ring: Literal['Yes', 'No'] = "Yes",
    guard_ring: Literal['Yes', 'No', 'U', 'Top+Bottom'] = "Yes",
) -> gf.Component:
    """Create an RF NMOS transistor layout.

    This function generates a parametric RF NMOS transistor with configurable
    width, length, number of gates/fingers, number of rows, and optional
    contacts and guard structures.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        cnt_rows: Number of transistor rows (vertical stacking of fingers).
        Met2Cont: Include Metal2-to-contact connection. Options: 'Yes' or 'No'.
        gat_ring: Include gate ring around the transistor. Options: 'Yes' or 'No'.
        guard_ring: Include guard ring around the transistor. Options:
            - 'U': U-shaped guard ring (One side stays open).
            - 'Top+Bottom': Guard ring on top and bottom (North/South).
            - 'Yes': Default guard ring.
            - 'No': No guard ring.

    Returns:
        gdsfactory.Component: The generated RF NMOS transistor layout.
    """
    
    params = {       
        'cdf_version': tech.techParams['CDFVersion'], 
        'rfmode': 1,
        'model': tech.techParams['rfnmos_model'],
        'w': w*1e-6,    # Width in μm
        'ws': eng_string_to_float(tech.techParams['rfnmos_defW'])/eng_string_to_float(tech.techParams['rfnmos_defNG'])*1e-6,   # Single Width in nm
        'l': l*1e-6,   # Length in μm
        'ng': ng,     # Number of gates
        'calculate': True,
        'cnt_rows': cnt_rows,
        'Met2Cont': Met2Cont,
        'gat_ring': gat_ring,
        'guard_ring': guard_ring,
        'Wmin': eng_string_to_float(tech.techParams['rfnmos_minW']),
        'Lmin': eng_string_to_float(tech.techParams['rfnmos_minL']),
        'm': 1,
        'trise': '',
        'Display': 'Selected'
    }

    c = generate_gf_from_ihp(cell_name="rfnmos", cell_params=params, function_name=rfnmosIHP())
    
    # add ports
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.Metal1drawing), port_type="electrical", port_name_prefix='DS_', ports_on_short_side=True, auto_rename_ports=False)
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    for i, port in enumerate(c.ports):
        port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
        
    gf.add_ports.add_ports_from_boxes(c, pin_layer=(tech.LAYER.GatPolydrawing), port_type="electrical", port_name_prefix="G_", ports_on_short_side=True, auto_rename_ports=False)
    return c


@gf.cell
def rfnmosHV(
    w: float = 1.0,
    l: float = 0.72,
    ng: int = 1,
    cnt_rows: int = 1,
    Met2Cont: Literal['Yes', 'No'] = "Yes",
    gat_ring: Literal['Yes', 'No'] = "Yes",
    guard_ring: Literal['Yes', 'No', 'U', 'Top+Bottom'] = "Yes",
) -> gf.Component:
    """Create a high-voltage RF NMOS (rfnmosHV) transistor layout.

    This function generates a parametric high-voltage RF NMOS transistor with
    configurable width, length, number of gates/fingers, number of rows, and
    optional contacts, gate ring, and guard ring structures.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        cnt_rows: Number of transistor rows (vertical stacking of fingers).
        Met2Cont: Include Metal2-to-contact connection. Options: 'Yes' or 'No'.
        gat_ring: Include gate ring around the transistor. Options: 'Yes' or 'No'.
        guard_ring: Include guard ring around the transistor. Options:
            - 'U': U-shaped guard ring (One side stays open).
            - 'Top+Bottom': Guard ring on top and bottom (North/South).
            - 'Yes': Default guard ring.
            - 'No': No guard ring.

    Returns:
        gdsfactory.Component: The generated high-voltage RF NMOS transistor layout.
    """
    
    params = {       
        'cdf_version': tech.techParams['CDFVersion'], 
        'rfmode': 1,
        'model': tech.techParams['rfnmosHV_model'],
        'w': w*1e-6,    # Width in μm
        'ws': eng_string_to_float(tech.techParams['rfnmosHV_defW'])/eng_string_to_float(tech.techParams['rfnmosHV_defNG'])*1e-6,   # Single Width in nm
        'l': l*1e-6,   # Length in μm
        'ng': ng,     # Number of gates
        'calculate': True,
        'cnt_rows': cnt_rows,
        'Met2Cont': Met2Cont,
        'gat_ring': gat_ring,
        'guard_ring': guard_ring,
        'Wmin': eng_string_to_float(tech.techParams['rfnmosHV_minW']),
        'Lmin': eng_string_to_float(tech.techParams['rfnmosHV_minL']),
        'm': 1,
        'trise': '',
        'Display': 'Selected'
    }

    c = generate_gf_from_ihp(cell_name="rfnmosHV", cell_params=params, function_name=rfnmosHVIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c


@gf.cell
def rfpmos(
    w: float = 1.0,
    l: float = 0.72,
    ng: int = 1,
    cnt_rows: int = 1,
    Met2Cont: Literal['Yes', 'No'] = "Yes",
    gat_ring: Literal['Yes', 'No'] = "Yes",
    guard_ring: Literal['Yes', 'No', 'U', 'Top+Bottom'] = "Yes",
) -> gf.Component:
    """Create an RF PMOS transistor layout.

    This function generates a parametric RF PMOS transistor with configurable
    width, length, number of gates/fingers, number of rows, and optional
    contacts, gate ring, and guard ring structures.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        cnt_rows: Number of transistor rows (vertical stacking of fingers).
        Met2Cont: Include Metal2-to-contact connection. Options: 'Yes' or 'No'.
        gat_ring: Include gate ring around the transistor. Options: 'Yes' or 'No'.
        guard_ring: Include guard ring around the transistor. Options:
            - 'U': U-shaped guard ring (One side stays open).
            - 'Top+Bottom': Guard ring on top and bottom (North/South).
            - 'Yes': Default guard ring.
            - 'No': No guard ring.

    Returns:
        gdsfactory.Component: The generated RF PMOS transistor layout.
    """

    
    params = {       
        'cdf_version': tech.techParams['CDFVersion'], 
        'rfmode': 1,
        'model': tech.techParams['rfpmos_model'],
        'w': w*1e-6,    # Width in μm
        'ws': eng_string_to_float(tech.techParams['rfpmos_defW'])/eng_string_to_float(tech.techParams['rfpmos_defNG'])*1e-6,   # Single Width in nm
        'l': l*1e-6,   # Length in μm
        'ng': ng,     # Number of gates
        'calculate': True,
        'cnt_rows': cnt_rows,
        'Met2Cont': Met2Cont,
        'gat_ring': gat_ring,
        'guard_ring': guard_ring,
        'Wmin': eng_string_to_float(tech.techParams['rfpmos_minW']),
        'Lmin': eng_string_to_float(tech.techParams['rfpmos_minL']),
        'm': 1,
        'trise': '',
        'Display': 'Selected'
    }

    c = generate_gf_from_ihp(cell_name="rfpmos", cell_params=params, function_name=rfpmosIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c

@gf.cell
def rfpmosHV(
    w: float = 1.0,
    l: float = 0.72,
    ng: int = 1,
    cnt_rows: int = 1,
    Met2Cont: Literal['Yes', 'No'] = "Yes",
    gat_ring: Literal['Yes', 'No'] = "Yes",
    guard_ring: Literal['Yes', 'No', 'U', 'Top+Bottom'] = "Yes",
) -> gf.Component:
    """Create a high-voltage RF PMOS (rfpmosHV) transistor layout.

    This function generates a parametric high-voltage RF PMOS transistor with
    configurable width, length, number of gates/fingers, number of rows, and
    optional contacts, gate ring, and guard ring structures.

    Args:
        w: Total width of the transistor in micrometers.
        l: Length of the transistor in micrometers.
        ng: Number of gates/fingers.
        cnt_rows: Number of transistor rows (vertical stacking of fingers).
        Met2Cont: Include Metal2-to-contact connection. Options: 'Yes' or 'No'.
        gat_ring: Include gate ring around the transistor. Options: 'Yes' or 'No'.
        guard_ring: Include guard ring around the transistor. Options:
            - 'U': U-shaped guard ring (One side stays open).
            - 'Top+Bottom': Guard ring on top and bottom (North/South).
            - 'Yes': Default guard ring.
            - 'No': No guard ring.

    Returns:
        gdsfactory.Component: The generated high-voltage RF PMOS transistor layout.
    """

    
    params = {       
        'cdf_version': tech.techParams['CDFVersion'], 
        'rfmode': 1,
        'model': tech.techParams['rfpmosHV_model'],
        'w': w*1e-6,    # Width in μm
        'ws': eng_string_to_float(tech.techParams['rfpmosHV_defW'])/eng_string_to_float(tech.techParams['rfpmosHV_defNG'])*1e-6,   # Single Width in nm
        'l': l*1e-6,   # Length in μm
        'ng': ng,     # Number of gates
        'calculate': True,
        'cnt_rows': cnt_rows,
        'Met2Cont': Met2Cont,
        'gat_ring': gat_ring,
        'guard_ring': guard_ring,
        'Wmin': eng_string_to_float(tech.techParams['rfpmosHV_minW']),
        'Lmin': eng_string_to_float(tech.techParams['rfpmosHV_minL']),
        'm': 1,
        'trise': '',
        'Display': 'Selected'
    }

    c = generate_gf_from_ihp(cell_name="rfpmosHV", cell_params=params, function_name=rfpmosHVIHP())
    # Adjust port orientations, for metal1 so every other port points in the opposite direction
    # for i, port in enumerate(c.ports):
    #     port.orientation = 90 if port.name.startswith("DS_") and i % 2 == 1 else port.orientation
    return c
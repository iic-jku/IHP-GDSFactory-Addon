"""Helpers to wrap the original IHP PyCells into gdsfactory Components."""

import os
import sys

_pdk_root = os.environ.get("PDK_ROOT", "/foss/pdks")
sys.path.append(os.path.join(_pdk_root, "ihp-sg13g2/libs.tech/klayout/python"))
sys.path.append(
    os.path.join(
        _pdk_root,
        "ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/",
    )
)

import gdsfactory as gf  # to have gf.Component
import pya  # KLayout Python API
from cni.dlo import PCellWrapper  # to wrap the PyCell
from cni.tech import Tech  # to get the technology


def generate_gf_from_ihp(cell_name, cell_params, function_name) -> gf.Component:
    """Instantiate an IHP PyCell and import the result as a gdsfactory Component.

    Args:
        cell_name: Name of the KLayout cell to create.
        cell_params: Dictionary with all parameter values expected by the PyCell.
        function_name: Instance of the IHP PyCell implementation class.

    Returns:
        gf.Component: The imported PyCell layout.
    """
    # ----------------------------------------------------------------
    # Step 1: Get the technology object
    # ----------------------------------------------------------------
    tech = Tech.get("SG13_dev")  # Must match the name registered in SG13_Tech

    # ----------------------------------------------------------------
    # Step 2: Create a layout and a cell
    # ----------------------------------------------------------------
    layout = pya.Layout()  # new empty layout
    cell = layout.create_cell(cell_name)  # new cell for your transistor

    # ----------------------------------------------------------------
    # Step 3: Wrap the PyCell
    # ----------------------------------------------------------------
    # PCellWrapper acts like the 'specs' object in KLayout
    # It handles parameter declarations and calls defineParamSpecs internally
    device = PCellWrapper(impl=function_name, tech=tech)

    # Convert params into a list in the order of device.param_decls
    param_values = [cell_params[p.name] for p in device.get_parameters()]

    # ----------------------------------------------------------------
    # Step 4: Produce the layout
    # ----------------------------------------------------------------
    device.produce(
        layout=layout,
        layers={},  # can pass layer map if needed
        parameters=param_values,
        cell=cell,
    )

    # ----------------------------------------------------------------
    # Step 5: Bring to GDSFactory
    # ----------------------------------------------------------------
    layout.write("temp.gds")
    print(f"{cell_name} PyCell placed successfully and GDS written.")
    c = gf.read.import_gds(gdspath="temp.gds")
    os.remove("temp.gds")
    # ----------------------------------------------------------------

    return c


def add_port_group(c: gf.Component, ref, ports: list, prefix: str = ""):
    """Add a group of ports from a reference to a component, with an optional prefix.

    Every name in ports must exist in ref.ports. The port objects are not
    deep-copied, the same ref.ports[p] objects are attached to c under
    their new names.

    Args:
        c: Component to which the ports are added.
        ref: Component reference from which the ports are copied.
        ports: Port names to copy from ref to c.
        prefix: String to prepend to each added port name.

    Returns:
        gf.Component: The component c with the copied ports added.
    """
    for p in ports:
        c.add_port(name=prefix + p, port=ref.ports[p])

    return c


def change_port_orientation(c: gf.Component, ports, orientation: int):
    """Change the orientation of one or more ports in a component.

    Every name in ports must exist in c.ports. The orientation is typically
    one of 0, 90, 180 or 270 in gdsfactory conventions, but arbitrary
    angles are allowed.

    Args:
        c: Component whose port orientations are modified.
        ports: Names of the ports in c to update.
        orientation: New orientation angle in degrees.

    Returns:
        gf.Component: The component c with the modified port orientations.
    """
    for p in ports:
        c.ports[p].orientation = orientation

    return c

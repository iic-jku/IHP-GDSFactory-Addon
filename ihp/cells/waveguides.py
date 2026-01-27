"""Primitives."""


import gdsfactory as gf
from gdsfactory.cross_section import port_names_electrical, port_types_electrical
from gdsfactory.typings import CrossSectionSpec, LayerSpec, Size
from math import exp, log, sqrt
from .. import tech

def _calculate_width_from_Z0(
    Z0: float, 
    ground_cross_section: CrossSectionSpec, 
    signal_cross_section: CrossSectionSpec
) -> float:
    """Calculate the width of a coplanar waveguide given the characteristic impedance Z0.

    Args:
        Z0: Target characteristic impedance (ohms).
        ground_cross_section: CrossSectionSpec for the ground layer.
        signal_cross_section: CrossSectionSpec for the signal layer.

    Returns:
        Calculated width (um).
    """
    # extract layer stack information
    layers = gf.get_active_pdk().get_layer_stack().layers
    
    # get indices of ground and signal layers
    keys = list(layers.keys())
    start = keys.index(ground_cross_section.split("_")[0])
    end = keys.index(signal_cross_section.split("_")[0])
    
    # calculate stack height between ground and signal layers
    stack_height = 0
    for k in keys[start + 1:end]:
        stack_height += layers[k].thickness
    
    signal_layer_thickness = layers[keys[end]].thickness
    
    # calculate width from Z0
    width = (exp(-Z0 * sqrt(4.1 + 1.41) / 87.0) * 5.98 * stack_height - signal_layer_thickness) / 0.8
    width = width - width%(2*tech.nm)  # truncate to 2 nm, gdsfactory needs even widths for ports
    print("Used Z0 =", Z0, " Ohms, to calculate width =", width, "um")
    
    return width

def _calculate_Z0_from_width(
    width: float,
    ground_cross_section: CrossSectionSpec, 
    signal_cross_section: CrossSectionSpec
) -> None:
    """Estimates the characteristic impedance Z0 from a given signal width.

    Computes the vertical stack height between the ground and signal layers
    using the active PDK layer stack, then applies an approximate closed-form
    formula to estimate Z0.

    Args:
        width: Signal line width (um).
        ground_cross_section: Cross-section spec for the ground layer.
        signal_cross_section: Cross-section spec for the signal layer.

    Returns:
        None. Prints intermediate layer information and the estimated Z0.
    """
    # extract layer stack information
    layers = gf.get_active_pdk().get_layer_stack().layers
    
    # get indices of ground and signal layers
    keys = list(layers.keys())
    start = keys.index(ground_cross_section.split("_")[0])
    end = keys.index(signal_cross_section.split("_")[0])
    
    # calculate stack height between ground and signal layers
    # print("Ground level: ", layers[keys[start]].layer)
    stack_height = 0
    for k in keys[start + 1:end]:
        stack_height += layers[k].thickness
    #     print(layers[k].layer, " thickness: ", layers[k].thickness, "um")
    # print("Signal level: ", layers[keys[end]].layer)
    # print("")
    
    signal_layer_thickness = layers[keys[end]].thickness
    # print("Total stack height from ground to signal:", stack_height, "um")
    # print(str(layers[keys[end]].layer) + " thickness: " + str(signal_layer_thickness) + " um")
    
    Z0 = 87.0/sqrt(4.1+1.41) * log(5.98*stack_height/(0.8*width + signal_layer_thickness))
    print("Used width =", width, "um, to calculate Z0 =", Z0, "Ohms")

    
    return Z0
        

@gf.cell
def straight(
    length: float = 10,
    cross_section: CrossSectionSpec = "strip",
    width: float | None = None,
    npoints: int = 2,
) -> gf.Component:
    """Returns a Straight waveguide.

    Args:
        length: straight length (um).
        cross_section: specification (CrossSection, string or dict).
        width: width of the waveguide. If None, it will use the width of the cross_section.
        npoints: number of points.
    """
    return gf.c.straight(
        length=length, cross_section=cross_section, width=width, npoints=npoints
    )


@gf.cell
def bend_euler(
    radius: float | None = None,
    angle: float = 90,
    p: float = 0.5,
    width: float | None = None,
    cross_section: CrossSectionSpec = "strip",
    allow_min_radius_violation: bool = False,
) -> gf.Component:
    """Regular degree euler bend.

    Args:
        radius: in um. Defaults to cross_section_radius.
        angle: total angle of the curve.
        p: Proportion of the curve that is an Euler curve.
        width: width to use. Defaults to cross_section.width.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
        allow_min_radius_violation: if True allows radius to be smaller than cross_section radius.
    """
    return gf.c.bend_euler(
        radius=radius,
        angle=angle,
        p=p,
        width=width,
        cross_section=cross_section,
        allow_min_radius_violation=allow_min_radius_violation,
        with_arc_floorplan=True,
        npoints=None,
        layer=None,
    )


@gf.cell
def bend_s(
    size: Size = (11, 1.8),
    cross_section: CrossSectionSpec = "strip",
    width: float | None = None,
    allow_min_radius_violation: bool = False,
) -> gf.Component:
    """Return S bend with bezier curve.

    stores min_bend_radius property in self.info['min_bend_radius']
    min_bend_radius depends on height and length

    Args:
        size: in x and y direction.
        cross_section: spec.
        width: width of the waveguide. If None, it will use the width of the cross_section.
        allow_min_radius_violation: allows min radius violations.
    """
    return gf.c.bend_s(
        size=size,
        cross_section=cross_section,
        npoints=99,
        allow_min_radius_violation=allow_min_radius_violation,
        width=width,
    )


@gf.cell
def wire_corner(
    cross_section: CrossSectionSpec = "metal_routing", width: float | None = None
) -> gf.Component:
    """Returns 45 degrees electrical corner wire.

    Args:
        cross_section: spec.
        width: optional width. Defaults to cross_section width.
    """
    return gf.c.wire_corner(
        cross_section=cross_section,
        width=width,
        port_names=port_names_electrical,
        port_types=port_types_electrical,
        radius=None,
    )


@gf.cell
def wire_corner45(
    cross_section: CrossSectionSpec = "metal_routing",
    radius: float = 10,
    width: float | None = None,
    layer: LayerSpec | None = None,
    with_corner90_ports: bool = True,
) -> gf.Component:
    """Returns 90 degrees electrical corner wire.

    Args:
        cross_section: spec.
        radius: ignored.
        width: optional width. Defaults to cross_section width.
        layer: ignored.
        with_corner90_ports: if True, adds ports at 90 degrees.
    """
    return gf.c.wire_corner45(
        cross_section=cross_section,
        radius=radius,
        width=width,
        layer=layer,
        with_corner90_ports=with_corner90_ports,
    )


####################
# Metal waveguides
####################


@gf.cell
def straight_metal(
    length: float = 10,
    cross_section: CrossSectionSpec = "metal_routing",
    width: float | None = None,
) -> gf.Component:
    """Returns a Straight waveguide.

    Args:
        length: straight length (um).
        cross_section: specification (CrossSection, string or dict).
        width: width of the waveguide. If None, it will use the width of the cross_section.
    """
    return gf.c.straight(
        length=length, cross_section=cross_section, width=width, npoints=2
    )


@gf.cell
def bend_metal(
    radius: float | None = None,
    angle: float = 90,
    width: float | None = None,
    cross_section: CrossSectionSpec = "metal_routing",
) -> gf.Component:
    """Regular degree euler bend."""
    if radius is None:
        if width:
            xs = gf.get_cross_section(cross_section=cross_section, width=width)
        else:
            xs = gf.get_cross_section(cross_section=cross_section)
        radius = xs.radius or xs.width
    return gf.c.bend_circular(
        radius=radius,
        angle=angle,
        width=width,
        cross_section=cross_section,
        allow_min_radius_violation=True,
        npoints=None,
        layer=None,
    )


@gf.cell
def bend_s_metal(
    size: Size = (11, 1.8),
    cross_section: CrossSectionSpec = "metal_routing",
    width: float | None = None,
    allow_min_radius_violation: bool = True,
) -> gf.Component:
    """Return S bend with bezier curve.

    stores min_bend_radius property in self.info['min_bend_radius']
    min_bend_radius depends on height and length

    Args:
        size: in x and y direction.
        cross_section: spec.
        width: width of the waveguide. If None, it will use the width of the cross_section.
        allow_min_radius_violation: allows min radius violations.
    """
    return gf.c.bend_s(
        size=size,
        cross_section=cross_section,
        npoints=99,
        allow_min_radius_violation=allow_min_radius_violation,
        width=width,
    )
    
    
# ------------------------------------------------------

@gf.cell
def tline(
    length: float = 10,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "metal5_routing",
    width: float | None = None,
    Z0: float | None = None,
    npoints: int = 2,
) -> gf.Component:
    """Returns a straight coplanar transmission line.

    Creates a signal straight and a wider ground straight aligned around it.
    
    Args:
        length: Length of the signal line (um).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        width: Line width (µm). Mutually exclusive with Z0.
        Z0: Target characteristic impedance (ohms). Mutually exclusive with width.
        npoints: Number of points used to draw the straights.
        
    Returns:
        A Component containing signal and ground lines.
    """
    if width is None and Z0 is None:
        raise ValueError("Provide either width or Z0")

    if width is not None and Z0 is not None:
        raise ValueError("Provide only one of width or Z0")
    
    if width is None:
        width = _calculate_width_from_Z0(
            Z0=Z0, 
            ground_cross_section=ground_cross_section, 
            signal_cross_section=signal_cross_section
        )   
    else:
        Z0 = _calculate_Z0_from_width(
            width=width,
            ground_cross_section=ground_cross_section, 
            signal_cross_section=signal_cross_section
        )
        
    
    c = gf.Component()
    
    signal = c.add_ref(
        gf.c.straight(
            length=length, cross_section=signal_cross_section, width=width, npoints=npoints
        )
    )
    c.add_ports(signal.ports)
    ground = c.add_ref(
        gf.c.straight(
            length=length+6*width, cross_section=ground_cross_section, width=7*width, npoints=npoints
        )
    )
    
    ground.move(( -3*width, 0))
    
    return c


@gf.cell
def tline_bend_circular(
    radius: float = 10,
    angle: float = 90,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "metal5_routing",
    width: float | None = None,
    Z0: float | None = None,
) -> gf.Component:
    """Returns a circular bend coplanar transmission line.

    Creates a signal bend and a wider ground bend aligned around it.
    
    Args:
        radius: Bend radius (um).
        angle: Bend angle (degrees).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        width: Line width (µm). Mutually exclusive with Z0.
        Z0: Target characteristic impedance (ohms). Mutually exclusive with width.
    """
    
    if width is None and Z0 is None:
        raise ValueError("Provide either width or Z0")

    if width is not None and Z0 is not None:
        raise ValueError("Provide only one of width or Z0")
    
    if width is None:
        width = _calculate_width_from_Z0(
            Z0=Z0, 
            ground_cross_section=ground_cross_section, 
            signal_cross_section=signal_cross_section
        )   
    else:
        Z0 = _calculate_Z0_from_width(
            width=width,
            ground_cross_section=ground_cross_section, 
            signal_cross_section=signal_cross_section
        )
        
    
    c = gf.Component()
    
    signal = c.add_ref(
        gf.c.bend_circular(
            radius=radius, angle=angle, cross_section=signal_cross_section, width=width
        )
    )
    c.add_ports(signal.ports)
    ground = c.add_ref(
        gf.c.bend_circular(
            radius=radius, angle=angle, cross_section=ground_cross_section, width=7*width
        )
    )
    
    return c


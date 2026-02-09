import gdsfactory as gf
from gdsfactory.cross_section import port_names_electrical, port_types_electrical
from gdsfactory.typings import CrossSectionSpec, LayerSpec, Size

from math import exp, log, sin, sqrt
from ihp.cells.resistors import rppd

from ihp.cells.waveguides import _calculate_width_from_Z0, tline, tline_bend_circular
from .. import tech



@gf.cell
def branch_line_coupler(
    connection_length: float = 100,
    frequency: float = 10e9,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "metal5_routing",
    Z0: float | None = None,
    e_r: float = 4.1
) -> gf.Component:
    """Returns a branch line coupler coplanar transmission line.

    Creates signal and ground lines for a branch line coupler.
    
    Args:
        connection_length: Length of the input line.
        frequency: Operating frequency (Hz).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        Z0: Target characteristic impedance (ohms).
        e_r: Relative permittivity of the substrate. Defaults to 4.1 for silicon dioxide.
    """
    wave_length = 299792458 / frequency * 1e6  # in um, assuming effective index of 3.5
    
    c = gf.Component()

    corner = gf.Component()

    # calculate the needed widths
    width_Z0, e_eff_Z0 = _calculate_width_from_Z0(
        Z0=Z0, 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r
    )
    width_Z0_sqrt2, e_eff_Z0_sqrt2 = _calculate_width_from_Z0(
        Z0=Z0/sqrt(2), 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r
    ) 
    print("e_eff_Z0 =", e_eff_Z0)
    print("e_eff_Z0_sqrt2 =", e_eff_Z0_sqrt2)
    quater_wave_length_Z0 = wave_length / 4  / sqrt(e_eff_Z0)  # this is just an estimate, the actual height will depend)
    quater_wave_length_Z0 = quater_wave_length_Z0 - quater_wave_length_Z0 % (tech.nm)  # truncate to 5 nm
    quater_wave_length_Z0_sqrt2 = wave_length / 4 / sqrt(e_eff_Z0_sqrt2)  # this is just an estimate, the actual height will depend)
    quater_wave_length_Z0_sqrt2 = quater_wave_length_Z0_sqrt2 - quater_wave_length_Z0_sqrt2 % (tech.nm)  # truncate to 5 nm
    
    

    # create corner component for the 4 corners of the coupler
    corner.add_polygon(
        points=[
            (0, 0),
            (0, width_Z0),
            (width_Z0-(width_Z0_sqrt2 - width_Z0), width_Z0),
            (width_Z0, width_Z0_sqrt2),
            (width_Z0, 0)
        ],
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    corner.add_port(
        name="e1",
        center=(width_Z0/2, 0),
        width=width_Z0,
        orientation=270,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    corner.add_port(
        name="e2",
        center=(width_Z0, width_Z0_sqrt2/2),
        width=width_Z0_sqrt2,
        orientation=0,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    corner.add_port(
        name="e3",
        center=(0, width_Z0/2),
        width=width_Z0,
        orientation=180,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )

    # start with the top left corner
    corner_nw = c.add_ref(corner)

    # create and connect the top Z0/sqrt(2) transmission line
    tline_top = c.add_ref(tline(
        length=quater_wave_length_Z0_sqrt2 - width_Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,
    ))   
    
    tline_top.connect(
        "e1", corner_nw.ports["e2"]
    )
    
    # create and connect the top right corner
    corner_ne = c.add_ref(corner).mirror(p1=(0,0), p2=(0,1))

    corner_ne.connect(
        "e2", tline_top.ports["e2"]
    )

    # create and connect the left Z0 transmission line
    tline_left = c.add_ref(tline(
        length=quater_wave_length_Z0 - width_Z0_sqrt2,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    tline_left.connect(
        "e1", corner_nw.ports["e1"]
    )

    # create and connect the bottom left corner
    corner_sw = c.add_ref(corner).mirror(p1=(0,0), p2=(1,0))

    corner_sw.connect(
        "e1", tline_left.ports["e2"]
    )

    # create and connect the bottom Z0/sqrt(2) transmission line
    tline_bottom = c.add_ref(tline(
        length=quater_wave_length_Z0_sqrt2 - width_Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,
    ))

    tline_bottom.connect(
        "e1", corner_sw.ports["e2"]
    )

    # create and connect the bottom right corner
    corner_se = c.add_ref(corner).mirror(p1=(0,0), p2=(1,0)).mirror(p1=(0,0), p2=(0,1))

    corner_se.connect(
        "e2", tline_bottom.ports["e2"]
    )

    # create and connect the right Z0 transmission line
    tline_right = c.add_ref(tline(
        length=quater_wave_length_Z0 - width_Z0_sqrt2,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    tline_right.connect(
        "e1", corner_ne.ports["e1"]
    )

    # create and connect input/output lines
    connection1 = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    connection1.connect(
        "e1", corner_nw.ports["e3"]
    )

    connection2 = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    connection2.connect(
        "e1", corner_ne.ports["e3"]
    )

    connection3 = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    connection3.connect(
        "e1", corner_se.ports["e3"]
    )

    connection4 = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    connection4.connect(
        "e1", corner_sw.ports["e3"]
    )

    # add ports to the component
    c.add_port(name = "e1", port=connection1.ports["e2"])
    c.add_port(name = "e2", port=connection2.ports["e2"])
    c.add_port(name = "e3", port=connection3.ports["e2"])
    c.add_port(name = "e4", port=connection4.ports["e2"])
    c.move((0,-width_Z0))
    return c


@gf.cell
def wilkinson_power_divider(
    connection_length: float = 50,
    frequency: float = 30e9,
    Z0: float = 50,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "metal5_routing",
) -> gf.Component:
    """Returns a Wilkinson power divider coplanar transmission line.

    Creates signal and ground lines for a Wilkinson power divider.
    
    Args:
        connection_length: Length of the input/output lines (um).
        frequency: Operating frequency (Hz).
        Z0: Target characteristic impedance (ohms).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        
    Returns:
        A Component containing the Wilkinson power divider.
    """

    wave_length = 3e8 / frequency * 1e6 / 3.5  # in um, assuming effective index of 3.5
    quater_wave_length = wave_length / 4
    quater_wave_length = quater_wave_length - quater_wave_length % (tech.nm)  # truncate to 5 nm
    print("Quarter wave length at", frequency/1e9, "GHz is", quater_wave_length, "um")

    c = gf.Component()

    # calculate the needed widths
    width_Z0 = _calculate_width_from_Z0(
        Z0=Z0, 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section
    )
    width_Z0_sqrt2 = _calculate_width_from_Z0(
        Z0=Z0*sqrt(2), 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section
    )

    # create and connect the input line
    connection_in = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))   
    
    c.add_ports(connection_in.ports)

    # we set the angle to 160 degrees (can be adjusted if needed)
    alpha = 160
    radius = (quater_wave_length *180)/(alpha * 3.14159)
    print("Bend radius for angle", alpha, "degrees is", radius, "um")
    # create upper branch line
    branch_upper = c.add_ref(tline_bend_circular(
        radius=radius,
        angle=alpha,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,)).mirror(p1=(0,0), p2=(0,1)).rotate(-90).move((connection_length,0))

    branch_lower = c.add_ref(tline_bend_circular(
        radius=radius,
        angle=alpha,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,)).rotate(-90).move((connection_length,0))

    opening = branch_upper.ports["e2"].center[1] - branch_lower.ports["e2"].center[1]
    print("Opening between branches is", opening, "um")

    r_square = 7
    w = (r_square/Z0)*opening

    c.add_ref(rppd(
        length=opening-0.2,
        width=w,
    ))
    
    return c
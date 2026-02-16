import gdsfactory as gf
from gdsfactory.cross_section import port_names_electrical, port_types_electrical
from gdsfactory.typings import CrossSectionSpec, LayerSpec, Size

from math import exp, log, sin, sqrt
from ihp.cells.resistors import rppd, CbResCalc

from ihp.cells.waveguides import _calculate_effective_dielectric_constant, _calculate_width_from_Z0, tline
from .. import tech



@gf.cell
def branch_line_coupler(
    connection_length: float = 100,
    frequency: float = 10e9,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "metal5_routing",
    Z0: float = 50,
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
    wave_length = 3e8 / frequency * 1e6  
    
    c = gf.Component()

    corner = gf.Component()

    # calculate the needed widths
    width_Z0 = _calculate_width_from_Z0(
        Z0=Z0, 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r
    )  
    width_Z0_sqrt2 = _calculate_width_from_Z0(
        Z0=Z0/sqrt(2), 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r
    ) 
    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r
    )
    
    quater_wave_length = wave_length / 4  / sqrt(e_eff)  # this is just an estimate, the actual height will depend)
    quater_wave_length = quater_wave_length - quater_wave_length % (tech.nm)  # truncate to 5 nm
    
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
        length=quater_wave_length - width_Z0,
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
        length=quater_wave_length - width_Z0_sqrt2,
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
        length=quater_wave_length - width_Z0,
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
        length=quater_wave_length - width_Z0_sqrt2,
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
    ground_cross_section: CrossSectionSpec | list[CrossSectionSpec] = "metal5_routing",
) -> gf.Component:
    """Return a Wilkinson power divider coplanar transmission line.

    Constructs a two-way Wilkinson divider from quarter-wave transformer
    branches (impedance $Z_0 \sqrt{2}$) arranged in a loop.  The
    quarter-wave length is derived from *frequency* and the effective
    dielectric constant of the selected cross-section stack.

    Args:
        connection_length: Length of the input/output feed lines (um).
        frequency: Operating frequency (Hz).
        Z0: Target characteristic impedance of the input/output ports
            (ohms).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
            Accepts a single spec for microstrip or a two-element list
            ``[lower, upper]`` for stripline.

    Returns:
        A Component containing the Wilkinson power divider with ports
        ``e1`` (input), ``e2`` and ``e3`` (outputs).
    """

    

    c = gf.Component()

    # calculate the needed widths
    width_Z0 = _calculate_width_from_Z0(
        Z0=Z0, 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section
    )
    width_Z0_sqrt2  = _calculate_width_from_Z0(
        Z0=Z0*sqrt(2), 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=4.1
    )

    print(width_Z0, width_Z0_sqrt2)
    
    # create and connect the input line
    connection_in = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))   
    
    # calculate the quarter wave length for the given frequency and cross-section
    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=4.1
    )
    wave_length = 3e8 / frequency * 1e6 / sqrt(e_eff)  # in um, assuming effective index of 3.5
    quater_wave_length = wave_length / 4
    quater_wave_length = quater_wave_length - quater_wave_length % (tech.nm)  # truncate to 5 nm


    # for future use
    width_R = 100
    length_R = CbResCalc(calc="l", l=0, r = 2*Z0, w=width_R, b=0, ps=0.18, cell='rppd')
    
    # Calculate the circumference of the square
    circumference = quater_wave_length * 2  + length_R
    
    
    # create and connect the corner piece for the connection line
    connection_corner = gf.Component()
    
    connection_corner.add_polygon(
        points=[
            (0, 0),
            (0, width_Z0),
            (width_Z0_sqrt2, width_Z0),
            (width_Z0_sqrt2, 0)
        ],
        layer=gf.get_cross_section(signal_cross_section).layer,
        
    )
    connection_corner.add_port(
        name="e1",
        center=(0, width_Z0/2),
        width=width_Z0,
        orientation=180,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    connection_corner.add_port(
        name="e2",
        center=(width_Z0_sqrt2/2, width_Z0),
        width=width_Z0_sqrt2,
        orientation=90,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    connection_corner.add_port(
        name="e3",
        center=(width_Z0_sqrt2/2, 0),
        width=width_Z0_sqrt2,
        orientation=270,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    
    
    connection_corner_ref = c.add_ref(connection_corner)
    
    connection_corner_ref.connect(
        "e1", connection_in.ports["e2"]
    )
    
    # create and connect upper branch line
    branch_left_up = c.add_ref(tline(
        length= circumference/8 - width_Z0_sqrt2 - width_Z0/2,  
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,))
    
    branch_left_up.connect(
        "e1", connection_corner_ref.ports["e2"]
    )
    
    # create the corner piece for the 4 outer corners of the coupler, which are all the same
    corner_piece = gf.Component()
    corner_piece.add_polygon(
        points=[
            (0, 0),
            (0, width_Z0_sqrt2),
            (width_Z0_sqrt2, width_Z0_sqrt2),
            (width_Z0_sqrt2, 0)
        ],
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    corner_piece.add_port(
        name="e1",
        center=(0, width_Z0_sqrt2/2),
        width=width_Z0_sqrt2,
        orientation=180,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    corner_piece.add_port(
        name="e2",
        center=(width_Z0_sqrt2/2, width_Z0_sqrt2),
        width=width_Z0_sqrt2,
        orientation=90,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    
    corner_piece_upper_left = c.add_ref(corner_piece)
    corner_piece_upper_left.connect(
        "e2", branch_left_up.ports["e2"]
    )
       
    branch_left_down = c.add_ref(tline(
        length= circumference/8 - width_Z0_sqrt2 - width_Z0/2,  
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,))
    
    branch_left_down.connect(
        "e1", connection_corner_ref.ports["e3"]
    )
    
    corner_piece_lower_left = c.add_ref(corner_piece)
    corner_piece_lower_left.connect(
        "e1", branch_left_down.ports["e2"]
    )
    
    branch_top = c.add_ref(tline(
        length= circumference/4 - width_Z0_sqrt2*2,  
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,))
    
    branch_top.connect(
        "e1", corner_piece_upper_left.ports["e1"]
    )
    
    branch_bottom = c.add_ref(tline(
        length= circumference/4 - width_Z0_sqrt2*2,  
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,))
    
    branch_bottom.connect(
        "e1", corner_piece_lower_left.ports["e2"]
    )
    
    corner_piece_upper_right = c.add_ref(corner_piece)
    
    corner_piece_upper_right.connect(
        "e2", branch_top.ports["e2"]
    )
    
    branch_right_down = c.add_ref(tline(
        length= circumference/8 - width_Z0_sqrt2*2 - length_R/2,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,))
    
    branch_right_down.connect(
        "e1", corner_piece_upper_right.ports["e1"]
    )
    
    corner_piece_lower_right = c.add_ref(corner_piece)
    corner_piece_lower_right.connect(
        "e1", branch_bottom.ports["e2"]
    )
    
    branch_right_up = c.add_ref(tline(
        length= circumference/8 - width_Z0_sqrt2*2 - length_R/2,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,))
    
    branch_right_up.connect(
        "e1", corner_piece_lower_right.ports["e2"]
    )
    
    corner_output_p2 = c.add_ref(corner_piece)
    corner_output_p2.connect(
        "e1", branch_right_down.ports["e2"]
    )
    
    corner_output_p3 = c.add_ref(corner_piece)
    corner_output_p3.connect(
        "e2", branch_right_up.ports["e2"]
    )
    
    c.add_port(name="e1", port=connection_in.ports["e1"])
    c.add_port(name="e2", port=corner_output_p2.ports["e2"])
    c.add_port(name="e3", port=corner_output_p3.ports["e1"])
    
    # for future use, add the resistor in the middle of the coupler
    # c.add_ref(rppd(
    #     length=length_R,
    #     width=width_R,
    #     polySpace=0.18,
    #     bends=0
    # ))
    
    return c
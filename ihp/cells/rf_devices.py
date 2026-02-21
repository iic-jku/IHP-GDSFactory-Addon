import gdsfactory as gf
from gdsfactory.cross_section import port_names_electrical, port_types_electrical
from gdsfactory.typings import CrossSectionSpec, LayerSpec, Size

from math import cosh, exp, log, pi, sin, sinh, sqrt

import scipy
from ihp.cells.resistors import rppd, CbResCalc

from ihp.cells.waveguides import _calculate_effective_dielectric_constant, _calculate_width_from_Z0, _get_stack_geometry, tline, coupler_tline, tline_corner
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
    
    quater_wave_length = wave_length / 4  / sqrt(e_eff)  
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
    branches (impedance $Z_0 / sqrt{2}$) arranged in a loop.  The
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


@gf.cell
def directional_coupler(
    connection_length: float = 100,
    frequency: float = 10e9,
    coupling_factor: float = 3,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "metal5_routing",
    Z0: float = 50,
    e_r: float = 4.1
) -> gf.Component:
    """Returns a directional coupler coplanar transmission line.

    Creates signal and ground lines for a directional coupler.
    
    Args:
        connection_length: Length of the input line.
        frequency: Operating frequency (Hz).
        coupling_factor: Coupling factor in dB.
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        Z0: Target characteristic impedance (ohms).
        e_r: Relative permittivity of the substrate. Defaults to 4.1 for silicon dioxide.
    """
    wave_length = scipy.constants.c / frequency * 1e6  
    
    c = gf.Component()
    
    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r
    )
    
    quater_wave_length = wave_length / 4  / sqrt(e_eff)  
    quater_wave_length = quater_wave_length - quater_wave_length % (tech.nm)  # truncate to 5 nm
    
    # couping factor must be negative
    if coupling_factor > 0:
        coupling_factor = -coupling_factor  # enforce negative coupling factor for the formula below
        
    coupling_factor_linear = 10 ** (coupling_factor / 20)
    
    # create the first line of the coupler
    coupled_lines = c.add_ref(coupler_tline(
        Z0e= Z0 * (1 + coupling_factor_linear) / (1 - coupling_factor_linear),
        Z0o= Z0 * (1 - coupling_factor_linear) / (1 + coupling_factor_linear),
        length=quater_wave_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    
    # create and connect the input line
    connection_port1 = c.add_ref(tline(
        length=connection_length,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    connection_port1.connect("e1", coupled_lines.ports["e1"])
    # create and connect the through port line
    connection_port2 = c.add_ref(tline(
        length=connection_length,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    connection_port2.connect("e1", coupled_lines.ports["e2"])
    
    corner_left = c.add_ref(tline_corner(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    
    corner_left.connect("e1", coupled_lines.ports["e4"])
    connection_port4 = c.add_ref(tline(
        length=connection_length,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    
    corner_right = c.add_ref(tline_corner(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    connection_port4.connect("e1", corner_left.ports["e2"])
    
    corner_right.connect("e1", coupled_lines.ports["e3"])
    connection_port3 = c.add_ref(tline(
        length=connection_length,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    connection_port3.connect("e1", corner_right.ports["e4"])
    
    
    
    c.add_port(name="e1", port=connection_port1.ports["e2"])
    c.add_port(name="e2", port=connection_port2.ports["e2"])
    c.add_port(name="e3", port=connection_port3.ports["e2"])
    c.add_port(name="e4", port=connection_port4.ports["e2"])
    c.flatten()
    return c


def _butterworth_prototype(N: int) -> list[float]:
    """Return Butterworth lowpass prototype element values g_0 … g_{N+1}."""
    # g = [1.0]
    g = []
    for k in range(1, N + 1):
        g.append(2 * sin((2 * k - 1) * pi / (2 * N)))
    g.append(1.0)
    return g


def _chebyshev_prototype(N: int, ripple_dB: float) -> list[float]:
    """Return Chebyshev lowpass prototype element values g_1 … g_{N+1}.

    Uses the standard recursion from Pozar / Matthaei-Young-Jones.

    Args:
        N: Filter order.
        ripple_dB: Pass-band ripple in dB (must be > 0).
    """
    x = ripple_dB / 17.37
    beta = log(cosh(x) / sinh(x))  # ln(coth(x))
    gamma = sinh(beta / (2 * N))

    a = [0.0] * (N + 1)
    b = [0.0] * (N + 1)
    for k in range(1, N + 1):
        a[k] = sin((2 * k - 1) * pi / (2 * N))
        b[k] = gamma ** 2 + sin(k * pi / N) ** 2

    g = []
    # g_1
    g.append(2 * a[1] / gamma)
    # g_2 ... g_N
    for k in range(2, N + 1):
        g.append(4 * a[k - 1] * a[k] / (b[k - 1] * g[-1]))
    # g_{N+1}
    if N % 2 == 1:
        g.append(1.0)
    else:
        g.append((cosh(beta / 4) / sinh(beta / 4)) ** 2)  # coth²(β/4)

    return g


@gf.cell
def coupled_line_bandpass_filter(
    order: int = 3,
    frequency: float = 10e9,
    fractional_bandwidth: float = 0.2,
    connection_length: float = 50,
    Z0: float = 50,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "metal5_routing",
    e_r: float = 4.1,
    filter_type: str = "butterworth",
    ripple_dB: float = 0.5,
) -> gf.Component:
    """Return a parallel-coupled-line bandpass filter.

    Creates an *N*-th order bandpass filter using *N* + 1 edge-coupled
    quarter-wave microstrip line sections.  The filter geometry is computed
    from Butterworth or Chebyshev lowpass prototype element values, which
    are transformed to coupled-line even/odd mode impedances and then to
    physical strip widths and coupling gaps.

    The layout consists of *N* + 2 signal strips arranged in a staggered
    (interdigitated) pattern on the signal layer, with a shared ground
    plane on the ground layer and input/output feed lines.  The first
    and last strips are λ/4 long; all intermediate strips are λ/2 long.
    Adjacent strips overlap horizontally by exactly λ/4, producing the
    required edge-coupled sections.  The input port is on the left and
    the output port on the right.

    .. note::

       For even-order Chebyshev filters the load impedance differs from
       the source impedance by the factor ``g[N+1]``.

    Args:
        order: Filter order *N*.  Number of coupled-line sections is
            *N* + 1 and the number of strips is *N* + 2.
        frequency: Centre frequency (Hz).
        fractional_bandwidth: Fractional bandwidth Δf / f₀.
        connection_length: Length of input/output feed lines (µm).
        Z0: Characteristic impedance of the input/output ports (Ω).
        signal_cross_section: Cross-section for the signal strips.
        ground_cross_section: Cross-section for the ground plane.
        e_r: Relative permittivity of the dielectric.  Defaults to 4.1
            (silicon dioxide).
        filter_type: ``"butterworth"`` (maximally flat) or
            ``"chebyshev"`` (equal-ripple).
        ripple_dB: Pass-band ripple in dB (Chebyshev only; ignored for
            Butterworth).

    Returns:
        A Component with ports ``e1`` (input) and ``e2`` (output).
    """
    N = order
    c = gf.Component()

    # --- 1. Lowpass prototype element values ---
    if filter_type == "butterworth":
        g = _butterworth_prototype(N)
    elif filter_type == "chebyshev":
        g = _chebyshev_prototype(N, ripple_dB)
    else:
        raise ValueError(
            f"Unknown filter_type '{filter_type}'; use 'butterworth' or 'chebyshev'"
        )

    # --- 2. Normalised J-inverter values  (J_j · Z_0) ---
    FBW = fractional_bandwidth
    JZ = [0.0] * (N + 1)
    JZ[0] = sqrt(pi * FBW / (2 * g[0] * g[1]))
    for j in range(1, N):
        JZ[j] = pi * FBW / (2 * sqrt(g[j] * g[j + 1]))
    JZ[N] = sqrt(pi * FBW / (2 * g[N] * g[N + 1]))

    # --- 3. Even / odd mode impedances per section ---
    Z0e_list = []
    Z0o_list = []
    for j in range(N + 1):
        Z0e_list.append(Z0 * (1 + JZ[j] + JZ[j] ** 2))
        Z0o_list.append(Z0 * (1 - JZ[j] + JZ[j] ** 2))

    # --- 4. Section characteristic impedances ---
    # Each section j has Z_j = sqrt(Z0e_j * Z0o_j)
    Z_section = [sqrt(Z0e_list[j] * Z0o_list[j]) for j in range(N + 1)]

    # --- 5. Signal width (for feed lines at Z0) and coupling gaps ---
    width = _calculate_width_from_Z0(
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r,
    )

    h, _t = _get_stack_geometry(signal_cross_section, ground_cross_section)

    gaps = []
    for j in range(N + 1):
        k_j = (Z0e_list[j] - Z0o_list[j]) / (Z0e_list[j] + Z0o_list[j])
        gap = -2 * h / pi * log(k_j)
        gap = max(gap, 2 * tech.nm)                 # enforce minimum gap
        gap = gap - gap % (2 * tech.nm)             # snap to grid
        gaps.append(gap)

    # --- 6. Quarter-wave length ---
    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r,
    )
    wavelength = 3e8 / frequency * 1e6 / sqrt(e_eff)
    quarter_wave = wavelength / 4
    quarter_wave = quarter_wave - quarter_wave % tech.nm  # snap to grid

    # --- 7. Build physical layout using tline ---
    #
    # Each coupled section j (0..N) has its own impedance Z_section[j].
    # Strip 0:     λ/4 at Z_section[0]           (only in section 0)
    # Strip j:     λ/4 at Z_section[j-1]  +  λ/4 at Z_section[j]
    # Strip N+1:   λ/4 at Z_section[N]           (only in section N)
    #
    # Adjacent strips overlap horizontally by exactly λ/4.
    # We track the y-cursor to stack strips with their coupling gaps.

    y = 0.0
    strips_left_port = []   # leftmost port of each strip (for connecting input)
    strips_right_port = []  # rightmost port of each strip (for connecting output)

    for j in range(N + 2):
        if j == 0:
            # First strip: single λ/4 segment at Z_section[0]
            seg = c.add_ref(tline(
                length=quarter_wave,
                signal_cross_section=signal_cross_section,
                ground_cross_section=ground_cross_section,
                Z0=Z_section[0],
            ))
            seg.move((0, y + _calculate_width_from_Z0(Z0=Z_section[0], signal_cross_section=signal_cross_section, ground_cross_section=ground_cross_section, e_r=e_r) / 2))
            strips_left_port.append(seg.ports["e1"])
            strips_right_port.append(seg.ports["e2"])
            w_j = _calculate_width_from_Z0(Z0=Z_section[0], signal_cross_section=signal_cross_section, ground_cross_section=ground_cross_section, e_r=e_r)

        elif j == N + 1:
            # Last strip: single λ/4 segment at Z_section[N]
            xs = N * quarter_wave
            w_j = _calculate_width_from_Z0(Z0=Z_section[N], signal_cross_section=signal_cross_section, ground_cross_section=ground_cross_section, e_r=e_r)
            seg = c.add_ref(tline(
                length=quarter_wave,
                signal_cross_section=signal_cross_section,
                ground_cross_section=ground_cross_section,
                Z0=Z_section[N],
            ))
            seg.move((xs, y + w_j / 2))
            strips_left_port.append(seg.ports["e1"])
            strips_right_port.append(seg.ports["e2"])

        else:
            # Intermediate strip j: left half at Z_section[j-1], right half at Z_section[j]
            xs = (j - 1) * quarter_wave
            w_left = _calculate_width_from_Z0(Z0=Z_section[j - 1], signal_cross_section=signal_cross_section, ground_cross_section=ground_cross_section, e_r=e_r)
            w_right = _calculate_width_from_Z0(Z0=Z_section[j], signal_cross_section=signal_cross_section, ground_cross_section=ground_cross_section, e_r=e_r)
            w_j = max(w_left, w_right)  # use max for gap calculation

            seg_left = c.add_ref(tline(
                length=quarter_wave,
                signal_cross_section=signal_cross_section,
                ground_cross_section=ground_cross_section,
                Z0=Z_section[j - 1],
            ))
            seg_left.move((xs, y + w_left / 2))

            seg_right = c.add_ref(tline(
                length=quarter_wave,
                signal_cross_section=signal_cross_section,
                ground_cross_section=ground_cross_section,
                Z0=Z_section[j],
            ))
            seg_right.connect("e1", seg_left.ports["e2"], allow_width_mismatch=True)

            strips_left_port.append(seg_left.ports["e1"])
            strips_right_port.append(seg_right.ports["e2"])

        y += w_j
        if j < N + 1:
            y += gaps[j]

    # Input feed at Z0 (connects to left edge of strip 0)
    connection_in = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    connection_in.connect("e2", strips_left_port[0], allow_width_mismatch=True)

    # Output feed at Z0 (connects to right edge of last strip)
    connection_out = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    connection_out.connect("e1", strips_right_port[-1], allow_width_mismatch=True)

    # --- 8. Ports ---
    c.add_port(name="e1", port=connection_in.ports["e1"])
    c.add_port(name="e2", port=connection_out.ports["e2"])

    return c


gf.cell
def coupled_line_bandpass_filter2(
        order: int = 3,
        frequency: float = 10e9,
        bandwidth: float = 0.2,
        connection_length: float = 50,
        Z0: float = 50,
        signal_cross_section: CrossSectionSpec = "topmetal2_routing",
        ground_cross_section: CrossSectionSpec = "metal5_routing",
        e_r: float = 4.1,
        filter_type: str = "butter",
        ripple_dB: float = 3,
    ) -> gf.Component:
    
    c = gf.Component()
    # get filter coefficients
    # g = [g1 g2 ... gN gN+1] for N-th order filter
    if filter_type == "butter":
        g = _butterworth_prototype(order)
    elif filter_type == "cheby":
        g = _chebyshev_prototype(order, ripple_dB)

    print(g)

    fractional_bandwidth = bandwidth / frequency
    f_2 = frequency * (1 + fractional_bandwidth / 2)
    f_1 = frequency * (1 - fractional_bandwidth / 2)
    print(f_1, f_2)
    delta = fractional_bandwidth


    # initialize lists for Z0J values
    Z0J = [0.0] * (order + 1)

    # first Z0J value
    Z0J[0] = sqrt(pi * delta / (2 * g[0]))

    # calculate Z0J values for j = 1 to N-1
    for j in range(1, order):
        Z0J[j] = pi * delta / (2 * sqrt(g[j-1] * g[j]))

    # last Z0J value 
    Z0J[order] = sqrt(pi * delta / (2 * g[order-1] * g[order]))


    # initialize and calculate Z0e and Z0o values for each section
    Z0e = [0.0] * (order + 1)
    Z0o = [0.0] * (order + 1)
    Z_section = [0.0] * (order + 1)
    
    for j in range(order + 1):
        Z0e[j] = Z0 * (1 + Z0J[j] + Z0J[j] ** 2)
        Z0o[j] = Z0 * (1 - Z0J[j] + Z0J[j] ** 2)
        print(f"Section {j}: Z0e = {Z0e[j]:.2f} ohms, Z0o = {Z0o[j]:.2f} ohms")
        Z_section[j] = sqrt(Z0e[j] * Z0o[j])
        print(f"Section {j}: Z_section = {Z_section[j]:.2f} ohms")
    
    # calculate the coupling coefficient k for each section
    g = [1.0] + g  # prepend g0 = 1.0 for easier indexing
    k = [0.0] * (order + 1)
    for j in range(order + 1):
        k[j] = (f_2 - f_1) / sqrt(f_1 * f_2 * g[j] * g[j+1])
        print(f"Section {j}: k = {k[j]:.4f}")

    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r,
    )
    segment_length = scipy.constants.c / frequency * 1e6 / sqrt(e_eff) / 4
    segment_length = segment_length - segment_length % tech.nm  # snap to grid
    print(f"Segment length (λ/4) = {segment_length:.2f}")

    connection_in = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))

    connection_out = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))

    previous_section = connection_in

    for i in range(order + 1):
        section_i = c.add_ref(coupler_tline(
            Z0e=Z0e[i],
            Z0o=Z0o[i],
            length=segment_length, 
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
        ))
        section_i.connect("e4", previous_section.ports["e2"], allow_width_mismatch=True)
        previous_section = section_i

    connection_out.connect("e1", previous_section.ports["e2"], allow_width_mismatch=True)
    
    c.add_port(name="e1", port=connection_in.ports["e1"])
    c.add_port(name="e2", port=connection_out.ports["e2"])

    c.flatten()
    
    return c

    
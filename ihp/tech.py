"""IHP PDK Technology definitions.

- LayerMap with IHP PDK layers
- LayerStack for 3D representation
- Cross-sections for routing
- Technology parameters
"""
import os
import json


import sys
from functools import partial
from typing import Any

import gdsfactory as gf
from doroutes.bundles import add_bundle_astar
from gdsfactory import typings
from gdsfactory.component import Component
from gdsfactory.cross_section import (
    CrossSection,
    get_cross_sections,
    port_names_electrical,
    port_types_electrical,
    xsection,
)
from gdsfactory.technology import LayerLevel, LayerMap, LayerStack
from gdsfactory.typings import Layer, LayerSpec
from pydantic import BaseModel
from gdsfactory.technology import lyp_to_dataclass
from ihp.config import PATH

nm = 0.005  # 1 grid unit = 5nm
gf.kcl.dbu = nm
pin_length = 10 * nm
heater_width = 4


ihp_filepath = "/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp"

package_folder = os.path.dirname(os.path.abspath(__file__))

output_filepath = os.path.join(package_folder, "layer_map_ihp.py")
lyp_to_dataclass(ihp_filepath, overwrite=True, output_filepath=output_filepath, map_name="LayerMapIHP")

# import after generation
from ihp.layer_map_ihp import LAYER

# Add aliases
LAYER.TEXT = LAYER.TEXTdrawing
LAYER.METAL1 = LAYER.Metal1drawing
LAYER.METAL2 = LAYER.Metal2drawing
LAYER.METAL3 = LAYER.Metal3drawing
LAYER.METAL4 = LAYER.Metal4drawing
LAYER.METAL5 = LAYER.Metal5drawing
LAYER.TOPMETAL1 = LAYER.TopMetal1drawing
LAYER.TOPMETAL2 = LAYER.TopMetal2drawing
LAYER.SUBSTRATE = LAYER.Substratedrawing
LAYER.ACTIV = LAYER.Activdrawing
LAYER.GATPOLY = LAYER.GatPolydrawing
LAYER.VIA1 = LAYER.Via1drawing
LAYER.VIA2 = LAYER.Via2drawing
LAYER.VIA3 = LAYER.Via3drawing
LAYER.VIA4 = LAYER.Via4drawing
LAYER.TOPVIA1 = LAYER.TopVia1drawing
LAYER.TOPVIA2 = LAYER.TopVia2drawing


def add_labels_to_ports_optical(
    component: Component,
    label_layer: LayerSpec = LAYER.TEXT,
    port_type: str | None = "optical",
    **kwargs,
) -> Component:
    """Add labels to component ports.

    Args:
        component: to add labels.
        label_layer: layer spec for the label.
        port_type: to select ports.

    keyword Args:
        layer: select ports with GDS layer.
        prefix: select ports with prefix in port name.
        orientation: select ports with orientation in degrees.
        width: select ports with port width.
        layers_excluded: List of layers to exclude.
        port_type: select ports with port_type (optical, electrical, vertical_te).
        clockwise: if True, sort ports clockwise, False: counter-clockwise.
    """
    suffix = "o3_0" if len(component.ports) == 4 else "o2_0"
    ports = component.ports.filter(port_type=port_type, suffix=suffix, **kwargs)
    for port in ports:
        component.add_label(text=port.name, position=port.center, layer=label_layer)

    return component


margin = 0.5


def get_layer_stack(
    thickness_metal1: float = 0.42,  # Metal1 thickness (420 nm from process specs)
    thickness_metal: float = 0.49,  # Metal2-5 thickness (490 nm from process specs)
    thickness_via1: float = 0.54,  # Via1 thickness (540 nm from process specs)
    thickness_via: float = 0.54,  # Via2-4 thickness (540 nm from process specs)
    thickness_topvia1: float = 0.85,  # TopVia1 thickness (850 nm from process specs)
    thickness_topmetal1: float = 2.0,  # TopMetal1 thickness (2000 nm from process specs)
    thickness_topvia2: float = 2.8,  # TopVia2 thickness (2800 nm from process specs)
    thickness_topmetal2: float = 3.0,  # TopMetal2 thickness (3000 nm from process specs)
    substrate_thickness: float = 300.0,  # Full substrate
) -> LayerStack:
    """Returns IHP PDK LayerStack for 3D visualization and simulation.

    Layer thicknesses are based on the IHP SG13 process specifications.
    Reference: https://ihp-open-pdk-docs.readthedocs.io/en/latest/process_specs/01_01_main_process_cross_sec.html

    Args:
        thickness_metal1: Metal1 layer thickness in um (default: 0.42).
        thickness_metal: Metal2-5 layer thickness in um (default: 0.49).
        thickness_via1: Via1 layer thickness in um (default: 0.54).
        thickness_via: Via2-4 layer thickness in um (default: 0.54).
        thickness_topvia1: TopVia1 layer thickness in um (default: 0.85).
        thickness_topmetal1: TopMetal1 layer thickness in um (default: 2.0).
        thickness_topvia2: TopVia2 layer thickness in um (default: 2.8).
        thickness_topmetal2: TopMetal2 layer thickness in um (default: 3.0).
        substrate_thickness: Substrate thickness in um (default: 300.0).

    Returns:
        LayerStack for IHP PDK with properly connected metal and via layers.
    """

    return LayerStack(
        layers=dict(
            # Substrate
            substrate=LayerLevel(
                layer=LAYER.Substratedrawing,
                thickness=substrate_thickness,
                zmin=-substrate_thickness,
                material="si",
                info={"mesh_order": 99},
            ),
            # Active silicon
            active=LayerLevel(
                layer=LAYER.Activdrawing,
                thickness=0.2,
                zmin=0.0,
                material="si",
                info={"mesh_order": 1},
            ),
            # Poly gate
            poly=LayerLevel(
                layer=LAYER.GatPolydrawing,
                thickness=0.18,
                zmin=0.0,
                material="poly_si",
                info={"mesh_order": 2},
            ),
            # Metal 1
            metal1=LayerLevel(
                layer=LAYER.Metal1drawing,
                thickness=thickness_metal1,
                zmin=1.0,
                material="aluminum",
                info={"mesh_order": 3},
            ),
            # Via 1
            via1=LayerLevel(
                layer=LAYER.Via1drawing,
                thickness=thickness_via1,
                zmin=1.0 + thickness_metal1,
                material="tungsten",
                info={"mesh_order": 4},
            ),
            # Metal 2
            metal2=LayerLevel(
                layer=LAYER.Metal2drawing,
                thickness=thickness_metal,
                zmin=1.0 + thickness_metal1 + thickness_via1,
                material="aluminum",
                info={"mesh_order": 5},
            ),
            # Via 2
            via2=LayerLevel(
                layer=LAYER.Via2drawing,
                thickness=thickness_via,
                zmin=1.0 + thickness_metal1 + thickness_via1 + thickness_metal,
                material="tungsten",
                info={"mesh_order": 6},
            ),
            # Metal 3
            metal3=LayerLevel(
                layer=LAYER.Metal3drawing,
                thickness=thickness_metal,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + thickness_metal
                + thickness_via,
                material="aluminum",
                info={"mesh_order": 7},
            ),
            # Via 3
            via3=LayerLevel(
                layer=LAYER.Via3drawing,
                thickness=thickness_via,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + 2 * thickness_metal
                + thickness_via,
                material="tungsten",
                info={"mesh_order": 8},
            ),
            # Metal 4
            metal4=LayerLevel(
                layer=LAYER.Metal4drawing,
                thickness=thickness_metal,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + 2 * thickness_metal
                + 2 * thickness_via,
                material="aluminum",
                info={"mesh_order": 9},
            ),
            # Via 4
            via4=LayerLevel(
                layer=LAYER.Via4drawing,
                thickness=thickness_via,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + 3 * thickness_metal
                + 2 * thickness_via,
                material="tungsten",
                info={"mesh_order": 10},
            ),
            # Metal 5
            metal5=LayerLevel(
                layer=LAYER.Metal5drawing,
                thickness=thickness_metal,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + 3 * thickness_metal
                + 3 * thickness_via,
                material="aluminum",
                info={"mesh_order": 11},
            ),
            # Top Via 1
            topvia1=LayerLevel(
                layer=LAYER.TopVia1drawing,
                thickness=thickness_topvia1,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via,
                material="tungsten",
                info={"mesh_order": 12},
            ),
            # Top Metal 1
            topmetal1=LayerLevel(
                layer=LAYER.TopMetal1drawing,
                thickness=thickness_topmetal1,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via
                + thickness_topvia1,
                material="aluminum",
                info={"mesh_order": 13},
            ),
            # Top Via 2
            topvia2=LayerLevel(
                layer=LAYER.TopVia2drawing,
                thickness=thickness_topvia2,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via
                + thickness_topvia1
                + thickness_topmetal1,
                material="tungsten",
                info={"mesh_order": 14},
            ),
            # Top Metal 2
            topmetal2=LayerLevel(
                layer=LAYER.TopMetal2drawing,
                thickness=thickness_topmetal2,
                zmin=1.0
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via
                + thickness_topvia1
                + thickness_topmetal1
                + thickness_topvia2,
                material="aluminum",
                info={"mesh_order": 15},
            ),
        )
    )

techParams: dict = {}
dataBaseUnits: float = 0.001

techName: str = "sg13g2"
techNameParam: str = "techName"
jsonTechFile: str = techName + "_tech.json"

techFilePath: str = os.path.join("/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/sg13g2_pycell_lib/", jsonTechFile) #TODO hardcoded path, böse

with open(techFilePath, "r") as tech_file:
    jsData = json.load(tech_file)
    techParams = jsData["techParams"]

class TechIHP(BaseModel):
    """IHP PDK Technology parameters."""

    # Grid and precision
    grid: float = 0.005  # 5nm grid
    precision: float = 1e-9

    # Design rules - transistors
    nmos_min_width: float = 0.15
    nmos_min_length: float = 0.13
    pmos_min_width: float = 0.15
    pmos_min_length: float = 0.13

    # Design rules - contacts and vias
    cont_size: float = 0.16
    cont_spacing: float = 0.18
    cont_enc_active: float = 0.07
    cont_enc_poly: float = 0.07
    cont_enc_metal: float = 0.06

    via1_size: float = 0.19
    via1_spacing: float = 0.22
    via1_enc_metal: float = 0.05
    
    topvia1_size: float = 0.42
    topvia1_spacing: float = 0.42
    topvia1_enc_metal: float = 0.42
    
    topvia2_size: float = 0.9
    topvia2_spacing: float = 1.05
    topvia2_enc_metal: float = 0.5

    # Design rules - metal
    metal1_width: float = 0.14
    metal1_spacing: float = 0.14
    metal2_width: float = 0.16
    metal2_spacing: float = 0.16
    metal3_width: float = 0.20
    metal3_spacing: float = 0.20
    metal4_width: float = 0.20
    metal4_spacing: float = 0.20
    metal5_width: float = 0.20
    metal5_spacing: float = 0.20
    topmetal1_width: float = 1.0
    topmetal1_spacing: float = 1.0
    topmetal2_width: float = 2.0
    topmetal2_spacing: float = 2.0

    # Design rules - resistors
    rsil_min_width: float = 0.4
    rsil_min_length: float = 0.8
    rsil_sheet_res: float = 7.0  # ohms/square

    rppd_min_width: float = 0.4
    rppd_min_length: float = 0.8
    rppd_sheet_res: float = 300.0  # ohms/square

    rhigh_min_width: float = 1.4
    rhigh_min_length: float = 5.0
    rhigh_sheet_res: float = 1350.0  # ohms/square

    # Design rules - capacitors
    mim_min_size: float = 0.5
    mim_cap_density: float = 1.5  # fF/um^2

    # Design rules - inductors
    inductor_min_width: float = 2.0
    inductor_min_spacing: float = 2.1
    inductor_min_diameter: float = 15.0

    techParams: dict = techParams

TECH = TechIHP()
LAYER_STACK = get_layer_stack()
LAYER_VIEWS = gf.technology.LayerViews(PATH.lyp)


############################
# Cross-sections functions
############################
cross_section = gf.cross_section.metal1


@xsection
def metal_routing(
    width: float = 1,
    layer: typings.LayerSpec = "M3",
    radius: float | None = None,
    port_names: typings.IOPorts = port_names_electrical,
    port_types: typings.IOPorts = port_types_electrical,
    **kwargs: Any,
) -> CrossSection:
    """Return Metal Strip cross_section."""
    radius = radius or width
    return cross_section(
        width=width,
        layer=layer,
        radius=radius,
        port_names=port_names,
        port_types=port_types,
        **kwargs,
    )


gatpoly_routing = partial(
    metal_routing,
    layer=LAYER.GatPolydrawing,
    width=0.13,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

# Metal routing cross-sections
metal1_routing = partial(
    metal_routing,
    layer=LAYER.METAL1,
    width=TECH.metal1_width * 2,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

metal2_routing = partial(
    metal_routing,
    layer=LAYER.METAL2,
    width=TECH.metal2_width * 2,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

metal3_routing = partial(
    metal_routing,
    layer=LAYER.METAL3,
    width=TECH.metal3_width * 2,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

metal4_routing = partial(
    metal_routing,
    layer=LAYER.METAL4,
    width=TECH.metal4_width * 2,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

metal5_routing = partial(
    metal_routing,
    layer=LAYER.METAL5,
    width=TECH.metal5_width * 2,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

topmetal1_routing = partial(
    metal_routing,
    layer=LAYER.TOPMETAL1,
    width=TECH.topmetal1_width,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

topmetal2_routing = partial(
    metal_routing,
    layer=LAYER.TOPMETAL2,
    width=TECH.topmetal2_width,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

strip = topmetal2_routing
metal_routing = topmetal2_routing

cross_sections = get_cross_sections(sys.modules[__name__])

############################
# Routing functions
############################

route_bundle = partial(gf.routing.route_bundle, cross_section="strip")
route_bundle_rib = partial(
    route_bundle,
    cross_section="rib",
)
route_bundle_metal = partial(
    route_bundle,
    straight="straight_metal",
    bend="bend_metal",
    taper=None,
    cross_section="metal_routing",
    port_type="electrical",
)
route_bundle_metal_corner = partial(
    route_bundle,
    straight="straight_metal",
    bend="wire_corner",
    taper=None,
    cross_section="metal_routing",
    port_type="electrical",
)

route_astar = partial(
    add_bundle_astar,
    layers=["TOPMETAL2"],
    bend="bend_euler",
    straight="straight",
    grid_unit=500,
    spacing=3,
)

route_astar_metal = partial(
    add_bundle_astar,
    layers=["TOPMETAL2"],
    bend="wire_corner",
    straight="straight_metal",
    grid_unit=500,
    spacing=15,
)


routing_strategies = dict(
    route_bundle=route_bundle,
    route_bundle_rib=route_bundle_rib,
    route_bundle_metal=route_bundle_metal,
    route_bundle_metal_corner=route_bundle_metal_corner,
    route_astar=route_astar,
    route_astar_metal=route_astar_metal,
)

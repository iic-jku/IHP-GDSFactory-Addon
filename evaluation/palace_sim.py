import os
import re
import sys

import gds2palace
import gdspy
from gds2palace import *

# conductor model (gds2palace >= 0.9.0): 'surface' (surface impedance, fastest),
# 'solve_inside' (metals meshed as volumes) or 'solve_inside_skin' (volumes plus thin
# skin layers along all faces, most accurate for loss). Set from the Makefile / environment.
CONDUCTOR_MODEL = os.environ.get("CONDUCTOR_MODEL", "solve_inside_skin")
# mesh cell size in the conductor region (um)
REFINED_CELLSIZE = float(os.environ.get("REFINED_CELLSIZE", "2"))

# older gds2palace ignores settings['conductor_model'] silently and simulates 'surface'
if CONDUCTOR_MODEL != "surface" and tuple(int(x) for x in gds2palace.__version__.split(".")[:2]) < (0, 9):
    sys.exit(
        f"conductor_model '{CONDUCTOR_MODEL}' needs gds2palace >= 0.9.0, found {gds2palace.__version__} "
        f"({gds2palace.__file__}). Use the nightly IIC-OSIC-TOOLS image or `pip install -U gds2palace`."
    )


def _get_number_of_ports(gds_filename):
    """Get number of ports from GDSII file, by counting layers with layer number > 200"""
    lib = gdspy.GdsLibrary()
    lib.read_gds(gds_filename)
    cell = lib.top_level()[0]
    layers = _get_layers(cell)
    return sum(1 for layer, _ in layers if layer > 200)


def _get_ghz_from_filename(gds_filename):
    """Extract the integer GHz value from a filename like 'tline_l4_for_10GHz.gds'."""
    base_name = os.path.basename(gds_filename)
    match = re.search(r"(\d+(?:\.\d+)?)\s*GHz", base_name, re.IGNORECASE)
    if not match:
        raise ValueError(f"No GHz value found in filename: {gds_filename}")
    ghz_value = float(match.group(1))
    if not ghz_value.is_integer():
        raise ValueError(f"GHz value must be an integer: {gds_filename}")
    return int(ghz_value)


def _get_layers(cell, layers=None):
    """Recursively collect every (layer, datatype) pair used in a cell and its
    referenced sub-cells. Returns a set of int tuples."""
    if layers is None:
        layers = set()
    for poly in cell.polygons:
        for layer, datatype in zip(poly.layers, poly.datatypes):
            layers.add((int(layer), int(datatype)))
    for ref in cell.references:
        _get_layers(ref.ref_cell, layers)
    return layers


def _get_ground_and_signal_layernames(gds_filename, metals_list):
    """Determine ground and signal layer names from the metal layers used in the GDSII file.

    Port layers (layer number > 200) are excluded. Of the remaining metal layers,
    the lowest layer number is ground, the highest layer number is the signal layer.
    """
    lib = gdspy.GdsLibrary()
    lib.read_gds(gds_filename)
    cell = lib.top_level()[0]
    layers = _get_layers(cell)
    metal_layernums = sorted({layer for layer, _ in layers if layer <= 200})
    if len(metal_layernums) < 2:
        raise ValueError(
            f"Expected at least 2 metal layers (ground and signal) in GDSII file, found: {metal_layernums}"
        )

    ground_layernum = metal_layernums[0]
    signal_layernum = metal_layernums[-1]

    ground_layername = metals_list.getbylayernumber(ground_layernum).name
    signal_layername = metals_list.getbylayernumber(signal_layernum).name

    return ground_layername, signal_layername


# ===================== input files and path settings =======================

gds_filename = sys.argv[1]  # geometries
XML_filename = "SG13G2_nosub.xml"  # stackup

# preprocess GDSII for safe handling of cutouts/holes?
preprocess_gds = False

# merge via polygons with distance less than .. microns, set to 0 to disable via merging.
merge_polygon_size = 0

# get path for this simulation file
script_path = utilities.get_script_path(__file__)

# use the GDS filename as model basename, so the Palace output directory and the
# Touchstone file combine_snp.py writes carry the model name instead of the script
# name (gds2palace derives both from this: sim_path = <basename>_data and the Palace
# "Output" dir = output/<basename>, which combine_snp.py turns into <basename>.sNp)
model_basename = utilities.get_basename(gds_filename)

# set and create directory for simulation output
sim_path = utilities.create_sim_path(script_path, model_basename, dirname=os.path.splitext(gds_filename)[0])
print("Simulation data directory: ", sim_path)

f_center = _get_ghz_from_filename(gds_filename) * 1e9
# f_center = 150e9
# print(f"Extracted center frequency from filename: {f_center/1e9:.0f} GHz")

# change path to models script path
modelDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(modelDir)

# ======================== simulation settings ================================

settings = {}

settings["unit"] = 1e-6  # geometry is in microns
settings["margin"] = 50  # distance in microns from GDSII geometry boundary to simulation boundary

settings["fstart"] = f_center * 0.5
settings["fstop"] = f_center * 1.5

# settings['fstart']  = 0
# settings['fstop']   = 500e9

settings["fstep"] = f_center / 100

settings["refined_cellsize"] = REFINED_CELLSIZE  # mesh cell size in conductor region
settings["cells_per_wavelength"] = 10  # how many mesh cells per wavelength, must be 10 or more

settings["meshsize_max"] = 70  # microns, override cells_per_wavelength
settings["adaptive_mesh_iterations"] = 0

settings["conductor_model"] = CONDUCTOR_MODEL
print(
    f"gds2palace {gds2palace.__version__}, conductor_model: {CONDUCTOR_MODEL}, refined_cellsize: {REFINED_CELLSIZE} um"
)

settings["no_gui"] = True  # create files without showing 3D model
# settings['no_gui'] = ('nogui' in sys.argv)  # check if nogui specified on command line, then create files without showing 3D model

# get technology stackup data (needed early to resolve ground/signal layer names)
materials_list, dielectrics_list, metals_list = stackup_reader.read_substrate(XML_filename)

# Ports from GDSII Data, polygon geometry from specified special layer
# Excitations can be switched off by voltage=0, those S-parameter will be incomplete then

simulation_ports = simulation_setup.all_simulation_ports()

# proc = subprocess.Popen(['python', 'get_ports.py', gds_filename], stdout=subprocess.PIPE)

# num_ports = int(proc.stdout.readline())

num_ports = _get_number_of_ports(gds_filename)

print(f"Number of ports found: {num_ports}")

# determine ground and signal layer from the metal layers used in the GDSII file
ground_layername, signal_layername = _get_ground_and_signal_layernames(gds_filename, metals_list)

print(f"Ground layer: {ground_layername}, Signal layer: {signal_layername}")

for portnumber in range(1, num_ports + 1):
    simulation_ports.add_port(
        simulation_setup.simulation_port(
            portnumber=portnumber,
            voltage=1,
            port_Z0=50,
            source_layernum=200 + portnumber,
            from_layername=signal_layername,
            to_layername=ground_layername,
            direction="z",
        )
    )

# print(simulation_ports)
# instead of in-plane port specified with target_layername, we here use via port specified with from_layername and to_layername
# simulation_ports.add_port(simulation_setup.simulation_port(portnumber=1, voltage=1, port_Z0=50, source_layernum=201, from_layername='Metal5', to_layername='TopMetal2', direction='z'))
# simulation_ports.add_port(simulation_setup.simulation_port(portnumber=2, voltage=1, port_Z0=50, source_layernum=202, from_layername='Metal5', to_layername='TopMetal2', direction='z'))
# simulation_ports.add_port(simulation_setup.simulation_port(portnumber=3, voltage=1, port_Z0=50, source_layernum=203, from_layername='Metal5', to_layername='TopMetal2', direction='z'))
# simulation_ports.add_port(simulation_setup.simulation_port(portnumber=4, voltage=1, port_Z0=50, source_layernum=204, from_layername='Metal5', to_layername='TopMetal2', direction='z'))


# ======================== simulation ================================

# get list of layers from technology
layernumbers = metals_list.getlayernumbers()
layernumbers.extend(simulation_ports.portlayers)

# read geometries from GDSII, only purpose 0
allpolygons = gds_reader.read_gds(
    gds_filename,
    layernumbers,
    purposelist=[0],
    metals_list=metals_list,
    preprocess=preprocess_gds,
    merge_polygon_size=merge_polygon_size,
)


########### create model ###########

settings["simulation_ports"] = simulation_ports
settings["materials_list"] = materials_list
settings["dielectrics_list"] = dielectrics_list
settings["metals_list"] = metals_list
settings["layernumbers"] = layernumbers
settings["allpolygons"] = allpolygons
settings["sim_path"] = sim_path
settings["model_basename"] = model_basename


# list of ports that are excited (set voltage to zero in port excitation to skip an excitation!)
excite_ports = simulation_ports.all_active_excitations()
config_name, data_dir = simulation_setup.create_palace(excite_ports, settings)

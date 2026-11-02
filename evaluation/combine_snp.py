# convert Palace output port-S.csv to Touchstone format,
# walk through directory and combine all excitation

# new version for new Palace output that creates multi excitations in one common output file
# updated 19-Oct-2025 Mue: support more than 9 ports
# updated 08-Nov-2025 Mue: added evaluation for optional port impedance file port_information.json that is created by new gds2palace code
# updated 13-Nov-2025 Mue: added simple de-embedding of parasitic port inductance (flat ribbon calculation)
# updated 26-Nov-2025 Mue: also read Elmer FEM files
# updated 20-Oct-2026: port de-embedding puts each port's L at its own port (was all at port 1)

import json
import math
import os
import re

import numpy as np
import skrf as rf
from skrf.circuit import Circuit


def todb(x):
    """Complex value -> magnitude in dB (20*log10|x|)."""
    return 20 * np.log10(np.abs(x))


def toangle(x):
    """Complex value -> phase in degrees, sign-flipped to match the Touchstone
    convention used by the rest of this script."""
    return -np.degrees(np.angle(x))


def parse_elmer_results(found_filename, freq, S_dB, S_arg):
    """Read an Elmer FEM result (a scalar_results.names + matching data file) and
    append its S-parameters into the caller's freq / S_dB / S_arg lists.

    The .names file lists column labels; the 'cmf' columns hold real and imaginary
    S-matrix entries. For each frequency row, every S[m][n] is converted to (dB, deg)
    and stored in a per-frequency dict. Returns (num_ports, freq_unit). Mutates the
    passed-in lists in place (the same accumulation pattern as parse_palace_csv)."""
    freq_unit = "GHz"

    names_filename = found_filename
    data_filename = names_filename.replace(".names", "")

    # Parse column names
    column_names = []
    with open(names_filename) as namesfile:
        for line in namesfile:
            if ":" in line and line.strip()[0].isdigit():
                parts = line.split(":")
                if len(parts) >= 3:
                    name = parts[2].strip()
                    column_names.append(name)

    cmf_names = [name for name in column_names if name.startswith("cmf")]
    count_cmf = len(cmf_names)
    num_ports = int(math.sqrt(count_cmf / 2))

    # find column with frequency
    omega_column = column_names.index("angular frequency")

    # find column with re{S11}
    if "cmf 11" in column_names:
        re_s11_column = column_names.index("cmf 11")
    else:
        re_s11_column = column_names.index("cmf 1 1")

    # find column with im{S11}
    if "cmf im 11" in column_names:
        im_s11_column = column_names.index("cmf im 11")
    else:
        im_s11_column = column_names.index("cmf im 1 1")

    if re_s11_column + num_ports**2 != im_s11_column:
        print("Incorrect number of values in data file, does not match port count")
        exit(1)

    # read data file
    data = np.loadtxt(data_filename)

    if data.ndim == 2:
        # we have multiple frequencies
        omegalist = data[:, omega_column]
    else:
        # we have only one frequency point
        omegalist = [data[omega_column]]
    for omega in omegalist:
        freq.append(omega / (1e9 * 2 * math.pi))

    # -------------------------
    # Build S-matrices
    # -------------------------

    # loop over frequencies
    numfreq = len(omegalist)
    for f_index in range(numfreq):
        dB = {}
        arg = {}
        for m in range(num_ports):
            for n in range(num_ports):
                key = str(m + 1) + " " + str(n + 1)
                data_offset = m * num_ports + n
                if data.ndim == 2:
                    # more than 1 frequency point
                    real_part = data[f_index, re_s11_column + data_offset]
                    imag_part = data[f_index, im_s11_column + data_offset]
                else:
                    # single frequency data
                    real_part = data[re_s11_column + data_offset]
                    imag_part = data[im_s11_column + data_offset]

                Smn = real_part + 1j * imag_part
                dB[key] = todb(Smn)
                arg[key] = toangle(Smn)

        S_dB.append(dB)
        S_arg.append(arg)

    # set unit GHz
    freq_unit = "GHz"

    return num_ports, freq_unit


def parse_palace_csv(input_filename, freq, S_dB, S_arg):
    """Read a Palace port-S.csv and append its S-parameters into the caller's
    freq / S_dB / S_arg lists.

    The header line names the columns (|S[a][b]| arg(S[a][b])); each later line is
    one frequency with alternating magnitude(dB)/phase(deg) values. Values are stored
    keyed by 'a b' in a per-frequency dict. Returns (num_ports, freq_unit). Mutates the
    passed-in lists in place (same accumulation pattern as parse_elmer_results)."""
    params = []

    with open(input_filename) as input_file:
        for line in input_file:
            aline = line.rstrip()
            aline = aline.replace(",", "")
            aline = aline.replace("(dB)", "")
            aline = aline.replace("(deg.)", "")

            dB = {}
            arg = {}

            # check if we have the header line
            if "Hz)" in aline:
                # get unit from header line
                items = aline.split()
                freq_unit = re.sub("[()]", "", items[1])

                # find what parameters we have in this line
                # items are like this:      |S[1][1]| arg(S[1][1])

                num_ports = 0

                for item in items:
                    if "|" in item:
                        Sxx = item.replace("|S", "")
                        Sxx = Sxx.replace("|", "")
                        # Sxx is like this: [1][1]'
                        Sxx = Sxx.replace("][", " ")
                        # Sxx is like this: [1 1]
                        Sxx = Sxx.replace("[", "")
                        Sxx = Sxx.replace("]", "")
                        # Sxx is like this: 1 1
                        params.append(str(Sxx))

                        # get port indices a and b from Sxx
                        split = Sxx.split()
                        a = int(split[0])
                        b = int(split[1])
                        num_ports = max(num_ports, a, b)

                print("Number of ports: ", num_ports)

            else:
                # process data line
                items = aline.split()
                f = items[0]
                for param in params:
                    dB_index = 2 * params.index(param) + 1
                    arg_index = dB_index + 1

                    dB[param] = items[dB_index]
                    arg[param] = items[arg_index]

                    # do we already have the frequency point?
                    if f in freq:
                        f_index = freq.index(f)
                        dB_dict = S_dB[f_index]
                        arg_dict = S_arg[f_index]

                        dB_dict[param] = items[dB_index]
                        arg_dict[param] = items[arg_index]

                    else:
                        freq.append(f)
                        S_dB.append(dB)
                        S_arg.append(arg)

    input_file.close()
    return num_ports, freq_unit


# ---------------------------


def traverse_directories(path, level=0):
    """Recursively walk `path`, appending every port-S.csv (Palace) and
    scalar_results.names (Elmer) result file found to the module-level
    `found_datafiles` list. Permission/not-found errors are printed and skipped."""
    try:
        items_in_path = os.listdir(path)
        for item in items_in_path:
            item_path = os.path.join(path, item)

            if os.path.isdir(item_path):
                traverse_directories(item_path, level + 1)
            elif item == "port-S.csv":
                found_datafiles.append(item_path)
            elif item == "scalar_results.names":
                found_datafiles.append(item_path)

    except PermissionError:
        print(item + "[Permission Denied]")
    except FileNotFoundError:
        print(item + "[Not Found]")


# ----------------------

# extrapolate down to DC


def extrapolate_to_DC(snp_filename):
    """Add an extrapolated DC (0 Hz) point to a Touchstone file, if it has enough
    low-frequency data to justify it (>20 points and data reaching <=1 GHz).

    Writes a sibling '<name>_dc.sNp' via skrf's cubic polar extrapolation and returns
    its path (without extension); returns '' if the file didn't qualify."""
    nw = rf.Network(snp_filename)

    returnval = ""
    # check if we have point below 1 GHz, otherwise exit
    if nw.frequency.npoints > 20:
        if nw.frequency.start <= 1e9:
            if True:  # nw.frequency.npoints > 50:
                # extrapolate to DC
                extrapolated = nw.extrapolate_to_dc(points=None, dc_sparam=None, kind="cubic", coords="polar")
                filename, file_extension = os.path.splitext(snp_filename)
                out_filename = filename + "_dc"  # without extension
                extrapolated.write_touchstone(
                    out_filename,
                    skrf_comment="DC point added by extrapolation",
                    form="db",
                    write_noise=True,
                )
                returnval = out_filename
                print("Created file with DC extrapolation: ", out_filename, "\n")
            else:
                print("Not enough frequency points, skipping DC extrapolation")
        else:
            print("No data at low frequency, skipping DC extrapolation")
    else:
        print("Skipping DC extrapolation, not enough frequency points")
    # return empty string or filename of DC extrapolated data
    return returnval


# ----------------------

# optional de-embdedding of port inductance


def flat_strip_inductance(length, width, thickness, unit):
    """
    Flat Wire Inductor Calculator
    The original for this equation is by F.E. Terman and can be found in the Radio Engineers Handbook, McGraw-Hill, New York, 1945.
    """
    return (
        2e-7
        * length
        * unit
        * (math.log(2 * length / (width + thickness)) + 0.5 + 0.2235 * (width + thickness) / length)
    )


def port_deembedding(snp_filename, port_info_available, port_info_data):
    """Remove the parasitic series inductance of each Palace lumped port from a
    Touchstone file.

    Each port's inductance is estimated from its sheet geometry (flat_strip_inductance),
    then cancelled by cascading a *negative* series inductor at that port. Writes a
    sibling '<name>_deembedded.sNp'. No-op (just a message) when port geometry data
    isn't available."""
    if port_info_available:
        print("Port de-embedding based on port geometry data")
        unit = port_info_data.get("unit", 1e-6)  # default dimension is micron

        # calculate parasitic port inductance for all ports
        Lport = {}
        portlist = port_info_data["ports"]
        for port in portlist:
            portnum = port.get("portnumber", None)
            length = port.get("length", None)
            width = port.get("width", None)
            if (length is not None) and (width is not None) and (portnum is not None):
                thickness = 0  # Palace ports are 2D sheets with no thickness
                L = flat_strip_inductance(length, width, thickness, unit)
                # store into dict for this port number, just in case the port numbers in the file are in wrong sorting order
                Lport[str(portnum)] = L

        # load SnP data and apply negative series L at each port
        ntwk = rf.Network(snp_filename)
        freq = ntwk.frequency
        ntwk.name = "dut"

        # Build the de-embedding circuit with explicit, named connections:
        # external port n -- series L of port n -- DUT port n.
        # Chaining connect(inductor, 0, ntwk, 0) instead put every L at port 1, because
        # connect() puts the inductor's free port first, not last (fixed upstream in
        # gds2palace combine_extend_snp.py, 12-Oct-2026). The L values are looked up by
        # port number, a port without geometry data is connected directly (not de-embedded).
        connections = []
        for n in range(ntwk.nports):
            z0 = ntwk.z0[0, n]
            port = Circuit.Port(freq, f"P{n + 1}", z0=z0)
            if str(n + 1) not in Lport:
                print(f"No geometry data for port {n + 1}, port not de-embedded")
                connections.append([(port, 0), (ntwk, n)])
                continue
            L = -Lport[str(n + 1)]
            print(f"Cascading L= {L * 1e12:.2f} pH at port {n + 1}")
            media = rf.media.DefinedGammaZ0(frequency=freq, z0=z0)
            inductor = media.inductor(L=L, name=f"L{n + 1}")
            connections.append([(port, 0), (inductor, 0)])
            connections.append([(inductor, 1), (ntwk, n)])
        ntwk = Circuit(connections).network

        filename, file_extension = os.path.splitext(snp_filename)
        out_filename = filename + "_deembedded"  # without extension
        ntwk.write_touchstone(
            out_filename,
            skrf_comment="De-embedded by adding negative series L at ports",
            form="db",
            write_noise=True,
        )
        print(
            "Created file with de-embedding (cascaded negative port L): ",
            out_filename,
            "\n",
        )
    else:
        print("Skipping port de-embedding, not port geometry information available")


workdir = os.getcwd()
found_datafiles = []

# work recursively through directories
traverse_directories(workdir)

# evaluate the found data files
for found_filename in found_datafiles:
    # print(str(f))

    # Before we evaluate S-parameters, also check if we have a file port_information.json
    port_info_available = False
    # Get the directory two levels up
    two_up_dir = os.path.abspath(os.path.join(os.path.dirname(found_filename), "..", ".."))
    # Possible full filename for port_information.json
    port_info_filename = os.path.join(two_up_dir, "port_information.json")

    # Check if it exists
    if not os.path.isfile(port_info_filename):
        # let's try one level above
        one_up_dir = os.path.abspath(os.path.join(os.path.dirname(found_filename), ".."))
        # Possible full filename for port_information.json
        port_info_filename = os.path.join(one_up_dir, "port_information.json")

    # If we found the port file one or two levels above
    if os.path.isfile(port_info_filename):
        print(f"Found extra file with port information: {port_info_filename}")

        # Load the JSON data
        with open(port_info_filename) as f:
            port_info_data = json.load(f)

        # Extract all Z0 values
        Z0_values = [port["Z0"] for port in port_info_data.get("ports", []) if "Z0" in port]
        print("Port Z0 values found:", Z0_values)

        Z0_string = str(Z0_values[0])
        for Z in Z0_values:
            if Z != Z0_values[0]:
                Z0_string = Z0_string + " " + str(Z)
        # If string is filled, we have a Z0 parameter for Touchstone header line.
        # For mixed port impedance, we have multiple values there
        port_info_available = True
        print("Port impedance for Touchstone header: ", Z0_string)

        # We might also get the model basename from the port information file.
        # This can be useful for Elmer files where the output file and directory
        # name is always "mesh"
        modelname_from_portinfo = port_info_data.get("name", "")

    else:
        Z0_string = "50"  # default
        modelname_from_portinfo = ""

    # data file items
    freq = []
    S_dB = []
    S_arg = []
    freq_unit = ""
    num_ports = 0

    if "port-S.csv" in found_filename:
        # Palace
        num_ports, freq_unit = parse_palace_csv(found_filename, freq, S_dB, S_arg)
    elif "scalar_results" in found_filename:
        # Elmer
        num_ports, freq_unit = parse_elmer_results(found_filename, freq, S_dB, S_arg)
    else:
        print("Invalid file, exit")
        exit(1)

    data_lines = []

    for frequency in freq:
        # line = str(frequency)

        index = freq.index(frequency)
        data_line = [frequency]

        for i in range(1, num_ports + 1):
            for j in range(1, num_ports + 1):
                # special case 2-port data: the output is S11 S21 S12 S22
                if num_ports == 2:
                    param = str(j) + " " + str(i)
                else:
                    param = str(i) + " " + str(j)

                found_params = S_dB[index].keys()
                # assume that we also have phase data then
                if param in found_params:
                    Sij_dB = S_dB[index].get(param)
                    Sij_arg = S_arg[index].get(param)
                else:
                    Sij_dB = 0.0
                    Sij_arg = 0.0
                # write Sij data
                data_line.append(Sij_dB)
                data_line.append(Sij_arg)

        data_lines.append(data_line)

    # sort data_lines by frequency (first value)
    data_lines.sort(key=lambda x: float(x[0]))

    # get directory where port-S.csv file is stored
    data_path = os.path.dirname(found_filename)
    output_path = data_path

    # get name of parent directory, so that we can use it as filename for output
    splitpath = os.path.split(data_path)
    parentname = splitpath[1]

    # for Elmer, parent name might be "mesh", then we can try to get meaningful name
    # from port information file
    if parentname == "mesh" and modelname_from_portinfo != "":
        parentname = modelname_from_portinfo

    output_filename = parentname + ".s" + str(num_ports) + "p"
    output_filename = os.path.join(output_path, output_filename)

    output_file = open(output_filename, "w")
    # write Touchstone header line
    output_file.write(f"#  {freq_unit.upper()} S DB R {Z0_string}\n")

    for data_line in data_lines:
        line = ""
        for value in data_line:
            line = line + " " + str(value)
        output_file.write(line + "\n")

    output_file.close()
    print(
        "Created combined S-parameter file for ",
        num_ports,
        "ports, filename: ",
        output_filename,
    )

    if not port_info_available:
        print("NOTE: Port impedance not listed in Palace file, assuming 50 Ohm!")
        print("      If required, you can change that value in Touchstone file header!\n")

    # try DC extrapolation
    dc_extrapolated_filename = extrapolate_to_DC(output_filename)

    # try port-deembedding of port geometry information is available
    if port_info_available:
        port_deembedding(output_filename, port_info_available, port_info_data)
        if dc_extrapolated_filename != "":
            # we need to add file extension
            fn = dc_extrapolated_filename + ".s" + str(num_ports) + "p"
            if os.path.isfile(fn):
                port_deembedding(fn, port_info_available, port_info_data)

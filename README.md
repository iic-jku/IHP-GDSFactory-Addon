# IHP Open-PDK GDSFactory Addon

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Test code](https://github.com/iic-jku/IHP-GDSFactory-Addon/actions/workflows/test_code.yml/badge.svg)](https://github.com/iic-jku/IHP-GDSFactory-Addon/actions/workflows/test_code.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](pyproject.toml)

(c) 2025-2026 David Kellerer-Pirklbauer and Simon Dorrer

Institute for Integrated Circuits and Quantum Computing, Johannes Kepler University (JKU), Linz, Austria

## Overview

This repository contains a Python-based Addon for the open-source **IHP SG13G2** 130 nm SiGe:C BiCMOS PDK, built on top of [GDSFactory](https://gdsfactory.github.io/gdsfactory/). The PCells drive the official [IHP-Open-PDK](https://github.com/IHP-GmbH/IHP-Open-PDK) PCell library (`sg13g2_pycell_lib`) through GDSFactory and extend it with parametric microstrip transmission lines and RF/mm-wave building blocks (couplers, dividers, and filters).

Because the layout is generated programmatically in Python, designs are reproducible, version-controllable, and easy to parameterize. PCells can be combined into complex, DRC-clean layouts directly from code.

This project started as a fork of [`gdsfactory/IHP`](https://github.com/gdsfactory/IHP) and is now independently developed and maintained. The version in `gdsfactory/IHP` builds the PCells completely from scratch, whereas this version uses a wrapper layer around the original IHP PCells.

## Features

### PCells

All PCells from the IHP Open-PDK are supported:

- [x] PMOS / NMOS
- [x] BJTs
- [x] Resistors
- [x] Capacitors
- [x] Inductors
- [x] Passives (ESD diodes, ptap, ntap, seal ring, etc.)
- [x] Via stacks
- [x] Bond pads / probe pads
- [x] Antennas

For a detailed implementation status, have a look at the [PCell checklist](KLayout_PCell_Checklist.xlsx).

### Waveguides

- [x] Embedded microstrip
- [x] Edge-coupled microstrip
- [x] 90°-bend microstrip

### RF devices

- [x] Branch-line coupler
- [x] Wilkinson divider
- [x] Directional coupler
- [x] Coupled-line microstrip bandpass filter
- [x] Hairpin coupled-line microstrip bandpass filter
- [x] Quarter-wave transformer

## Requirements

> [!IMPORTANT]
> This Addon requires the [IHP-Open-PDK](https://github.com/IHP-GmbH/IHP-Open-PDK) to be installed, with the environment variable `PDK_ROOT` pointing to its installation directory (defaults to `/foss/pdks`, as used in the [IIC-OSIC-TOOLS](https://github.com/iic-jku/IIC-OSIC-TOOLS) container). The PCells import `sg13g2_pycell_lib` from `$PDK_ROOT/ihp-sg13g2/libs.tech/klayout/python` at load time.

- Python 3.11, 3.12, or 3.13
- [KLayout](https://www.klayout.de/) for viewing the generated layouts

> [!TIP]
> Use the [IIC-OSIC-TOOLS](https://github.com/iic-jku/IIC-OSIC-TOOLS) container with tag `2026.07` or later. Everything is already set up there, and you can start designing immediately.

## Installation

### For users

```sh
pip install git+https://github.com/iic-jku/IHP-GDSFactory-Addon.git
```

### For contributors

```sh
git clone https://github.com/iic-jku/IHP-GDSFactory-Addon.git
cd IHP-GDSFactory-Addon
pip install -e ".[dev]"
pre-commit install
```

### KLayout technology

To install the SG13G2 layer properties and technology into KLayout, run:

```sh
python install_tech.py
```

Then restart KLayout to make the newly installed technology appear.

## Usage

```python
import ihp

ihp.PDK.activate()

c = ihp.cells.straight(length=30, cross_section="metal5_routing")
c.show()  # stream the layout to KLayout (requires the klive plugin)
```

## Directory Structure

```
📁 IHP-GDSFactory-Addon/
├─ 📁 .github/                      → CI workflows (pre-commit, packaging check)
├─ 📁 ihp/                          → the Python package
│  ├─ 📁 cells/                     → PCells: transistors, diodes, R/L/C, bond pads,
│  │                                  ESD, via stacks, microstrips, RF devices, …
│  ├─ 📁 klayout/tech/              → KLayout technology (layers.lyp, tech.lyt)
│  ├─ 📄 config.py                  → package paths
│  ├─ 📄 layer_map_ihp.py           → layer map (generated from layers.lyp)
│  ├─ 📄 tech.py                    → layers, layer stack, and cross-sections
│  └─ 📄 __init__.py                → PDK definition and registration
├─ 📄 install_tech.py               → installs the KLayout technology
├─ 📄 playground.py                 → development playground
├─ 📄 KLayout_PCell_Checklist.xlsx  → PCell implementation status
├─ 📄 pyproject.toml                → package metadata and dependencies
└─ 📄 LICENSE                       → Apache License 2.0
```

## Documentation

- [GDSFactory documentation](https://gdsfactory.github.io/gdsfactory/)
- [IHP-Open-PDK](https://github.com/IHP-GmbH/IHP-Open-PDK)
- [PCell checklist](KLayout_PCell_Checklist.xlsx)

## Acknowledgements

This Addon is developed and maintained at the **Institute for Integrated Circuits and Quantum Computing (IICQC)**, Johannes Kepler University (JKU), Linz, Austria.

## License

Licensed under the **Apache License 2.0**, see [`LICENSE`](LICENSE).

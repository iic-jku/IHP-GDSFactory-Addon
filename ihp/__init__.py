"""IHP PDK."""

# Inject sg13g2_pycell_lib paths early so the submodule imports below can
# resolve `from sg13g2_pycell_lib...` at module load. The sys.path setup in
# `ihp.cells.utils` only runs after `ihp.cells.__init__` has tried to import
# the passive PCells, so it is too late to satisfy the first failing import.
import os as _os
import sys as _sys

_pdk_root = _os.environ.get("PDK_ROOT", "/foss/pdks")
for _p in (
    _os.path.join(_pdk_root, "ihp-sg13g2/libs.tech/klayout/python"),
    _os.path.join(
        _pdk_root,
        "ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/",
    ),
):
    if _p not in _sys.path:
        _sys.path.append(_p)

from typing import cast

from gdsfactory.get_factories import get_cells
from gdsfactory.pdk import Pdk
from gdsfactory.typings import (
    ConnectivitySpec,
)

from ihp import cells, tech
from ihp.config import PATH

# from ihp.models import get_models
from ihp.tech import (
    LAYER,
    LAYER_STACK,
    LAYER_VIEWS,
    cross_sections,
    # routing_strategies,
)

components = cells

__version__ = "0.1.1"
__all__ = [
    "PATH",
    "components",
    "tech",
    "LAYER",
    "cells",
    "cross_sections",
    "PDK",
    "__version__",
]

connectivity = cast(
    list[ConnectivitySpec],
    [
        ("METAL1", "VIA1", "METAL2"),
        ("METAL2", "VIA2", "METAL3"),
        ("METAL3", "VIA3", "METAL4"),
        ("METAL4", "VIA4", "METAL5"),
        ("METAL5", "TOPVIA1", "TOPMETAL1"),
        ("TOPMETAL1", "TOPVIA2", "TOPMETAL2"),
    ],
)

_cells = get_cells(cells)
PDK = Pdk(
    name="IHP",
    cells=_cells,
    cross_sections=cross_sections,
    # models=get_models(),
    layers=LAYER,
    layer_stack=LAYER_STACK,
    layer_views=LAYER_VIEWS,
    connectivity=connectivity,
    # routing_strategies=routing_strategies,
)

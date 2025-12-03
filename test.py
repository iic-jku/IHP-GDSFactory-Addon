import gdsfactory as gf
import ihp
import sys
import os

from ihp.cells.utils import add_port_group, change_port_orientation

# paths_to_remove = [
#     "/foss/pdks/ihp-sg13g2/libs.tech/klayout/python",
#     "/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python/"
# ]

# for p in paths_to_remove:
#     if p in sys.path:
#         sys.path.remove(p)

# import sys

# # Print every path entry on its own line
# for p in sys.path:
#     print(p)

ihp.PDK.activate()


# c= ihp.cells.straight(length = 30, cross_section="metal5_routing")
# c.show()


# ----------------------------------------------------------------
# not working anymore due to changes in via array generation

# c = ihp.cells.via_stack(bottom_layer="Metal1", top_layer="TopMetal2", vn_columns=3, vn_rows=4)
# c.show()

# ----------------------------------------------------------------


# c = ihp.cells.via_stack_test(bottom_layer="TopMetal2", top_layer="Metal2", vn_columns=3, vn_rows=4)
# c.draw_ports()
# c.show()

# ----------------------------------------------------------------

# c = ihp.cells.nmos(width=0.15, length=0.13, nf=1, m=1)
# c.show()

# ----------------------------------------------------------------

# c = gf.import_gds("ihp/gds/test.gds").copy()
# c.pprint_ports()
# c.show()

# c_with_ports = gf.add_ports.add_ports_from_boxes(c, pin_layer=(ihp.LAYER.Metal1pin), port_type="electrical", port_name_prefix="DS", ports_on_short_side=True)
# c_with_ports = gf.add_ports.add_ports_from_boxes(c, pin_layer=(ihp.LAYER.GatPolypin), port_type="electrical", port_name_prefix="G", ports_on_short_side=True)
# c_with_ports.pprint_ports()
# c_with_ports.draw_ports()
# c_with_ports.show()

# ----------------------------------------------------------------

# c = gf.read.import_gds("ihp/gds/test2.gds")
# c.pprint_ports()
# c.show()

# c_with_ports = gf.add_ports.add_ports_from_boxes(c, pin_layer=(ihp.LAYER.Metal1drawing), port_type="electrical", port_name_prefix="DS", ports_on_short_side=True)
# c_with_ports = gf.add_ports.add_ports_from_boxes(c, pin_layer=(ihp.LAYER.GatPolydrawing), port_type="electrical", port_name_prefix="G", ports_on_short_side=True)
# c_with_ports.pprint_ports()
# c_with_ports.draw_ports()
# c_with_ports.show()

# ----------------------------------------------------------------

# c = gf.Component()
# nm_1 = ihp.cells.nmos(ng = 10).copy()
# nm_2 = ihp.cells.nmos(ng = 8).copy()
# nm_1_ref = c.add_ref(nm_1)
# nm_1_ref_2 = c.add_ref(nm_1)
# nm_1_ref_2.move((0, 1))
# pm = c.add_ref(ihp.cells.pmos(ng = 5).copy())
# nm_2_ref = c.add_ref(nm_2)

# nm_2.move((0, -2))
# pm.move((0, -1))
# c.show()


# wg = ihp.cells.straight(length = 2, width = 0.16, cross_section="metal1_routing")
# wg.draw_ports()
# wg_ref = c.add_ref(wg)

# wg_ref.connect("e1", nm_1_ref.ports["DS_9"], allow_width_mismatch=True)
# nm_2_ref.connect("DS_1", wg_ref.ports["e2"], allow_width_mismatch=True)

# nm_1.draw_ports()
# nm_2.draw_ports()
# c.draw_ports()
# print("NMOS 1 ports:")
# nm_1.pprint_ports()
# c.add_ports(nm_1.ports)
# c.add_ports(nm_2.ports)
# c.add_ports(pm.ports)
# print("Component ports:")
# c.pprint_ports()
# c.show()


# -----------------------------------------------------------------
# antennas test

# c = gf.Component()

# da = c.add_ref(ihp.cells.dantenna(width = 5, guardRingType="psub", guardRingDistance=2))
# c.add_port(name="da_e1", port=da.ports["e2"]) # when using a component with a guard ring, the port you want to add must be specified manually
# c.pprint_ports()
# c.draw_ports()

# c.move((0,6))
# dpa1 = c.add_ref(ihp.cells.dpantenna(guardRingType="psub", guardRingDistance=2))
# c.add_ports(dpa1.ports, prefix="dpa1_")   # adding all ports results in unwanted ports from the guard ring being added

# # new function add_port_group test
# c.move((0,6))
# dpa2 = c.add_ref(ihp.cells.dpantenna(guardRingType="psub", guardRingDistance=2))
# add_port_group(c, dpa2, ports=["e1", "e3"], prefix="dpa2_")   # adding specific ports using the new function  

# c.pprint_ports()
# c.draw_ports()
# c.show()

# ----------------------------------------------------------------
# bjt transistors test

# c = gf.Component()

# npn = c.add_ref(ihp.cells.npn13G2(Nx=4))
# c.add_ports(npn.ports, prefix="npn_")
# c.move((4,11))

# npnL = c.add_ref(ihp.cells.npn13G2L(Nx=10))
# c.add_ports(npnL.ports, prefix="npnL_")
# c.ports["npnL_B"].orientation =270      # change port orientation
# c.ports["npnL_B"].center = (c.ports["npnL_B"].center[0] + 5, c.ports["npnL_B"].center[1]) # change port position
# c.move((0,8))

# npnV = c.add_ref(ihp.cells.npn13G2V(Nx=15))
# c.add_ports(npnV.ports, prefix="npnV_")
# c.move((-3.5,4))

# pnp = c.add_ref(ihp.cells.pnpMPA().copy())
# c.add_ports(pnp.ports, prefix="pnp_")
# c.move((3,3))
# c.draw_ports()
# c.pprint_ports()
# c.show()

# -----------------------------------------------------------------
# bondpad test

# c = gf.Component()

# c.add_ref(ihp.cells.bondpads.bondpad(shape="octagon", topMetal="TM1"))

# c.move((0,100))
# c.add_ref(ihp.cells.bondpads.bondpad_array(n_pads=4, pad_pitch=100))
# c.show()

# -----------------------------------------------------------------
# capacitor test

c = gf.Component()

cmim1 = c.add_ref(ihp.cells.cmim(width=10, length=10, guardRingType="psub", guardRingDistance=1))
c.move((40,0))
cmim2 = c.add_ref(ihp.cells.cmim(width=20, length=20))
c.add_ports(cmim1.ports, prefix="cmim1_")
c.add_ports(cmim2.ports, prefix="cmim2_")


c.move((-40,35))
rfcmim1 = c.add_ref(ihp.cells.rfcmim(width=10, length=10))
c.move((40,0))
rfcmim2 = c.add_ref(ihp.cells.rfcmim(width=20, length=20))
c.add_ports(rfcmim1.ports, prefix="rfcmim1_")
c.add_ports(rfcmim2.ports, prefix="rfcmim2_")

c.move((-40,35))
svaricap1 = c.add_ref(ihp.cells.svaricap(Nx=1))
c.move((40,0))
svaricap2 = c.add_ref(ihp.cells.svaricap(Nx=10, guardRingType="nwell", guardRingDistance=2))
c.add_ports(svaricap1.ports, prefix="svaricap1_")
c.add_ports(svaricap2.ports, prefix="svaricap2_")
c.draw_ports()
c.pprint_ports()
c.show()

# ----------------------------------------------------------------
# inductor test

# c = gf.Component()

# ind2 = c.add_ref(ihp.cells.inductor2(guardRingType="psub", guardRingDistance=2))
# c.add_ports(ind2.ports, prefix="ind2_")
# c.move((-100, 0))

# ind3 = c.add_ref(ihp.cells.inductor3())
# c.add_ports(ind3.ports, prefix="ind3_")
# c.draw_ports()
# c.pprint_ports()
# c.show()

# ----------------------------------------------------------------
# test mos_transistors.py 

# c = gf.Component()

# nmos = c.add_ref(ihp.cells.nmos(ng = 5, guardRingType="psub", guardRingDistance=1))
# ps = {"e4", "e5", "e6", "e7", "e8", "e9"}

# c = add_port_group(c, nmos, ps)

# c = change_port_orientation(c, ps, 90)

# c.add_ref(ihp.cells.pmos(ng=1, guardRingType="nwell", guardRingDistance=1))
# c.move((0,5))

# c.add_ref(ihp.cells.nmosHV(ng = 1, guardRingType="psub", guardRingDistance=1))
# c.move((0,5))

# c.add_ref(ihp.cells.pmosHV(ng=1, guardRingType="nwell", guardRingDistance=1))
# c.move((1.5,3))

# c.add_ref(ihp.cells.rfnmos(ng = 1)).rotate(-90)
# c.move((0,5))

# c.add_ref(ihp.cells.rfnmosHV(ng=1)).rotate(-90)
# c.move((0,5))

# c.add_ref(ihp.cells.rfpmos(ng = 1)).rotate(-90)
# c.move((0,5))

# c.add_ref(ihp.cells.rfpmosHV(ng=1)).rotate(-90)
# c.move((0,5))

# c.pprint_ports()
# c.draw_ports()
# c.show()

# -----------------------------------------------------------------
# passives test

# c = gf.Component()

# esd = c.add_ref(ihp.cells.esd(model="diodevss_4kv"))
# c.add_ports(esd.ports, prefix="esd_")

# c.move((0,5))
# ptap1 = c.add_ref(ihp.cells.ptap1())
# c.add_ports(ptap1.ports, prefix="ptap1_")

# c.move((0,5))
# ntap1 = c.add_ref(ihp.cells.ntap1())
# c.add_ports(ntap1.ports, prefix="ntap1_")

# c.move((200,200))
# sealring = c.add_ref(ihp.cells.sealring())
# c.add_ports(sealring.ports, prefix="sealring_")

# c.draw_ports()
# c.pprint_ports()
# c.show()

# -----------------------------------------------------------------
# resistor test

# c = gf.Component()

# rhigh1 = c.add_ref(ihp.cells.rhigh(length=10, guardRingType="psub", guardRingDistance=2, bends= 2, numberOfSegments=2, segmentConnection="Parallel"))
# c.move((5,0))
# rhigh2 = c.add_ref(ihp.cells.rhigh(length=20, width=1))
# c.add_ports(rhigh1.ports, prefix="rhigh1_")
# c.add_ports(rhigh2.ports, prefix="rhigh2_")

# c.move((5,0))
# rppd1 = c.add_ref(ihp.cells.rppd(length=10))
# c.move((5,0))
# rppd2 = c.add_ref(ihp.cells.rppd(length=20, width=1))
# c.add_ports(rppd1.ports, prefix="rppd1_")
# c.add_ports(rppd2.ports, prefix="rppd2_")

# c.move((5,0))
# rsil1 = c.add_ref(ihp.cells.rsil(length=10))
# c.move((5,0))
# rsil2 = c.add_ref(ihp.cells.rsil(length=20, width=1))
# c.add_ports(rsil1.ports, prefix="rsil1_")
# c.add_ports(rsil2.ports, prefix="rsil2_")

# c.draw_ports()
# c.pprint_ports()
# c.show()

# -----------------------------------------------------------------
# stack test

# c = gf.Component()

# vs1 = c.add_ref(ihp.cells.via_stack(top_layer="TopMetal2", bottom_layer="Metal1"))
# c.add_ports(vs1.ports, prefix="vs1_")

# c.move((5,15))
# c.add_ref(ihp.cells.via_stacks.no_filler_stack())

# c.draw_ports()
# c.pprint_ports()
# c.show()
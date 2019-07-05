# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

import gdspy
import numpy as np
from picwriter.components import *
from picwriter import toolkit as tk

""" Test cases below for each component type in the library.  Checks creation and size. """
class TestPICwriter(TestCase):
	global AREA_TOL
	AREA_TOL = 1E-1 # Some variation is expected when small updates occur to library
	def test_waveguide_creation(self):
		top = gdspy.Cell("t1")
		wgt = WaveguideTemplate(bend_radius=50, resist='+', fab="LIFTOFF")
		wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
		wg2=Waveguide([(0,0), (0,100), (-250, 100), (-250, -100)], wgt)
		tk.add(top, wg1)
		tk.add(top, wg2)
		print("Waveguide area = "+str(top.area()))
		self.assertTrue(len(top.references)==2)
		self.assertTrue(abs(top.area()-33939.41272703404) <= AREA_TOL)

	def test_metal_creation(self):
		top = gdspy.Cell("t-electrical")
		mt = MetalTemplate(bend_radius=0, resist='+', fab="ETCH")
		mt1=MetalRoute([(0,0), (0,250), (100,250), (100,500), (400,500)], mt)
		tk.add(top, mt1)
		print("MetalRoute area = "+str(top.area()))
		self.assertTrue(len(top.references)==1)
		self.assertTrue(abs(top.area()-88800.0) <= AREA_TOL)

	def test_taper_creation(self):
		top = gdspy.Cell("t2")
		wgt = WaveguideTemplate(bend_radius=50, resist='+')
		wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
		tk.add(top, wg1)
		tp1 = Taper(wgt, 100.0, 0.3, **wg1.portlist["input"])
		tp2 = Taper(wgt, 100.0, 0.0, **wg1.portlist["output"])
		tk.add(top, tp1)
		tk.add(top, tp2)
		print("Taper area = "+str(top.area()))
		self.assertTrue(len(top.references)==3)
		self.assertTrue(abs(top.area()-27005.706363517016) <= AREA_TOL)

	def test_grating_coupler_creation(self):
		top = gdspy.Cell("t3")
		wgt = WaveguideTemplate(bend_radius=50, resist='+', fab='ETCH')
		wg1=Waveguide([(0,0), (250,0), (250,500), (500,500)], wgt)
		tk.add(top, wg1)
		gc1 = GratingCouplerStraight(wgt, width=20, length=50, taper_length=20, period=1.0, dutycycle=0.7, **wg1.portlist["input"])
		tk.add(top, gc1)
		gc2 = GratingCouplerFocusing(wgt, focus_distance=20.0, width=20, length=50, period=1.0, dutycycle=0.7, **wg1.portlist["output"])
		tk.add(top, gc2)
		print("Grating coupler area = "+str(top.area()))
		self.assertTrue(len(top.references)==3)
		self.assertTrue(abs(top.area()-30061.488748043674) <= AREA_TOL)

	def test_spiral_creation(self):
		top = gdspy.Cell("t4")
		wgt = WaveguideTemplate(bend_radius=50, resist='-')

		sp1 = Spiral(wgt,
		width=2000.0,
		length=20000.0,
		spacing=50.0,
		parity=1,
		port=(0,-10000),
		direction='WEST')
		tk.add(top, sp1)

		print("Spiral area = "+str(top.area()))
		self.assertTrue(len(top.references)==1)
		self.assertTrue(abs(top.area()-479997.9517151703) <= AREA_TOL)

	def test_mmi1x2_creation(self):
		top = gdspy.Cell("t-mmi1x2")
		wgt = WaveguideTemplate(bend_radius=50, resist='+')
		wg1=Waveguide([(0,0), (250,0)], wgt)
		tk.add(top, wg1)
		mmi = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, **wg1.portlist["output"])
		tk.add(top, mmi)
		print("MMI1x2 area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==2)
		self.assertTrue(abs(top.area()-11623.153798646574) <= AREA_TOL)

	def test_mmi2x2_creation(self):
		top = gdspy.Cell("t6")
		wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

		wg1=Waveguide([(0, 0), (0, -100)], wgt)
		tk.add(top, wg1)
		mmi = MMI2x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3.0, port=(0,0), direction='EAST')
		tk.add(top, mmi)
		print("MMI2x2 area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==2)
		self.assertTrue(abs(top.area()-9482.165964182654) <= AREA_TOL)

	def test_ring_creation(self):
		top = gdspy.Cell("t7")
		wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

		wg1=Waveguide([(0,0), (100,0)], wgt)
		tk.add(top, wg1)
		r1 = Ring(wgt, 60.0, 1.0, parity=1, **wg1.portlist["output"])
		tk.add(top, r1)
		print("Ring area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==2)
		self.assertTrue(abs(top.area()-13133.377916248292) <= AREA_TOL)

	def test_disk_creation(self):
		top = gdspy.Cell("t8")
		wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

		wg1=Waveguide([(0,0), (100,0)], wgt)
		tk.add(top, wg1)
		d1 = Disk(wgt, 60.0, 1.0, parity=1, **wg1.portlist["output"])
		tk.add(top, d1)
		print("Disk area = "+str(top.area()))
		print(len(top.references))
		for t in top.references:
			print("reference cell = "+str(t.ref_cell))
			print("reference cell polygons = "+str(t.ref_cell.polygons))
			for polyset in t.ref_cell.polygons:
				print("polygon = "+str(polyset.polygons))
		self.assertTrue(len(top.references)==2)
		self.assertTrue(abs(top.area()-32153.142850436107) <= AREA_TOL)

	def test_mzi_creation(self):
		top = gdspy.Cell("t-mzi")
		wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')
		htr_mt = MetalTemplate(width=25, clad_width=25, bend_radius=wgt.bend_radius, resist='+', fab="ETCH", metal_layer=13, metal_datatype=0, clad_layer=14, clad_datatype=0)
		mt = MetalTemplate(width=25, clad_width=25, resist='+', fab="ETCH", metal_layer=11, metal_datatype=0, clad_layer=12, clad_datatype=0)

		wg_in = Waveguide([(0,0), (300,0)], wgt)
		tk.add(top, wg_in)
		mzi = MachZehnder(wgt, MMIlength=50, MMIwidth=10, MMItaper_width=2.0, MMIwg_sep=3, arm1=0, arm2=100, heater=True, heater_length=400, mt=htr_mt, **wg_in.portlist["output"])
		tk.add(top, mzi)
		wg_out = Waveguide([mzi.portlist["output"]["port"], (mzi.portlist["output"]["port"][0]+300, mzi.portlist["output"]["port"][1])], wgt)
		tk.add(top, wg_out)
		print("MZI area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==3)
		self.assertTrue(abs(top.area()-184056.04963673785) <= AREA_TOL)
  		
		mzi2 = MachZehnderSwitch1x2(wgt, MMI1x2length=50, MMI1x2width=10, MMI2x2length=100, MMI2x2width=12, angle=np.pi/6.0, MMI1x2taper_width=2.0, MMI1x2taper_length=30.0,MMI1x2wg_sep=5.0, MMI2x2taper_width=2.0, MMI2x2wg_sep=6.0, arm1=300, arm2=250, heater=False, heater_length=400, mt=None, **wg_in.portlist["output"])
		mzi3 = MachZehnderSwitchDC1x2(wgt, MMI1x2length=50, MMI1x2width=10, MMI1x2taper_width=2.0, MMI1x2wg_sep=3, DClength=100, DCgap=0.5, arm1=500, arm2=500, heater=False, heater_length=400, mt=htr_mt, **wg_in.portlist["output"])
		mzi4 = MachZehnderSwitchDC2x2(wgt, DC1length=200, DC1gap=0.5, DC2length=100, DC2gap=1.5, arm1=500, arm2=500, heater=True, heater_length=400, mt=htr_mt, **wg_in.portlist["output"])
		tk.add(top, mzi2)
		tk.add(top, mzi3)
		tk.add(top, mzi4)
		self.assertTrue(len(top.references)==6)
	def test_dbr_creation(self):
		top = gdspy.Cell("t-dbr")
		wgt = WaveguideTemplate(bend_radius=50, resist='+')

		wg1=Waveguide([(0,0), (100,0)], wgt)
		tk.add(top, wg1)

		dbr1 = DBR(wgt, 10.0, 0.85, 0.5, 0.4, **wg1.portlist["output"])
		tk.add(top, dbr1)

		(x1, y1) = dbr1.portlist["output"]["port"]
		wg2=Waveguide([(x1,y1), (x1+100,y1), (x1+100,y1+100)], wgt)
		tk.add(top, wg2)

		dbr2 = DBR(wgt, 10.0, 0.85, 0.5, 0.6, **wg2.portlist["output"])
		tk.add(top, dbr2)
		print("DBR area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==4)
		self.assertTrue(abs(top.area()-9093.453181758501) <= AREA_TOL)

	def test_dc_creation(self):
		top = gdspy.Cell("t-dc")
		wgt = WaveguideTemplate(bend_radius=100, resist='+')

		wg1=Waveguide([(0,0), (100,0)], wgt)
		tk.add(top, wg1)

		import numpy as np
		dc1 = DirectionalCoupler(wgt, 10.0, 0.5, angle=np.pi/6.0, parity=1, **wg1.portlist["output"])
		dc2 = DirectionalCoupler(wgt, 10.0, 0.5, angle=np.pi/6.0, parity=-1, **dc1.portlist["output_top"])
		dc3 = DirectionalCoupler(wgt, 10.0, 0.5, angle=np.pi/6.0, parity=1, **dc1.portlist["output_bot"])
		dc4 = DirectionalCoupler(wgt, 10.0, 0.5, angle=np.pi/6.0, parity=1, **dc2.portlist["output_bot"])
		dc5 = DirectionalCoupler(wgt, 10.0, 0.5, angle=np.pi/6.0, parity=-1, **dc2.portlist["output_top"])
		dc6 = DirectionalCoupler(wgt, 10.0, 0.5, angle=np.pi/6.0, parity=1, **dc3.portlist["output_bot"])
		tk.add(top, dc1)
		tk.add(top, dc2)
		tk.add(top, dc3)
		tk.add(top, dc4)
		tk.add(top, dc5)
		tk.add(top, dc6)
		self.assertTrue(len(top.references)==7)
		self.assertTrue(abs(top.area()-65614.5258016434) <= AREA_TOL)

	def test_contradc_creation(self):
		top = gdspy.Cell("t-contradc")
		wgt = WaveguideTemplate(wg_width=1.0, bend_radius=50, resist='+')

		wg1=Waveguide([(0,0), (20,0)], wgt)
		tk.add(top, wg1)

		cdc = ContraDirectionalCoupler(wgt, length=30.0, gap=0.5, period=0.220, dc=0.5, angle=np.pi/12.0, width_top=3.0, width_bot=0.75, input_bot=True, **wg1.portlist["output"])
		tk.add(top, cdc)
		print("Contra DC area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==2)
		self.assertTrue(abs(top.area()-4221.992567042908) <= AREA_TOL)

	def test_stripslotconverter_creation(self):
		top = gdspy.Cell("t-stripslotyconverter")
		wgt_strip = WaveguideTemplate(bend_radius=50, wg_type='strip', wg_width=0.7)
		wgt_slot = WaveguideTemplate(bend_radius=50, wg_type='slot', wg_width=0.7, slot=0.2)
		wg1=Waveguide([(0,0), (100,0)], wgt_strip)
		tk.add(top, wg1)

		ycoup = StripSlotYConverter(wgt_strip, wgt_slot, 10.0, 0.2, end_slot_width=0, **wg1.portlist["output"])
		tk.add(top, ycoup)

		(x1,y1)=ycoup.portlist["output"]["port"]
		wg2=Waveguide([(x1, y1), (x1+100, y1)], wgt_slot)
		tk.add(top, wg2)
		
		coup2 = StripSlotMMIConverter(wgt_strip, wgt_slot, 2.5, 6.0, 20.0, **wg2.portlist["output"])
		tk.add(top, coup2)
  
		coup3 = StripSlotConverter(wgt_strip, 
                             wgt_slot, 
                             length1 = 15.0, 
                             length2 = 15.0, 
                             start_rail_width = 0.1,
                             end_strip_width = 0.4,
                             d = 1.0,
                             **coup2.portlist["output"])
		tk.add(top, coup3)
		
		print("StripSlotConverter area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==5)
		self.assertTrue(abs(top.area()-5559.85) <= AREA_TOL)

	def test_adiabaticcoupler_creation(self):
		top = gdspy.Cell("t-ac")
		wgt = WaveguideTemplate(wg_width=2.0, bend_radius=100, resist='+')
		wg1=Waveguide([(0,0), (100,0)], wgt)
		tk.add(top, wg1)

		ac = AdiabaticCoupler(wgt, 
                          length1=60.0, 
                          length2=50.0,
                          gap=0.5, 
                          fargap=6.0,
                          dw=1.0, 
                          angle=np.pi/16.0, 
                          **wg1.portlist["output"])
		tk.add(top, ac)

		print("AdiabaticCoupler area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==2)
		self.assertTrue(abs(top.area()-11449.803524547198) <= AREA_TOL)
  
  
	def test_fullcoupler_creation(self):
		top = gdspy.Cell("t-fc")
		wgt = WaveguideTemplate(wg_width=2.0, bend_radius=100, resist='+')
		wg1=Waveguide([(0,0), (100,0)], wgt)
		tk.add(top, wg1)

		fc = FullCoupler(wgt, 40.0, 0.5, 1.0, angle=np.pi/12.0, parity=1, **wg1.portlist["output"])
		tk.add(top, fc)

		print("FullCoupler area = "+str(top.area()))
		print(len(top.references))
		self.assertTrue(len(top.references)==2)
		self.assertTrue(abs(top.area()-9346.404699396264) <= AREA_TOL)
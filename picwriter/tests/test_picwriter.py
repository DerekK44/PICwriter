# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

import gdspy
from picwriter.components import *
from picwriter import toolkit as tk

""" Test case below not necessary, but should serve as framework for later """
class TestPICwriter(TestCase):
	def test_waveguide_creation(self):
		top = gdspy.Cell("t1")
		wgt = WaveguideTemplate(bend_radius=50, resist='+', fab="LIFTOFF")
		wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
		wg2=Waveguide([(0,0), (0,100), (-250, 100), (-250, -100)], wgt)
		tk.add(top, wg1)
		tk.add(top, wg2)
		# print("Waveguide area = "+str(top.area()))
		self.assertTrue(len(top.elements)==2)
		self.assertTrue(abs(top.area()-33939.818854) <= 1e-6)

	def test_metal_creation(self):
		top = gdspy.Cell("t-electrical")
		mt = MetalTemplate(bend_radius=0, resist='+', fab="ETCH")
		mt1=MetalRoute([(0,0), (0,250), (100,250), (100,500), (400,500)], mt)
		tk.add(top, mt1)
		# print("MetalRoute area = "+str(top.area()))
		self.assertTrue(len(top.elements)==1)
		self.assertTrue(abs(top.area()-88800.0) <= 1e-6)

	def test_taper_creation(self):
		top = gdspy.Cell("t2")
		wgt = WaveguideTemplate(bend_radius=50, resist='+')
		wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
		tk.add(top, wg1)
		tp1 = Taper(wgt, 100.0, 0.3, **wg1.portlist["input"])
		tp2 = Taper(wgt, 100.0, 0.0, **wg1.portlist["output"])
		tk.add(top, tp1)
		tk.add(top, tp2)
		# print("Taper area = "+str(top.area()))
		self.assertTrue(len(top.elements)==3)
		self.assertTrue(abs(top.area()-27005.909427) <= 1e-6)

	def test_grating_coupler_creation(self):
		top = gdspy.Cell("t3")
		wgt = WaveguideTemplate(bend_radius=50, resist='+', fab='ETCH')
		wg1=Waveguide([(0,0), (250,0), (250,500), (500,500)], wgt)
		tk.add(top, wg1)
		gc1 = GratingCouplerStraight(wgt, width=20, length=50, taper_length=20, period=1.0, dutycycle=0.7, **wg1.portlist["input"])
		tk.add(top, gc1)
		gc2 = GratingCouplerFocusing(wgt, focus_distance=20.0, width=20, length=50, period=1.0, dutycycle=0.7, **wg1.portlist["output"])
		tk.add(top, gc2)
		# print("Grating coupler area = "+str(top.area()))
		self.assertTrue(len(top.elements)==3)
		self.assertTrue(abs(top.area()-30061.6918115) <= 1e-6)

	def test_spiral_creation(self):
		top = gdspy.Cell("t4")
		wgt = WaveguideTemplate(bend_radius=50, resist='-')
		sp1 = Spiral(wgt, 1000.0, 1000.0, 10000.0)
		tk.add(top, sp1)
		# print("Spiral area = "+str(top.area()))
		self.assertTrue(len(top.elements)==1)
		self.assertTrue(abs(top.area()-241199.988149) <= 1e-6)

	def test_mmi1x2_creation(self):
		top = gdspy.Cell("t5")
		wgt = WaveguideTemplate(bend_radius=50, resist='+')
		wg1=Waveguide([(0,0), (250,0)], wgt)
		tk.add(top, wg1)
		mmi = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, **wg1.portlist["output"])
		tk.add(top, mmi)
		# print("MMI1x2 area = "+str(top.area()))
		print(len(top.elements))
		self.assertTrue(len(top.elements)==2)
		self.assertTrue(abs(top.area()-9190.0) <= 1e-6)

	def test_mmi2x2_creation(self):
		top = gdspy.Cell("t6")
		wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

		wg1=Waveguide([(0, 0), (0, -100)], wgt)
		tk.add(top, wg1)
		mmi = MMI2x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3.0, port=(0,0), direction='EAST')
		tk.add(top, mmi)
		# print("MMI2x2 area = "+str(top.area()))
		print(len(top.elements))
		self.assertTrue(len(top.elements)==2)
		self.assertTrue(abs(top.area()-5640.0) <= 1e-6)

	def test_ring_creation(self):
		top = gdspy.Cell("t7")
		wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

		wg1=Waveguide([(0,0), (100,0)], wgt)
		tk.add(top, wg1)
		r1 = Ring(wgt, 60.0, 1.0, parity=1, **wg1.portlist["output"])
		tk.add(top, r1)
		# print("Ring area = "+str(top.area()))
		print(len(top.elements))
		self.assertTrue(len(top.elements)==2)
		self.assertTrue(abs(top.area()-13133.8016946) <= 1e-6)

	def test_disk_creation(self):
		top = gdspy.Cell("t8")
		wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

		wg1=Waveguide([(0,0), (100,0)], wgt)
		tk.add(top, wg1)
		d1 = Disk(wgt, 60.0, 1.0, parity=1, **wg1.portlist["output"])
		tk.add(top, d1)
		# print("Disk area = "+str(top.area()))
		print(len(top.elements))
		self.assertTrue(len(top.elements)==2)
		self.assertTrue(abs(top.area()-31953.5046652) <= 1e-6)

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
		# print("MZI area = "+str(top.area()))
		print(len(top.elements))
		self.assertTrue(len(top.elements)==3)
		self.assertTrue(abs(top.area()-179518.918964) <= 1e-6)
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
		# print("DBR area = "+str(top.area()))
		print(len(top.elements))
		self.assertTrue(len(top.elements)==4)
		self.assertTrue(abs(top.area()-9095.25471349) <= 1e-6)

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

		# print("DC area = "+str(top.area()))
		print(len(top.elements))
		self.assertTrue(len(top.elements)==7)
		self.assertTrue(abs(top.area()-65615.8506033) <= 1e-6)

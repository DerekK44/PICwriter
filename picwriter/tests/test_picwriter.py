#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

import gdspy
# from picwriter.components.waveguide import Waveguide, WaveguideTemplate
from picwriter.components import *

""" Test case below not necessary, but should serve as framework for later """
class TestPICwriter(TestCase):
	def test_waveguide_creation(self):
		top = gdspy.Cell("t1")
		wgt = WaveguideTemplate(bend_radius=50, resist='+', fab="LIFTOFF")
		wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
		wg2=Waveguide([(0,0), (0,100), (-250, 100), (-250, -100)], wgt)
		top.add(wg1)
		top.add(wg2)
		# print("Waveguide area = "+str(top.area()))
		self.assertTrue(len(top.elements)==2)
		self.assertTrue(abs(top.area()-2828.31852764) <= 1e-6)

	def test_taper_creation(self):
		top = gdspy.Cell("t2")
		wgt = WaveguideTemplate(bend_radius=50, resist='+')
		wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
		top.add(wg1)
		tp1 = Taper(wgt, 100.0, 0.3, **wg1.portlist["input"])
		tp2 = Taper(wgt, 100.0, 0.0, **wg1.portlist["output"])
		top.add(tp1)
		top.add(tp2)
		# print("Taper area = "+str(top.area()))
		self.assertTrue(len(top.elements)==3)
		self.assertTrue(abs(top.area()-22141.5926399) <= 1e-6)

	def test_grating_coupler_creation(self):
		top = gdspy.Cell("t3")
		wgt = WaveguideTemplate(bend_radius=50, resist='+', fab='ETCH')
		wg1=Waveguide([(0,0), (250,0), (250,500), (500,500)], wgt)
		top.add(wg1)
		gc1 = GratingCouplerStraight(wgt, width=20, length=50, taper_length=20, period=1.0, dutycycle=0.7, **wg1.portlist["input"])
		top.add(gc1)
		gc2 = GratingCouplerFocusing(wgt, focus_distance=20.0, width=20, length=50, period=1.0, dutycycle=0.7, **wg1.portlist["output"])
		top.add(gc2)
		# print("Grating coupler area = "+str(top.area()))
		self.assertTrue(len(top.elements)==3)
		self.assertTrue(abs(top.area()-22562.0664901) <= 1e-6)

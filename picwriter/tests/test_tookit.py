#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

import gdspy
from picwriter.components.waveguide import Waveguide, WaveguideTemplate

""" Test case below not necessary, but should serve as framework for later """
class TestToolkit(TestCase):
	def test_cell_creation(self):
	    top = gdspy.Cell("top")
	    wgt = WaveguideTemplate(bend_radius=50, resist='+', fab="LIFTOFF")

	    wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
	    wg2=Waveguide([(0,0), (0,100), (-250, 100), (-250, -100)], wgt)

	    top.add(wg1)
	    top.add(wg2)

		#self.assertTrue(isinstance(c.name, basestring))

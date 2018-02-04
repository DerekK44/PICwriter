#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

import picwriter.toolkit as tk

""" Test case below not necessary, but should serve as framework for later """
class TestToolkit(TestCase):
	def test_cell_creation(self):
		c = tk.Cell("cell1")
		self.assertTrue(isinstance(c.name, basestring))

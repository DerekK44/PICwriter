#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import gdspy
import math
import heapq

class Cell:
    """
    Cell class for PICwriter toolkit that make it easier to manipulate for 
    photonics applications 
    (waveguide routing, management, etc.) 
        """
    def __init__(self, name):
        self.name = name #DELETE THIS LATER
        self.components = {}

#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import gdspy

"""
Set of helper functions that make it easier to manipulate
and work with gdspy subclasses defined in 'components' folder
"""

def get_angle(pt1, pt2):
    dx, dy = pt2[0]-pt1[0], pt2[1]-pt1[1]
    """ Uncomment below if we want to use real angles in the future
    and not just 90 degree bends
    if dx>0 and dy>0: #quadrant 1
        angle = np.arctan(dy/dx)
    elif dx<=0 and dy>0: #quadrant 2
        angle = 0.5*np.pi + np.arctan(-dx/dy)
    elif dx<0 and dy<=0: #quadrant 3
        angle = np.pi + np.arctan(dy/dx)
    else: #quadrant 4
        angle = 1.5*np.pi + np.arctan(-dx/dy)
    """
    if dx<=1e-6 and dy>0:
        angle=0.5*np.pi
    elif dy<=1e-6 and dx<0:
        angle=np.pi
    elif dx<=1e-6 and dy<0:
        angle=1.5*np.pi
    else:
        angle=0.0
    return angle

def dist(pt1, pt2):
    return np.sqrt((pt2[0]-pt1[0])**2 + (pt2[1]-pt1[1])**2)

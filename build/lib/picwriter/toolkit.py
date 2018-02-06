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
    if abs(dx)<=1e-6 and dy>0:
        angle=0.5*np.pi
    elif abs(dy)<=1e-6 and dx<0:
        angle=np.pi
    elif abs(dx)<=1e-6 and dy<0:
        angle=1.5*np.pi
    else:
        angle=0.0
    return angle

def dist(pt1, pt2):
    return np.sqrt((pt2[0]-pt1[0])**2 + (pt2[1]-pt1[1])**2)

def get_direction(pt1, pt2):
    """  Returns a cardinal direction:
        -NORTH, WEST, SOUTH, and EAST
        that corresponds to a cartesian point 'pt1' (tuple), pointing
        TOWARDS a second point pt2 """
    dx, dy = pt2[0]-pt1[0], pt2[1]-pt1[1]
    if abs(dx)<=1e-6 and dy>0:
        return "NORTH"
    elif abs(dy)<=1e-6 and dx<0:
        return "WEST"
    elif abs(dx)<=1e-6 and dy<0:
        return "SOUTH"
    else:
        return "EAST"

def flip_direction(direction):
    if direction=="NORTH": return "SOUTH"
    if direction=="SOUTH": return "NORTH"
    if direction=="WEST": return "EAST"
    if direction=="EAST": return "WEST"

def translate_point(pt, length, direction):
    if direction=="NORTH":
        return (pt[0], pt[1]+length)
    elif direction=="SOUTH":
        return (pt[0], pt[1]-length)
    elif direction=="WEST":
        return (pt[0]-length, pt[1])
    elif direction=="EAST":
        return (pt[0]+length, pt[1])

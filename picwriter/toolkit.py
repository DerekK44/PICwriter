# -*- coding: utf-8 -*-
"""
Set of helper functions that make it easier to manipulate
and work with gdspy subclasses defined in **components** miodule
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import gdspy

TOL=1e-6

def add(topcell, subcell, center=(0,0)):
    """ First creates a CellReference to subcell, then adds this to topcell at location center

        Args:
           * **topcell** (gdspy.Cell):  Cell to be added to
           * **subcell** (gdspy.Cell):  Cell being added

        Keyword Args:
           * **center** (tuple): center location for subcell to be added

        Returns:
           None

    """
    topcell.add(gdspy.CellReference(subcell, origin=center))

def get_keys(cell):
    """ Returns a list of the keys available in a portlist, such as 'input', 'output', 'top_output', etc.  Only works for picwriter components.

        Args:
           * **cell** (gdspy.Cell):  Cell from which to get get the portlist

        Returns:
           List of portlist keys corresponding to 'cell'.

    """
    return list(cell.portlist.keys())

def get_angle(pt1, pt2):
    """
    Given two cardinal points, returns the corresponding angle
    in *radians*.  Must be an integer multiple of pi/2.

    Args:
       * **pt1** (tuple):  Point 1
       * **pt2** (tuple):  Point 2

    Returns:
       float.  Angle (integer multiple of pi/2)

    Example::

        import picwriter.toolkit as tk
        print(tk.get_angle((0, 0), (0, 100)))

    The above prints 1.5707963267948966

    """
    dx, dy = pt2[0]-pt1[0], pt2[1]-pt1[1]
    if abs(dx)<=TOL and dy>0:
        angle=0.5*np.pi
    elif abs(dy)<=TOL and dx<0:
        angle=np.pi
    elif abs(dx)<=TOL and dy<0:
        angle=1.5*np.pi
    elif abs(dy)<=TOL and dx>0:
        angle=0.0
    else:
        raise ValueError("Warning! The angle between the two points must be an "
                         "integer multiples of 90deg from each other")
    return angle

def dist(pt1, pt2):
    """
    Given two cardinal points, returns the distance between the two.

    Args:
       * **pt1** (tuple):  Point 1
       * **pt2** (tuple):  Point 2

    Returns:
       float.  Distance

    Example::

        import picwriter.toolkit as tk
        print(tk.dist((0, 0), (100, 100)))

    The above prints 141.42135623730951

    """
    return np.sqrt((pt2[0]-pt1[0])**2 + (pt2[1]-pt1[1])**2)

def get_direction(pt1, pt2):
    """  Returns a cardinal direction (``'NORTH'``, ``'WEST'``, ``'SOUTH'``, and ``'EAST'``)
        that corresponds to a cartesian point `pt1 (tuple), pointing
        TOWARDS a second point `pt2`

        Args:
           * **pt1** (tuple):  Point 1
           * **pt2** (tuple):  Point 2

        Returns:
           string.  (``'NORTH'``, ``'WEST'``, ``'SOUTH'``, and ``'EAST'``)

        Example::

            import picwriter.toolkit as tk
            tk.get_direction((0,0), (-100,0))

        The above prints 'WEST'

    """
    dx, dy = pt2[0]-pt1[0], pt2[1]-pt1[1]
    if abs(dx)<=TOL and dy>0:
        return "NORTH"
    elif abs(dy)<=TOL and dx<0:
        return "WEST"
    elif abs(dx)<=TOL and dy<0:
        return "SOUTH"
    else:
        return "EAST"

def get_turn(dir1, dir2):
    """ Returns an angle (+pi/2 or -pi/2) corresponding to the CW or CCW
    turns that takes you from direction dir1 to dir2 """
    if (dir1=="NORTH" and dir2=="WEST") or (dir1=="WEST" and dir2=="SOUTH") or (dir1=="SOUTH" and dir2=="EAST") or (dir1=="EAST" and dir2=="NORTH"):
        return np.pi/2.0
    elif (dir1=="NORTH" and dir2=="EAST") or (dir1=="EAST" and dir2=="SOUTH") or (dir1=="SOUTH" and dir2=="WEST") or (dir1=="WEST" and dir2=="NORTH"):
        return -np.pi/2.0

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

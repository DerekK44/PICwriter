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
    topcell.add(gdspy.CellReference(subcell, origin=center))

def get_keys(subcell):
    return list(subcell.portlist.keys())

def get_angle(pt1, pt2):
    """
    Given two cardinal points, returns the corresponding angle
    in *radians*.  Must be an integer multiple of pi/2.

    Args:
       **pt1** (tuple):  Point 1

       **pt2** (tuple):  Point 2

    Returns:
       float.  Angle (integer multiple of pi/2)

    Example::

        import picwriter.toolkit as tk
        print(tk.get_angle((0, 0), (0, 100)))
        >> 1.5707963267948966

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
       **pt1** (tuple):  Point 1

       **pt2** (tuple):  Point 2

    Returns:
       float.  Distance

    Example::

        import picwriter.toolkit as tk
        print(tk.dist((0, 0), (100, 100)))
        >> 141.42135623730951

    """
    return np.sqrt((pt2[0]-pt1[0])**2 + (pt2[1]-pt1[1])**2)

def get_direction(pt1, pt2):
    """  Returns a cardinal direction (``'NORTH'``, ``'WEST'``, ``'SOUTH'``, and ``'EAST'``)
        that corresponds to a cartesian point `pt1 (tuple), pointing
        TOWARDS a second point `pt2`

        Args:
           **pt1** (tuple):  Point 1

           **pt2** (tuple):  Point 2

        Returns:
           string.  (``'NORTH'``, ``'WEST'``, ``'SOUTH'``, and ``'EAST'``)

        Example::

            import picwriter.toolkit as tk
            tk.get_direction((0,0), (-100,0))
            >> 'WEST'

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

# def rotate_direction(dir1, angle):
#     if not (abs(angle%(np.pi/2.0))<=TOL):
#         raise ValueError("Warning! Angle for 'rotate_direction()' must be an integer multiple of pi/2")
#     angle = angle%(2*np.pi) #Make angle either 0, 0.5pi, pi, or 1.5pi
#     if (dir1=="NORTH" and abs(angle-0.0)<=TOL) or (dir1=="EAST" and abs(angle-np.pi/2.0)<=TOL) or (dir1=="SOUTH" and abs(angle-np.pi)<=TOL) or (dir1=="WEST" and abs(angle-1.5*np.pi)<=TOL):
#         return "NORTH"
#     elif (dir1=="WEST" and abs(angle-0.0)<=TOL) or (dir1=="NORTH" and abs(angle-np.pi/2.0)<=TOL) or (dir1=="EAST" and abs(angle-np.pi)<=TOL) or (dir1=="SOUTH" and abs(angle-1.5*np.pi)<=TOL):
#         return "WEST"
#     elif (dir1=="SOUTH" and abs(angle-0.0)<=TOL) or (dir1=="WEST" and abs(angle-np.pi/2.0)<=TOL) or (dir1=="NORTH" and abs(angle-np.pi)<=TOL) or (dir1=="EAST" and abs(angle-1.5*np.pi)<=TOL):
#         return "SOUTH"
#     elif (dir1=="EAST" and abs(angle-0.0)<=TOL) or (dir1=="SOUTH" and abs(angle-np.pi/2.0)<=TOL) or (dir1=="WEST" and abs(angle-np.pi)<=TOL) or (dir1=="NORTH" and abs(angle-1.5*np.pi)<=TOL):
#         return "EAST"
#     else:
#         raise ValueError("No case found for rotate_direction()")

# def get_portlist(subclass, center, rotation=0):
#     """ Preferred over just grabbing a cell portlist, since this
#     version rotates the position & direction as specified
#     **ONLY WORKS** FOR 90degree turns!
#     angle MUST be in radians"""
#     if not (abs(rotation%(np.pi/2.0))<=TOL):
#         raise ValueError("Warning! Rotation angle for 'rotate()' must be an integer multiple of pi/2")
#     newportlist={}
#     for key in list(subclass.portlist.keys()):
#         newportlist[key] = {}
#         port = subclass.portlist[key]["port"]
#         direction = subclass.portlist[key]["direction"]
#         newportlist[key]['direction']= rotate_direction(direction, rotation)
#         v=np.array([[port[0]-center[0]], [port[1]-center[1]]])
#         c, s = np.cos(rotation), np.sin(rotation)
#         R = np.array([[c, -s],
#                       [s, c]])
#         vn = np.dot(R,v)
#         newportlist[key]['port'] = (float(vn[0]+center[0]), float(vn[1]+center[1]))
#     return newportlist

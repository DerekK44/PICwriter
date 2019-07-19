# -*- coding: utf-8 -*-
"""
Set of helper functions that make it easier to manipulate
and work with gdspy subclasses defined in **components** module
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import math
import gdspy

TOL=1e-6
CURRENT_CELLS = {}
CURRENT_CELL_NAMES = {}

def add(top_cell, component_cell, center=(0,0), x_reflection=False):
    """ First creates a CellReference to subcell, then adds this to topcell at location center.

        Args:
           * **top_cell** (gdspy.Cell):  Cell being added to
           * **component_cell** (gdspy.Cell):  Cell of the component being added

        Keyword Args:
           * **port** (tuple): location for the subcell to be added
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to 'EAST' (zero degrees of rotation).

        Returns:
           None
    """
    
    if isinstance(component_cell, gdspy.Cell):
        top_cell.add(gdspy.CellReference(component_cell, 
                                         origin = center,
                                         x_reflection=x_reflection))
    elif isinstance(component_cell, Component):
        component_cell.addto(top_cell)
    
def getCellName(name):
    global CURRENT_CELL_NAMES
    if name not in CURRENT_CELL_NAMES.keys():
        CURRENT_CELL_NAMES[name] = 1
    else:
        CURRENT_CELL_NAMES[name] += 1
    return str(name)+"_"+str(CURRENT_CELL_NAMES[name])

def build_mask(cell, wgt, final_layer=None, final_datatype=None):
    """ Builds the appropriate mask according to the resist specifications and fabrication type.  Does this by applying a boolean 'XOR' or 'AND' operation on the waveguide and clad masks.

        Args:
           * **cell** (gdspy.Cell):  Cell with components.  Final mask is placed in this cell.
           * **wgt** (WaveguideTemplate):  Waveguide template containing the resist information, and layers/datatypes for the waveguides and cladding.

        Keyword Args:
           * **final_layer** (int): layer to place the mask on (defaults to `wgt.clad_layer + 1`)
           * **final_datatype** (int): datatype to place the mask on (defaults to `0`)

        Returns:
           None

    """
    fl = wgt.clad_layer+1 if final_layer==None else final_layer
    fd = 0 if final_datatype==None else final_datatype

    polygons = cell.get_polygons(by_spec=True)
    try:
        pWG = polygons[(wgt.wg_layer, wgt.wg_datatype)]
        pCLAD = polygons[(wgt.clad_layer, wgt.clad_datatype)]
    except KeyError:
        print("Warning! No objects written to layer/datatype specified by WaveguideTemplate")
    if wgt.resist=='+':
        cell.add(gdspy.fast_boolean(pWG, pCLAD, 'xor', precision=0.001, max_points=199, layer=fl, datatype=fd))
    elif wgt.resist=='-':
        cell.add(gdspy.fast_boolean(pWG, pCLAD, 'and', precision=0.001, max_points=199, layer=fl, datatype=fd))

def get_trace_length(trace, wgt):
    """ Returns the total length of a curved waveguide trace.

    Args:
       * **trace** (list): tracelist of (x,y) points all specifying 90 degree angles.
       * **wgt** (WaveguideTemplate): template for the waveguide, the bend_radius of which is used to compute the length of the curved section.

    Returns:
       float corresponding to the length of the waveguide trace

    """
    length = 0.0
    dbr = 2*wgt.bend_radius - 0.5*np.pi*wgt.bend_radius
    for i in range(len(trace)-1):
        pt2, pt1 = trace[i+1], trace[i]
        length += np.sqrt((pt2[0]-pt1[0])**2 + (pt2[1]-pt1[1])**2)
    length = length - (dbr*(len(trace)-1))
    return length

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
       float  Angle (integer multiple of pi/2)

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

def get_exact_angle(pt1, pt2):
    """
    Given two cardinal points, returns the corresponding angle
    in *radians*.

    Args:
       * **pt1** (tuple):  Point 1
       * **pt2** (tuple):  Point 2

    Returns:
       float  Angle (in radians)

    Example::

        import picwriter.toolkit as tk
        print(tk.get_angle((0, 0), (100, 100)))

    The above prints 0.785398163

    """
    dx, dy = pt2[0]-pt1[0], pt2[1]-pt1[1]
    return math.atan2(dy,dx)

def dist(pt1, pt2):
    """
    Given two cardinal points, returns the distance between the two.

    Args:
       * **pt1** (tuple):  Point 1
       * **pt2** (tuple):  Point 2

    Returns:
       float  Distance

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
           string  (``'NORTH'``, ``'WEST'``, ``'SOUTH'``, and ``'EAST'``)

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
    """  Returns an angle (+pi/2 or -pi/2) corresponding to the CW or CCW turns that takes you from direction `dir1` to `dir2`, where each direction is either ``'NORTH'``, ``'WEST'``, ``'SOUTH'``, or ``'EAST'``

        Args:
           * **dir1** (direction):  Point 1
           * **pt2** (tuple):  Point 2

        Returns:
           float  (+pi/2 or -pi/2)

    """
    if (dir1=="NORTH" and dir2=="WEST") or (dir1=="WEST" and dir2=="SOUTH") or (dir1=="SOUTH" and dir2=="EAST") or (dir1=="EAST" and dir2=="NORTH"):
        return np.pi/2.0
    elif (dir1=="NORTH" and dir2=="EAST") or (dir1=="EAST" and dir2=="SOUTH") or (dir1=="SOUTH" and dir2=="WEST") or (dir1=="WEST" and dir2=="NORTH"):
        return -np.pi/2.0

def flip_direction(direction):
    """  Returns the opposite of `direction`, where each direction is either ``'NORTH'``, ``'WEST'``, ``'SOUTH'``, or ``'EAST'``

        Args:
           * **direction** (direction):  Direction to be flipped
           * **pt2** (tuple):  Point 2

        Returns:
           direction (``'NORTH'``, ``'WEST'``, ``'SOUTH'``, or ``'EAST'``)

    """
    if direction=="NORTH": return "SOUTH"
    if direction=="SOUTH": return "NORTH"
    if direction=="WEST": return "EAST"
    if direction=="EAST": return "WEST"
    elif isinstance(direction, float):
        return (direction + np.pi)%(2*np.pi)

def translate_point(pt, length, direction, height=0.0):
    """  Returns the point (tuple) corresponding to `pt` translated by distance `length` in direction `direction` where each direction is either ``'NORTH'``, ``'WEST'``, ``'SOUTH'``, or ``'EAST'``

        Args:
           * **pt** (tuple):  Starting point
           * **length** (float): Distance to move in *direction*
           * **direction** (direction):  Direction to move in
           
        Keyword Args:
           * **height** (float):  Distance to move perpendicular to *direction*.  Defaults to 0.

        Returns:
           point, tuple (x, y)

    """
    if isinstance(direction,float):
        # direction is a float (in radians)
        return (pt[0]+length*np.cos(direction)-height*np.sin(direction), pt[1]+length*np.sin(direction)+height*np.cos(direction))
    elif str(direction)=="NORTH":
        return (pt[0]-height, pt[1]+length)
    elif str(direction)=="SOUTH":
        return (pt[0]+height, pt[1]-length)
    elif str(direction)=="WEST":
        return (pt[0]-length, pt[1]-height)
    elif str(direction)=="EAST":
        return (pt[0]+length, pt[1]+height)

def normalize_angle(angle):
    """  Returns the angle (in radians) between -pi and +pi that corresponds to the input angle

        Args:
           * **angle** (float):  Angle to normalize

        Returns:
           float  Angle

    """
    angle = angle % (2*np.pi)
    if angle > np.pi:
        angle -= 2*np.pi
    return angle
    
def get_curve_length(func, start, end, grid=0.001):
    """  Returns the length (in microns) of a curve defined by the function `func` on the interval [start, end]

        Args:
           * **func** (function):  Function that takes a single (floating point) argument, and returns a (x,y) tuple.
           * **start** (float):  Starting value (argument passed to `func`).
           * **end** (float):  Ending value (argument passed to `func`).
           
        Keyword Args:
           * **grid** (float):  Grid resolution used to determine when curve length has converged.  Defaults to 0.001.

        Returns:
           float  Length

    """
    def get_cur_length(pt_list):
        # list of tuples [(x1,y1), (x2,y2), ...]
        length=0
        for i in range(len(pt_list)-1):
            pt1, pt2 = pt_list[i], pt_list[i+1]
            length += np.sqrt((pt2[1]-pt1[1])**2 + (pt2[0]-pt1[0])**2)
        return length
    
    num_pts = 2 # start with 2 points
    error = 2*grid  #start high
    pts = [func(i) for i in np.linspace(start, end, num_pts)]
    prev_length = get_cur_length(pts)
    
    while error > grid: #Don't exit loop until length has converged
        print("num_pts = "+str(num_pts))
        print("prev_length = "+str(prev_length))
        num_pts = num_pts*2 # Increase pt resolution exponentially
        pts = [func(i) for i in np.linspace(start, end, num_pts)]
        cur_length = get_cur_length(pts)
        error = abs(cur_length - prev_length)
        prev_length = cur_length
       
    print("num_pts = "+str(num_pts))
    print("Final length! = "+str(prev_length))
    return cur_length
    
def build_waveguide_polygon(func, wg_width, start_direction, end_direction, start_val=0, end_val=1, grid=0.001):
    """
        Args:
           * **func** (function):  Function that takes a single (floating point) argument, and returns a (x,y) tuple.
           * **wg_width** (float):  Waveguide width
           * **num_pts** (int):  Number of points that make up the waveguide path
           * **start_direction** (float):  Starting direction of the path, in *radians*.
           * **end_direction** (float):  End direction of the path, in *radians*.
           
        Keyword Args:
           * **start_val** (float):  Starting value (argument passed to `func`).  Defaults to 0.
           * **end_val** (float):  Ending value (argument passed to `func`).  Defaults to 1.
           * **grid** (float): Grid resolution used to determine when curve length has converged.  Guarantees that polygon formed by the points results in no more than a grid/2.0 error from the true position.  Defaults to 0.001

        Returns:
           Two lists, one for each edge of the waveguide.
    
    """
    def get_path_points(func, wg_width, num_pts, start_direction, end_direction, start_val=0, end_val=1):
        poly_list1, poly_list2 = [], []

        center_pts = [func(i) for i in np.linspace(start_val, end_val, num_pts)]
        
        # Add the first points
        angle = (start_direction + np.pi/2.0)%(2*np.pi)
        poly_list1.append((center_pts[0][0] + (wg_width/2.0)*np.cos(angle), center_pts[0][1] + (wg_width/2.0)*np.sin(angle)))
        angle = (start_direction - np.pi/2.0)%(2*np.pi)
        poly_list2.append((center_pts[0][0] + (wg_width/2.0)*np.cos(angle), center_pts[0][1] + (wg_width/2.0)*np.sin(angle)))
        
        for i in range(len(center_pts)-2): #compute the derivative for the points (except first & last points)
            prev_pt, cur_pt, next_pt = center_pts[i], center_pts[i+1], center_pts[i+2]
            d1, d2 = np.arctan2((cur_pt[1]-prev_pt[1]), (cur_pt[0]-prev_pt[0]))%(2*np.pi), np.arctan2((next_pt[1]-cur_pt[1]), (next_pt[0]-cur_pt[0]))%(2*np.pi)
            
            
            angle = ((d1+d2)/2.0 + np.pi/2.0)%(2*np.pi)
            poly_list1.append((cur_pt[0] + (wg_width/2.0)*np.cos(angle), cur_pt[1] + (wg_width/2.0)*np.sin(angle)))
            angle = ((d1+d2)/2.0 - np.pi/2.0)%(2*np.pi)
            poly_list2.append((cur_pt[0] + (wg_width/2.0)*np.cos(angle), cur_pt[1] + (wg_width/2.0)*np.sin(angle)))
            
        # Now add the final points
        angle = (end_direction + np.pi + np.pi/2.0)%(2*np.pi) # Add an extra pi because end_direction points in the opposite way by convention (points 'into' the path)
        poly_list1.append((center_pts[-1][0] + (wg_width/2.0)*np.cos(angle), center_pts[-1][1] + (wg_width/2.0)*np.sin(angle)))
        angle = (end_direction + np.pi - np.pi/2.0)%(2*np.pi)
        poly_list2.append((center_pts[-1][0] + (wg_width/2.0)*np.cos(angle), center_pts[-1][1] + (wg_width/2.0)*np.sin(angle)))
        
        return (poly_list1, poly_list2)

    def check_path(path, grid):
        """ Determines if a path has sufficiently low grid error (and if so, returns True, else False).
        Does this by iterating through the points, and computing the area of the triangle formed by any
        3 consecutive points on path.  If this area, divided by the length between the first & last point, is greater than 0.5*grid,
        then the the error is too large!
        """
        for i in range(len(path)-2):
            pt1, pt2, pt3 = path[i], path[i+1], path[i+2]
            area = abs((pt1[0]*(pt2[1]-pt3[1]) + pt2[0]*(pt3[1]-pt1[1]) + pt3[0]*(pt1[1]-pt2[1]))/2.0)
            length = np.sqrt((pt3[1] - pt1[1])**2 + (pt3[0] - pt1[0])**2)
            if area/length > 0.5*grid:
                return False
        # If none of the segments give a large grid error, return True
        return True
        
    num_pts = 16 # start with 4, increase by a factor of 2 each time
    isPathOK = False
    firstIter = True
    cur_path1, cur_path2 = [], []
    
    while isPathOK==False:
        if not firstIter: # do this all the other times (except first time)
            prev_path1, prev_path2 = cur_path1, cur_path2
        
        cur_path1, cur_path2 = get_path_points(func, wg_width, num_pts, start_direction, end_direction, start_val=start_val, end_val=end_val)
        if firstIter: # do this once (initialize prev_paths)
            prev_path1, prev_path2 = cur_path1, cur_path2
            firstIter=False
            
        isPathOK = check_path(cur_path1, grid) and check_path(cur_path2, grid) # returns False if either is False
        num_pts = num_pts*2
        
    # Now the two paths are of sufficiently high resolution.  Return the sum list of points.
    path_points = prev_path1 + prev_path2[::-1]
    return path_points
    
class Component():
    """ Super class for all objects created in PICwriter.  This class handles rotations, naming, etc. for all components,
        so that writing python code for new cells requires less overhead.  Component is a wrapper around gdspy Cell objects.

        Args:
           * **name** (string):  The name prefix to be used for these 

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6.

    """
    
    def __init__(self, name, *args):
        self.name_prefix = name
        
        # Add default values below.
        self.portlist = {}
        self.port = (0,0)
        self.direction = 0.0
        
        self._hash_cell_(args[0])
        
    def _auto_transform_(self):
        """ 
        Go through all the ports and do the appropriate 
        rotations and translations corresponding to the specified 'port' and 'direction'
        """
        for key in self.portlist.keys():
            cur_port = self.portlist[key]['port']
            
            if self.direction=="EAST": #direction of the input port (which specifies whole component orientation)
                angle = 0.0
            elif self.direction=="NORTH":
                angle = np.pi/2.0
            elif self.direction=="WEST":
                angle = np.pi
            elif self.direction=="SOUTH":
                angle = 3*np.pi/2.0
            elif isinstance(self.direction, float) or isinstance(self.direction, int):
                angle=float(self.direction)
            dx = cur_port[0]*np.cos(angle) - cur_port[1]*np.sin(angle)
            dy = cur_port[0]*np.sin(angle) + cur_port[1]*np.cos(angle)
            
            self.portlist[key]['port'] = (self.port[0] + dx,
                                          self.port[1] + dy)
            
    def _hash_cell_(self, *args):
        """ Check to see if the same exact cell has been created already (with the same parameters).
        If not, add the cell to the global CURRENT_CELLS dictionary.
        If so, point to the identical cell in the CURRENT_CELLS dictionary.
        """
        dont_hash = ['port', 'direction', 'self'] #list of keys not to be hashed
        args = args[0]
        new_args = []
        for k in args.keys():
            if k not in dont_hash:
                try:
                    if ("WaveguideTemplate" in args[k].name) or ("MetalTemplate" in args[k].name):
                        new_args.append(args[k].name) # WaveguideTemplates each have a unique name
                except:
                    new_args.append(args[k])

        global CURRENT_CELLS
        properties = self.name_prefix+''.join([str(p) for p in new_args])
        self.cell_hash = properties
        if self.cell_hash not in CURRENT_CELLS.keys():
            #Create the cell if it does not exist anywhere else
            CURRENT_CELLS[self.cell_hash] = gdspy.Cell(getCellName(self.name_prefix))
            self.first_cell = True
        else:
            self.first_cell = False

        # Now delete the cell completely to save memory (since this info is now stored globally in CURRENT_CELLS)
#        del self.cell
        
    def __get_cell(self):
        return CURRENT_CELLS[self.cell_hash]

    def __direction_to_rotation(self, direction):
        # Returns a rotation (in degrees) given a 'direction' which can be a cardinal direction or an angle in radians
        if isinstance(direction,float):
            # direction is a float in radians, but rotation should be a float in degrees
            return direction*180.0/np.pi
        elif str(direction)=="EAST":
            return 0.0
        elif str(direction)=="NORTH":
            return 90.0
        elif str(direction)=="WEST":
            return 180.0
        elif str(direction)=="SOUTH":
            return 270.0

    def add(self, element, origin=(0,0), rotation=0.0, x_reflection=False):
        """ Add a reference to an element or list of elements to the cell associated with this component """
        this_cell = CURRENT_CELLS[self.cell_hash]
        
        if self.first_cell == True:
            """ Only add elements if this is the first cell made. 
            Otherwise, duplicate elements will be added 
            """
            if isinstance(element, Component):
                element_cell = CURRENT_CELLS[element.cell_hash]
                rot = self.__direction_to_rotation(element.direction)
                this_cell.add(gdspy.CellReference(element_cell, 
                                                  origin=element.port, 
                                                  rotation=rot, 
                                                  x_reflection=x_reflection))
            elif isinstance(element, gdspy.Cell):
                this_cell.add(gdspy.CellReference(element, origin=origin, rotation=rotation, x_reflection=x_reflection))
            else:
                this_cell.add(element)

    def addto(self, top_cell, x_reflection=False):
        
        rot = self.__direction_to_rotation(self.direction)
            
        if isinstance(top_cell, gdspy.Cell):
            top_cell.add(gdspy.CellReference(CURRENT_CELLS[self.cell_hash], 
                                             origin=self.port, 
                                             rotation=rot, 
                                             x_reflection=x_reflection))
            
        elif isinstance(top_cell, Component):
            tc = CURRENT_CELLS[top_cell.cell_hash]
            tc.add(gdspy.CellReference(CURRENT_CELLS[self.cell_hash], 
                                                     origin=self.port, 
                                                     rotation=rot, 
                                                     x_reflection=x_reflection))
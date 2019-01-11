# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class MetalTemplate:
    """ Template for electrical wires that contains some standard information about the fabrication process and metal wire.

        Keyword Args:
           * **bend_radius** (float): Radius of curvature for bends in the metal route.  Defaults to zero.
           * **width** (float): Width of the metal route as shown on the mask.  Defaults to 20.
           * **clad_width** (float): Width of the cladding (region next to route, mainly used for positive-type photoresists + etching, or negative-type and liftoff).  Defaults to 20.
           * **resist** (string): Must be either '+' or '-'.  Specifies the type of photoresist used.  Defaults to `'+'`.
           * **fab** (string): If 'ETCH', then keeps resist as is, otherwise changes it from '+' to '-' (or vice versa).  This is mainly used to reverse the type of mask used if the fabrication type is 'LIFTOFF'.  Defaults to `'ETCH'`.
           * **metal_layer** (int): Layer type used for metal route.  Defaults to 11.
           * **metal_datatype** (int): Data type used for metal route.  Defaults to 0.
           * **clad_layer** (int): Layer type used for cladding.  Defaults to 12.
           * **clad_datatype** (int): Data type used for cladding.  Defaults to 0.

    """
    def __init__(self, bend_radius=0, width=20.0, clad_width=20.0,
                 resist='+', fab='ETCH', metal_layer=11, metal_datatype=0, clad_layer=12, clad_datatype=0):
        self.width = width
        self.bend_radius = bend_radius
        self.clad_width = clad_width
        if resist != '+' and resist != '-':
            raise ValueError("Warning, invalid input for type resist in "
                             "MetalTemplate")
        if fab=='ETCH':
            self.resist = resist #default state assumes 'etching'
        else: #reverse resist type if liftoff or something else
            self.resist = '+' if resist=='-' else '-'

        self.metal_layer = metal_layer
        self.metal_datatype = metal_datatype
        self.clad_layer = clad_layer
        self.clad_datatype = clad_datatype

class MetalRoute(gdspy.Cell):
    """ Standard MetalRoute Cell class (subclass of gdspy.Cell).

        Args:
           * **trace** (list):  List of coordinates used to generate the route (such as '[(x1,y1), (x2,y2), ...]').  For now, all trace points must specify 90 degree turns.
           * **mt** (MetalTemplate):  MetalTemplate object

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) are the first elements of 'trace', (x2, y2) are the last elements of 'trace', and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.

    """
    def __init__(self, trace, mt):
        gdspy.Cell.__init__(self,"MetalRoute--"+str(uuid.uuid4()))

        self.portlist = {}

        self.trace = trace
        self.mt = mt
        self.resist = mt.resist
        self.bend_radius = mt.bend_radius
        self.spec = {'layer': mt.metal_layer, 'datatype': mt.metal_datatype}
        self.clad_spec = {'layer': mt.clad_layer, 'datatype': mt.clad_datatype} #Used for 'xor' operation

        self.type_check_trace()
        self.build_cell()
        self.build_ports()

    def type_check_trace(self):
        trace = []
        """ Round each trace value to the nearest 1e-6 -- prevents
        some typechecking errors
        """
        for t in self.trace:
            trace.append((round(t[0], 6), round(t[1], 5)))
        self.trace = trace

        """ Make sure that each waypoint is spaced > 2*bend_radius apart
        as a conservative estimate ¯\_(ツ)_/¯
        Make sure all waypoints specify 90degree angles.  This might be
        updated in the future to allow for 45deg, or arbitrary bends
        """
        prev_dx, prev_dy = 1,1 #initialize to safe value
        for i in range(len(self.trace)-1):
            dx = abs(self.trace[i+1][0]-self.trace[i][0])+1E-10
            dy = abs(self.trace[i+1][1]-self.trace[i][1])+1E-10
            if (dx < 2*self.mt.bend_radius and dy < 2*self.mt.bend_radius) and (i != 0) and (i!=len(self.trace)-2) and (self.bend_radius != 0):
                raise ValueError("Warning!  All waypoints *must* be greater than "
                                 "two bend radii apart.")
            if ((i == 0) or (i==len(self.trace)-2)) and (dx < self.mt.bend_radius and dy < self.mt.bend_radius) and (self.bend_radius != 0):
                raise ValueError("Warning! Start and end waypoints *must be greater "
                                 "than one bend radius apart.")
            if dx>=1e-6 and dy>=1e-6:
                raise ValueError("Warning! All waypoints *must* specify turns "
                                 "that are 90degrees")
            if ((prev_dx <= 1e-6 and dx<=1e-6) or (prev_dy <= 1e-6 and dy<=1e-6)):
                raise ValueError("Warning! Unnecessary waypoint specified.  All"
                                 " waypoints must specify a valid 90deg bend")
            prev_dx, prev_dy = dx, dy

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        br = self.mt.bend_radius

        path = gdspy.Path(self.mt.width, self.trace[0])
        path2 = gdspy.Path(self.mt.width+2*self.mt.clad_width, self.trace[0])

        prior_direction = tk.get_direction(self.trace[0], self.trace[1])

        if br != 0:
            """ Path routing for curved bends.  Same as in waveguide class. """
            path.segment(tk.dist(self.trace[0], self.trace[1])-br,
                         direction=tk.get_angle(self.trace[0], self.trace[1]),
                         **self.spec)
            path2.segment(tk.dist(self.trace[0], self.trace[1])-br,
                         direction=tk.get_angle(self.trace[0], self.trace[1]),
                         **self.clad_spec)
            for i in range(len(self.trace)-2):
                direction = tk.get_direction(self.trace[i+1], self.trace[i+2])
                turn = tk.get_turn(prior_direction, direction)
                path.turn(br, turn, number_of_points=0.1, **self.spec)
                path2.turn(br, turn, number_of_points=0.1, **self.clad_spec)
                if tk.dist(self.trace[i+1], self.trace[i+2])-2*br > 0: #ONLY False for last points if spaced br < distance < 2br
                    path.segment(tk.dist(self.trace[i+1], self.trace[i+2])-2*br, **self.spec)
                    path2.segment(tk.dist(self.trace[i+1], self.trace[i+2])-2*br, **self.clad_spec)
                prior_direction = direction
            if tk.dist(self.trace[-2],self.trace[-1]) < 2*br:
                path.segment(tk.dist(self.trace[-2],self.trace[-1])-br, **self.spec)
                path2.segment(tk.dist(self.trace[-2],self.trace[-1])-br, **self.clad_spec)
            else:
                path.segment(br, **self.spec)
                path2.segment(br, **self.clad_spec)

            if len(self.trace)==2 and tk.dist(self.trace[1], self.trace[0])<=self.mt.bend_radius:
                path = gdspy.Path(self.mt.width, self.trace[0])
                path.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_angle(self.trace[0], self.trace[1]), **self.spec)
                path2 = gdspy.Path(self.mt.width+2*self.mt.clad_width, self.trace[0])
                path2.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_angle(self.trace[0], self.trace[1]), **self.clad_spec)
        elif br == 0:
            """ Do path routing for sharp 90 degree trace bends """
            path.segment(tk.dist(self.trace[0], self.trace[1]),
                         direction=tk.get_angle(self.trace[0], self.trace[1]),
                         **self.spec)
            path2.segment(tk.dist(self.trace[0], self.trace[1]),
                         direction=tk.get_angle(self.trace[0], self.trace[1]),
                         **self.clad_spec)
            for i in range(len(self.trace)-2):
                """ Add a square to fill in the corner """
                self.add(gdspy.Rectangle((self.trace[i+1][0]-self.mt.width/2.0, self.trace[i+1][1]-self.mt.width/2.0),
                                         (self.trace[i+1][0]+self.mt.width/2.0, self.trace[i+1][1]+self.mt.width/2.0), **self.spec))
                self.add(gdspy.Rectangle((self.trace[i+1][0]-self.mt.width/2.0-self.mt.clad_width, self.trace[i+1][1]-self.mt.width/2.0-self.mt.clad_width),
                                         (self.trace[i+1][0]+self.mt.width/2.0+self.mt.clad_width, self.trace[i+1][1]+self.mt.width/2.0+self.mt.clad_width), **self.clad_spec))
                angle = tk.get_angle(self.trace[i+1], self.trace[i+2])
                path.segment(tk.dist(self.trace[i+1], self.trace[i+2]), direction=angle, **self.spec)
                path2.segment(tk.dist(self.trace[i+1], self.trace[i+2]), direction=angle, **self.clad_spec)

        """ Extra padding """
        if tk.get_direction(self.trace[0], self.trace[1])=='EAST' or tk.get_direction(self.trace[0], self.trace[1])=='WEST':
            pad_ll = (self.trace[0][0]-self.mt.clad_width, self.trace[0][1]-self.mt.width/2.0-self.mt.clad_width)
            pad_ul = (self.trace[0][0]+self.mt.clad_width, self.trace[0][1]+self.mt.width/2.0+self.mt.clad_width)
        else:
            pad_ll = (self.trace[0][0]-self.mt.width/2.0-self.mt.clad_width, self.trace[0][1]-self.mt.clad_width)
            pad_ul = (self.trace[0][0]+self.mt.width/2.0+self.mt.clad_width, self.trace[0][1]+self.mt.clad_width)
        self.add(gdspy.Rectangle(pad_ll, pad_ul, **self.clad_spec))

        if tk.get_direction(self.trace[-2], self.trace[-1])=='EAST' or tk.get_direction(self.trace[-2], self.trace[-1])=='WEST':
            pad_ll = (self.trace[-1][0]-self.mt.clad_width, self.trace[-1][1]-self.mt.width/2.0-self.mt.clad_width)
            pad_ul = (self.trace[-1][0]+self.mt.clad_width, self.trace[-1][1]+self.mt.width/2.0+self.mt.clad_width)
        else:
            pad_ll = (self.trace[-1][0]-self.mt.width/2.0-self.mt.clad_width, self.trace[-1][1]-self.mt.clad_width)
            pad_ul = (self.trace[-1][0]+self.mt.width/2.0+self.mt.clad_width, self.trace[-1][1]+self.mt.clad_width)
        self.add(gdspy.Rectangle(pad_ll, pad_ul, **self.clad_spec))

        self.add(path)
        self.add(path2)

    def build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':(self.trace[0][0], self.trace[0][1]),
                                  'direction': tk.get_direction(self.trace[1], self.trace[0])}
        self.portlist["output"] = {'port':(self.trace[-1][0], self.trace[-1][1]),
                                   'direction':tk.get_direction(self.trace[-2], self.trace[-1])}

class Bondpad(gdspy.Cell):
    """ Standard Bondpad Cell class (subclass of gdspy.Cell).

        Args:
           * **mt** (MetalTemplate):  WaveguideTemplate object

        Keyword Args:
           * **length** (float): Length of the bondpad.  Defaults to 150
           * **width** (float): Width of the bondpad.  Defaults to 100
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the taper will point *towards*, must be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.  Defaults to `'EAST'`.

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['output'] = {'port': (x1, y1), 'direction': 'dir'}

        Where in the above (x1,y1) is the same as the 'port' input, and 'dir' is the same as 'direction' input of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.

    """
    def __init__(self, mt, length=150, width=100, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "Bondpad--"+str(uuid.uuid4()))

        self.portlist = {}

        self.length = length
        self.width = width
        self.port = port
        self.direction = direction
        self.mt = mt

        self.spec = {'layer': mt.metal_layer, 'datatype': mt.metal_datatype}
        self.clad_spec = {'layer': mt.clad_layer, 'datatype': mt.clad_datatype}

        self.build_cell()
        self.build_ports()

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        w, l, c = self.width, self.length, self.mt.clad_width
        if self.direction=="EAST":
            self.add(gdspy.Rectangle((self.port[0], self.port[1]-w/2.0), (self.port[0]+l, self.port[1]+w/2.0), **self.spec))
            self.add(gdspy.Rectangle((self.port[0]-c, self.port[1]-w/2.0-c), (self.port[0]+l+c, self.port[1]+w/2.0+c), **self.clad_spec))
        elif self.direction=="NORTH":
            self.add(gdspy.Rectangle((self.port[0]-w/2.0, self.port[1]), (self.port[0]+w/2.0, self.port[1]+l), **self.spec))
            self.add(gdspy.Rectangle((self.port[0]-w/2.0-c, self.port[1]-c), (self.port[0]+w/2.0+c, self.port[1]+l+c), **self.clad_spec))
        elif self.direction=="WEST":
            self.add(gdspy.Rectangle((self.port[0], self.port[1]-w/2.0), (self.port[0]-l, self.port[1]+w/2.0), **self.spec))
            self.add(gdspy.Rectangle((self.port[0]+c, self.port[1]-w/2.0-c), (self.port[0]-l-c, self.port[1]+w/2.0+c), **self.clad_spec))
        elif self.direction=="SOUTH":
            self.add(gdspy.Rectangle((self.port[0]-w/2.0, self.port[1]), (self.port[0]+w/2.0, self.port[1]-l), **self.spec))
            self.add(gdspy.Rectangle((self.port[0]-w/2.0-c, self.port[1]+c), (self.port[0]+w/2.0+c, self.port[1]-l-c), **self.clad_spec))

    def build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["output"] = {'port':self.port, 'direction':self.direction}

if __name__ == "__main__":
    top = gdspy.Cell("top")
    mt = MetalTemplate(bend_radius=0, resist='+', fab="ETCH")

    mt1=MetalRoute([(0,0), (0,250), (100,250), (100,500), (400,500)], mt)

    bp1 = Bondpad(mt, **mt1.portlist["output"])
    bp2 = Bondpad(mt, **mt1.portlist["input"])
    tk.add(top, bp1)
    tk.add(top, bp2)
    tk.add(top, mt1)

    # gdspy.LayoutViewer()
    gdspy.write_gds('metal.gds', unit=1.0e-6, precision=1.0e-9)

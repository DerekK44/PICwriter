# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class WaveguideTemplate:
    """ Standard template for waveguides (as well as other structures) that contains some standard information about the fabrication process and waveguides.

        Keyword Args:
           * **bend_radius** (float): Radius of curvature for waveguide bends (circular)
           * **wg_width** (float): Width of the waveguide as shown on the mask
           * **clad_width** (float): Width of the cladding (region next to waveguide, mainly used for positive-type photoresists + etching, or negative-type and liftoff)
           * **resist** (string): Must be either '+' or '-'.  Specifies the type of photoresist used
           * **fab** (string): If 'ETCH', then keeps resist as is, otherwise changes it from '+' to '-' (or vice versa).  This is mainly used to reverse the type of mask used if the fabrication type is 'LIFTOFF'
           * **wg_layer** (int): Layer type used for waveguides
           * **wg_datatype** (int): Data type used for waveguides
           * **clad_layer** (int): Layer type used for cladding
           * **clad_datatype** (int): Data type used for cladding

    """
    def __init__(self, bend_radius=50.0, wg_width=2.0, clad_width=10.0,
                 resist='+', fab='ETCH', wg_layer=1, wg_datatype=0, clad_layer=2, clad_datatype=0):
        self.wg_width = wg_width
        self.bend_radius = bend_radius
        self.clad_width = clad_width
        if resist != '+' and resist != '-':
            raise ValueError("Warning, invalid input for type resist in "
                             "WaveguideTemplate")
        if fab=='ETCH':
            self.resist = resist #default state assumes 'etching'
        else: #reverse waveguide type if liftoff or something else
            self.resist = '+' if resist=='-' else '-'

        self.wg_layer = wg_layer
        self.wg_datatype = wg_datatype
        self.clad_layer = clad_layer
        self.clad_datatype = clad_datatype

class Waveguide(gdspy.Cell):
    """ Standard Waveguide Cell class (subclass of gdspy.Cell).

        Args:
           * **trace** (list):  List of coordinates used to generate the waveguide (such as '[(x1,y1), (x2,y2), ...]').  For now, all trace points must specify 90 degree turns.
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) are the first elements of 'trace', (x2, y2) are the last elements of 'trace', and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.

    """
    def __init__(self, trace, wgt):
        gdspy.Cell.__init__(self,"Waveguide--"+str(uuid.uuid4()))

        self.portlist = {}

        self.trace = trace
        self.wgt = wgt
        self.resist = wgt.resist
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype} #Used for 'xor' operation

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
            dx = abs(self.trace[i+1][0]-self.trace[i][0])
            dy = abs(self.trace[i+1][1]-self.trace[i][1])
            if (dx < 2*self.wgt.bend_radius and dy < 2*self.wgt.bend_radius) and (i != 0) and (i!=len(self.trace)-2):
                raise ValueError("Warning!  All waypoints *must* be greater than "
                                 "two waveguide bend radii apart.")
            if ((i == 0) or (i==len(self.trace)-2)) and (dx < self.wgt.bend_radius and dy < self.wgt.bend_radius):
                raise ValueError("Warning! Start and end waypoints *must be greater "
                                 "than one waveguide bend radius apart.")
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
        br = self.wgt.bend_radius

        path = gdspy.Path(self.wgt.wg_width, self.trace[0])
        path2 = gdspy.Path(self.wgt.wg_width+2*self.wgt.clad_width, self.trace[0])

        prior_direction = tk.get_direction(self.trace[0], self.trace[1])
        path.segment(tk.dist(self.trace[0], self.trace[1])-br,
                     direction=tk.get_angle(self.trace[0], self.trace[1]),
                     **self.wg_spec)
        path2.segment(tk.dist(self.trace[0], self.trace[1])-br,
                     direction=tk.get_angle(self.trace[0], self.trace[1]),
                     **self.clad_spec)
        for i in range(len(self.trace)-2):
            direction = tk.get_direction(self.trace[i+1], self.trace[i+2])
            turn = tk.get_turn(prior_direction, direction)
            path.turn(br, turn, number_of_points=0.1, **self.wg_spec)
            path2.turn(br, turn, number_of_points=0.1, **self.clad_spec)
            if tk.dist(self.trace[i+1], self.trace[i+2])-2*br > 0: #ONLY False for last points if spaced br < distance < 2br
                path.segment(tk.dist(self.trace[i+1], self.trace[i+2])-2*br, **self.wg_spec)
                path2.segment(tk.dist(self.trace[i+1], self.trace[i+2])-2*br, **self.clad_spec)
            prior_direction = direction
        if tk.dist(self.trace[-2],self.trace[-1]) < 2*br:
            path.segment(tk.dist(self.trace[-2],self.trace[-1])-br, **self.wg_spec)
            path2.segment(tk.dist(self.trace[-2],self.trace[-1])-br, **self.clad_spec)
        else:
            path.segment(br, **self.wg_spec)
            path2.segment(br, **self.clad_spec)

        if len(self.trace)==2 and tk.dist(self.trace[1], self.trace[0])<=self.wgt.bend_radius:
            path = gdspy.Path(self.wgt.wg_width, self.trace[0])
            path.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_angle(self.trace[0], self.trace[1]), **self.wg_spec)
            path2 = gdspy.Path(self.wgt.wg_width+2*self.wgt.clad_width, self.trace[0])
            path2.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_angle(self.trace[0], self.trace[1]), **self.clad_spec)

        self.add(path)
        self.add(path2)

    def build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':(self.trace[0][0], self.trace[0][1]),
                                  'direction': tk.get_direction(self.trace[1], self.trace[0])}
        self.portlist["output"] = {'port':(self.trace[-1][0], self.trace[-1][1]),
                                   'direction':tk.get_direction(self.trace[-2], self.trace[-1])}

if __name__ == "__main__":
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+', fab="ETCH")

    wg1=Waveguide([(0,0), (250,0), (250,100), (500,100)], wgt)

    tk.add(top, wg1)

    gdspy.LayoutViewer()
    # gdspy.write_gds('waveguide.gds', unit=1.0e-6, precision=1.0e-9)

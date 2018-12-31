# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class WaveguideTemplate:
    """ Standard template for waveguides that contains standard information about the geometry and fabrication.

        Keyword Args:
           * **wg_type** (string): Type of waveguide used.  Options are "strip" and "slot".  Defaults to "strip".
           * **bend_radius** (float): Radius of curvature for waveguide bends (circular).  Defaults to 50.
           * **wg_width** (float): Width of the waveguide as shown on the mask.  Defaults to 2.
           * **slot** (float): Size of the waveguide slot region.  This is only used if `wg_type`=`'slot'`.  Defaults to 0.1.
           * **clad_width** (float): Width of the cladding (region next to waveguide, mainly used for positive-type photoresists + etching, or negative-type and liftoff).  Defaults to 10.
           * **resist** (string): Must be either '+' or '-'.  Specifies the type of photoresist used.  Defaults to '+'
           * **fab** (string): If 'ETCH', then keeps resist as is, otherwise changes it from '+' to '-' (or vice versa).  This is mainly used to reverse the type of mask used if the fabrication type is 'LIFTOFF'.   Defaults to 'ETCH'.
           * **wg_layer** (int): Layer type used for waveguides.  Defaults to 1.
           * **wg_datatype** (int): Data type used for waveguides.  Defaults to 0.
           * **clad_layer** (int): Layer type used for cladding.  Defaults to 2.
           * **clad_datatype** (int): Data type used for cladding.  Defaults to 0.

    """
    def __init__(self, wg_type='strip', bend_radius=50.0, wg_width=2.0, clad_width=10.0,
                 resist='+', fab='ETCH', slot=0.1,
                 wg_layer=1, wg_datatype=0, clad_layer=2, clad_datatype=0):
        self.wg_width = wg_width
        if wg_type in ['strip', 'slot']:
            self.wg_type = wg_type
        else:
            raise ValueError("Warning, invalid input for kwarg wg_type.")
        if self.wg_type =='slot':
            self.slot = slot
            self.rail = (self.wg_width - self.slot)/2.0
            self.rail_dist = self.wg_width -self.rail
        self.bend_radius = bend_radius
        self.clad_width = clad_width
        if resist != '+' and resist != '-':
            raise ValueError("Warning, invalid input for kwarg resist in "
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
           * **trace** (list):  List of coordinates used to generate the waveguide (such as '[(x1,y1), (x2,y2), ...]').
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) are the first elements of 'trace', (x2, y2) are the last elements of 'trace', and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*. 'Direction' points *towards* the component that the waveguide will connect to.

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
        """ Round each trace (x,y) point to the nearest 1e-6.
        Prevents some typechecking errors
        """
        for t in self.trace:
            trace.append((round(t[0], 6), round(t[1], 6)))
        self.trace = trace

        """ Type-check trace ¯\_(ツ)_/¯
        """
        prev_dx, prev_dy = 1,1 #initialize to arbitrary value
        for i in range(len(self.trace)-1):
            dx = abs(self.trace[i+1][0]-self.trace[i][0])+1E-10
            dy = abs(self.trace[i+1][1]-self.trace[i][1])+1E-10
            if ((prev_dx <= 1e-6 and dx<=1e-6) or (prev_dy <= 1e-6 and dy<=1e-6)):
                raise ValueError("Warning! Unnecessary waypoint specified.  All"
                                 " waypoints must specify a valid bend")
            prev_dx, prev_dy = dx, dy

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        br = self.wgt.bend_radius

        if len(self.trace)==2:
            if self.wgt.wg_type=='strip':
                path = gdspy.Path(self.wgt.wg_width, self.trace[0])
                path.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_exact_angle(self.trace[0], self.trace[1]), **self.wg_spec)
            elif self.wgt.wg_type=='slot':
                path = gdspy.Path(self.wgt.rail, self.trace[0], number_of_paths=2, distance=self.wgt.rail_dist)
                path.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_exact_angle(self.trace[0], self.trace[1]), **self.wg_spec)
            path2 = gdspy.Path(self.wgt.wg_width+2*self.wgt.clad_width, self.trace[0])
            path2.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_exact_angle(self.trace[0], self.trace[1]), **self.clad_spec)

        else:
            if self.wgt.wg_type=='strip':
                path = gdspy.Path(self.wgt.wg_width, self.trace[0])
            elif self.wgt.wg_type=='slot':
                path = gdspy.Path(self.wgt.rail, self.trace[0], number_of_paths=2, distance=self.wgt.rail_dist)
            path2 = gdspy.Path(self.wgt.wg_width+2*self.wgt.clad_width, self.trace[0])

            prev_dl = 0.0
            for i in range(len(self.trace)-2):
                start_angle = tk.get_exact_angle(self.trace[i], self.trace[i+1])
                next_angle = tk.get_exact_angle(self.trace[i+1], self.trace[i+2])

                #dl is the amount of distance that is taken *off* the waveguide from the curved section
                dl = abs(br*np.tan((next_angle-start_angle)/2.0))
                if (dl+prev_dl) > tk.dist(self.trace[i], self.trace[i+1])+1E-6:
                    raise ValueError("Warning! The waypoints "+str(self.trace[i])+" and "+str(self.trace[i+1])+" are too close to accommodate "
                                     " the necessary bend-radius of "+str(br)+", the points were closer than "+str(dl+prev_dl))

                path.segment(tk.dist(self.trace[i], self.trace[i+1])-dl-prev_dl,
                             direction=start_angle, **self.wg_spec)
                path2.segment(tk.dist(self.trace[i], self.trace[i+1])-dl-prev_dl,
                             direction=start_angle, **self.clad_spec)

                # The following makes sure the turn-by angle is *always* between -pi and +pi
                turnby = (next_angle - start_angle)%(2*np.pi)
                turnby = turnby-2*np.pi if turnby > np.pi else turnby

                path.turn(br, turnby, number_of_points=0.1, **self.wg_spec)
                path2.turn(br, turnby, number_of_points=0.1, **self.clad_spec)
                prev_dl = dl

            path.segment(tk.dist(self.trace[-2], self.trace[-1])-prev_dl,
                         direction=next_angle, **self.wg_spec)
            path2.segment(tk.dist(self.trace[-2], self.trace[-1])-prev_dl,
                         direction=next_angle, **self.clad_spec)

        self.add(path)
        self.add(path2)

    def build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':(self.trace[0][0], self.trace[0][1]),
                                  'direction': tk.get_exact_angle(self.trace[1], self.trace[0])}
        self.portlist["output"] = {'port':(self.trace[-1][0], self.trace[-1][1]),
                                   'direction':tk.get_exact_angle(self.trace[-2], self.trace[-1])}

if __name__ == "__main__":
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(wg_type='slot', wg_width=1.0, bend_radius=50, resist='+', fab="ETCH")

    wg1=Waveguide([(0,0), (150,0), (150,100), (250,100),(350,0), (200,-150)], wgt)
    tk.add(top, wg1)
    print(wg1.portlist)

    gdspy.LayoutViewer()
    # gdspy.write_gds('waveguide.gds', unit=1.0e-6, precision=1.0e-9)

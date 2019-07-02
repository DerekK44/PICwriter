# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk

class MMI1x2(tk.Component):
    """ 1x2 multi-mode interfereomter (MMI) Cell class.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length** (float): Length of the MMI region (along direction of propagation)
           * **width** (float): Width of the MMI region (perpendicular to direction of propagation)

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6.  Note: it is possible to generate a MMI with straight tapered outputs (not curved) by setting angle=0 and then connecting a straight Taper object to the desired MMI ports.
           * **taper_width** (float): Maximum width of the taper region (default = wg_width from wg_template).  Defaults to None (waveguide width).
           * **taper_length** (float): Length of the input taper leading up to the MMI (single-port side).  Defaults to None (taper_length=20).
           * **wg_sep** (float): Separation between waveguides on the 2-port side (defaults to width/3.0).  Defaults to None (width/3.0).
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output_top'] = {'port': (x2, y2), 'direction': 'dir2'}
           * portlist['output_bot'] = {'port': (x3, y3), 'direction': 'dir3'}

        Where in the above (x1,y1) is the input port, (x2, y2) is the top output port, (x3, y3) is the bottom output port, and 'dir1', 'dir2', 'dir3' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, wgt, length, width, angle=np.pi/6.0, taper_width=None, taper_length=None, wg_sep=None, port=(0,0), direction='EAST'):
        tk.Component.__init__(self, "MMI1x2")
        
        self.portlist = {}

        self.wgt = wgt
        self.length = length
        self.width = width
        if angle > np.pi/2.0 or angle < 0:
            raise ValueError("Warning! Improper angle specified ("+str(angle)+").  Must be between 0 and pi/2.0.")
        self.angle = angle
        self.taper_width = wgt.wg_width if taper_width==None else taper_width
        self.taper_length = 20 if taper_length==None else taper_length
        self.wg_sep = width/3.0 if wg_sep==None else wg_sep

        self.port = port
        self.direction = direction
        self.resist = wgt.resist
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.__type_check_values()
        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()
        
        """ The _hash_cell_ function makes sure that duplicate cells are not created.
        Pass to it all the unique properties of this cell, which are used to check for duplicates.
        Do *not* include properties like port, direction.  These are specific to Cell References only.
        """
        self._hash_cell_(wgt, length, width, angle, taper_width, taper_length, wg_sep)

    def __type_check_values(self):
        #Check that the values for the MMI1x2 are all valid

        if self.wg_sep > (self.width-self.taper_width):
            raise ValueError("Warning! Waveguide separation is larger than the "
                             "max value (width - taper_width)")
        if self.wg_sep < self.taper_width:
            raise ValueError("Warning! Waveguide separation is smaller than the "
                             "minimum value (taper_width)")

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # then add it to the Cell

        angle_x_dist = 2*self.wgt.bend_radius*np.sin(self.angle)
        angle_y_dist = 2*self.wgt.bend_radius*(1-np.cos(self.angle))

        path1 = gdspy.Path(self.wgt.wg_width, (0,0))
        path1.segment(self.taper_length, direction='+x', final_width=self.taper_width, **self.wg_spec)

        path2 = gdspy.Path(self.width, (path1.x, path1.y))
        path2.segment(self.length, direction='+x', **self.wg_spec)

        path3 = gdspy.Path(self.taper_width, (path2.x, path2.y+self.wg_sep/2.0))
        path3.turn(self.wgt.bend_radius, self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width, **self.wg_spec)
        path3.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)

        path4 = gdspy.Path(self.taper_width, (path2.x, path2.y-self.wg_sep/2.0))
        path4.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width, **self.wg_spec)
        path4.turn(self.wgt.bend_radius, self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)

        clad_pts = [(0.0, -self.wgt.wg_width/2.0-self.wgt.clad_width),
                    (self.taper_length, -self.width/2.0-self.wgt.clad_width),
                    (self.taper_length+self.length, -self.width/2.0-self.wgt.clad_width),
                    (2*self.taper_length+self.length, -self.wg_sep/2.0-self.wgt.wg_width/2.0-self.wgt.clad_width),
                    (2*self.taper_length+self.length, self.wg_sep/2.0+self.wgt.wg_width/2.0+self.wgt.clad_width),
                    (self.taper_length+self.length, self.width/2.0+self.wgt.clad_width),
                    (self.taper_length, self.width/2.0+self.wgt.clad_width),
                    (0.0, self.wgt.wg_width/2.0+self.wgt.clad_width)]
        clad = gdspy.Polygon(clad_pts, **self.clad_spec)

        clad_path3 = gdspy.Path(self.taper_width+2*self.wgt.clad_width, (path2.x, path2.y+self.wg_sep/2.0))
        clad_path3.turn(self.wgt.bend_radius, self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        clad_path3.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)

        clad_path4 = gdspy.Path(self.taper_width+2*self.wgt.clad_width, (path2.x, path2.y-self.wg_sep/2.0))
        clad_path4.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        clad_path4.turn(self.wgt.bend_radius, +self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)

        totlength = self.length + angle_x_dist + self.taper_length #2*self.taper_length+self.length
        ylength = self.wg_sep/2.0 + angle_y_dist
        
        self.output_port_top = (totlength, ylength)
        self.output_port_bot = (totlength, -ylength)

        self.cell.add(path1)
        self.cell.add(path2)
        self.cell.add(path3)
        self.cell.add(path4)
        self.cell.add(clad_path3)
        self.cell.add(clad_path4)
        self.cell.add(clad)

    def __build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}

        self.portlist["input"] = {'port':(0,0), 'direction':tk.flip_direction(self.direction)}
        self.portlist["output_top"] = {'port':self.output_port_top, 'direction':self.direction}
        self.portlist["output_bot"] = {'port':self.output_port_bot, 'direction':self.direction}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

    wg1=Waveguide([(0, 0), (100, 100)], wgt)
    tk.add(top, wg1)

    mmi = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, **wg1.portlist["output"])
    mmi2 = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, **mmi.portlist["output_top"])
    mmi3 = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, **mmi.portlist["output_bot"])
    # mmi = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=4.0, port=(0,0), direction='EAST')
    mmi.addto(top)
    mmi2.addto(top)
    mmi3.addto(top)
#    tk.add(top, mmi)
#    tk.add(top, mmi2)
#    tk.add(top, mmi3)

    gdspy.LayoutViewer()
    # gdspy.write_gds('mmi1x2.gds', unit=1.0e-6, precision=1.0e-9)

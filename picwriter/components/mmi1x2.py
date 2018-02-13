# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class MMI1x2(gdspy.Cell):
    """ Standard 1x2 MMI Cell class (subclass of gdspy.Cell).

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length** (float): Length of the MMI region (along direction of propagation)
           * **width** (float): Width of the MMI region (perpendicular to direction of propagation)

        Keyword Args:
           * **taper_width** (float): Maximum width of the taper region (default = wg_width from wg_template).  Defaults to None (waveguide width).
           * **taper_length** (float): Length of the taper leading up to the MMI.  Defaults to None (taper_length=20).
           * **wg_sep** (float): Separation between waveguides on the 2-port side (defaults to width/3.0).  Defaults to None (width/3.0).
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the taper will point *towards*, must be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.  Defaults to `'EAST'`.

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output_top'] = {'port': (x2, y2), 'direction': 'dir2'}
           * portlist['output_bot'] = {'port': (x3, y3), 'direction': 'dir3'}

        Where in the above (x1,y1) is the input port, (x2, y2) is the top output port, (x3, y3) is the bottom output port, and 'dir1', 'dir2', 'dir3' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.

    """
    def __init__(self, wgt, length, width, taper_width=None, taper_length=None, wg_sep=None, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "MMI1x2--"+str(uuid.uuid4()))

        self.portlist = {}

        self.wgt = wgt
        self.length = length
        self.width = width
        self.taper_width = wgt.wg_width if taper_width==None else taper_width
        self.taper_length = 20 if taper_length==None else taper_length
        self.wg_sep = width/3.0 if wg_sep==None else wg_sep

        self.port = port
        self.direction = direction
        self.resist = wgt.resist
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.type_check_values()
        self.build_cell()
        self.build_ports()

    def type_check_values(self):
        #Check that the values for the MMI1x2 are all valid

        if self.wg_sep > (self.width-self.taper_width):
            raise ValueError("Warning! Waveguide separation is larger than the "
                             "max value (width - taper_width)")
        if self.wg_sep < self.taper_width:
            raise ValueError("Warning! Waveguide separation is smaller than the "
                             "minimum value (taper_width)")

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # then add it to the Cell

        path1 = gdspy.Path(self.wgt.wg_width, self.port)
        path1.segment(self.taper_length, direction='+x', final_width=self.taper_width, **self.wg_spec)
        path2 = gdspy.Path(self.width, (self.port[0]+self.taper_length, self.port[1]))
        path2.segment(self.length, direction='+x', **self.wg_spec)
        path3 = gdspy.Path(self.wgt.wg_width, (self.port[0]+2*self.taper_length+self.length, self.port[1]+self.wg_sep/2.0))
        path3.segment(self.taper_length, direction='-x',final_width=self.taper_width, **self.wg_spec)
        path4 = gdspy.Path(self.wgt.wg_width, (self.port[0]+2*self.taper_length+self.length, self.port[1]-self.wg_sep/2.0))
        path4.segment(self.taper_length, direction='-x', final_width=self.taper_width, **self.wg_spec)

        clad_pts = [(self.port[0], self.port[1]-self.wgt.wg_width/2.0-self.wgt.clad_width),
                    (self.port[0]+self.taper_length, self.port[1]-self.width/2.0-self.wgt.clad_width),
                    (self.port[0]+self.taper_length+self.length, self.port[1]-self.width/2.0-self.wgt.clad_width),
                    (self.port[0]+2*self.taper_length+self.length, self.port[1]-self.wg_sep/2.0-self.wgt.wg_width/2.0-self.wgt.clad_width),
                    (self.port[0]+2*self.taper_length+self.length, self.port[1]+self.wg_sep/2.0+self.wgt.wg_width/2.0+self.wgt.clad_width),
                    (self.port[0]+self.taper_length+self.length, self.port[1]+self.width/2.0+self.wgt.clad_width),
                    (self.port[0]+self.taper_length, self.port[1]+self.width/2.0+self.wgt.clad_width),
                    (self.port[0], self.port[1]+self.wgt.wg_width/2.0+self.wgt.clad_width)]
        clad = gdspy.Polygon(clad_pts, **self.clad_spec)

        angle=0
        if self.direction=="EAST":
            self.output_port_top = (self.port[0]+2*self.taper_length+self.length, self.port[1]+self.wg_sep/2.0)
            self.output_port_bot = (self.port[0]+2*self.taper_length+self.length, self.port[1]-self.wg_sep/2.0)
        elif self.direction=="NORTH":
            self.output_port_top = (self.port[0]-self.wg_sep/2.0, self.port[1]+2*self.taper_length+self.length)
            self.output_port_bot = (self.port[0]+self.wg_sep/2.0, self.port[1]+2*self.taper_length+self.length)
            angle=np.pi/2.0
        elif self.direction=="WEST":
            self.output_port_top = (self.port[0]-2*self.taper_length-self.length, self.port[1]-self.wg_sep/2.0)
            self.output_port_bot = (self.port[0]-2*self.taper_length-self.length, self.port[1]+self.wg_sep/2.0)
            angle=np.pi
        elif self.direction=="SOUTH":
            self.output_port_top = (self.port[0]+self.wg_sep/2.0, self.port[1]-2*self.taper_length-self.length)
            self.output_port_bot = (self.port[0]-self.wg_sep/2.0, self.port[1]-2*self.taper_length-self.length)
            angle=-np.pi/2.0

        path1.rotate(angle, self.port)
        path2.rotate(angle, self.port)
        path3.rotate(angle, self.port)
        path4.rotate(angle, self.port)
        clad.rotate(angle, self.port)

        self.add(path1)
        self.add(path2)
        self.add(path3)
        self.add(path4)
        self.add(clad)

    def build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}

        self.portlist["input"] = {'port':self.port, 'direction':tk.flip_direction(self.direction)}
        self.portlist["output_top"] = {'port':self.output_port_top, 'direction':self.direction}
        self.portlist["output_bot"] = {'port':self.output_port_bot, 'direction':self.direction}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

    wg1=Waveguide([(0, 0), (100, 0)], wgt)
    tk.add(top, wg1)

    mmi = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, **wg1.portlist["output"])
    # mmi = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=4.0, port=(0,0), direction='EAST')
    tk.add(top, mmi)

    gdspy.LayoutViewer()
    # gdspy.write_gds('mmi1x2.gds', unit=1.0e-6, precision=1.0e-9)

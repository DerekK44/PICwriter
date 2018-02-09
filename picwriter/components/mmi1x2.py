# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class MMI1x2(gdspy.Cell):
    def __init__(self, wgt, length, width, taper_width=None, taper_length=None, wg_sep=None, port=(0,0), direction='EAST'):
        """
        wg_template, center=(0,0), length=33.0, width=6.0, taper_width=0, taper_length=25.0, wg_sep=0):
        Defines a horizontal (input from left, output on right) multimode interferometer
        First initiate super properties (gdspy.Cell)
        length = horizontal length of the MMI region
        width = vertical height of the MMI region
        taper_width = max width of the taper region (default=wg_width from wg_template)
        taper_length = length of the taper leading up to the MMI
        wg_sep = separation between waveguides on the 2-port side (defaults to 0.5*width)
        """
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
        self.wgt = wgt
        self.spec = {'layer': wgt.layer, 'datatype': wgt.datatype}

        self.type_check_values()
        self.build_cell()
        self.build_ports()

    def type_check_values(self):
        """ Check that the values for the MMI1x2 are all valid
        """
        if self.wg_sep > (self.width-self.taper_width):
            raise ValueError("Warning! Waveguide separation is larger than the "
                             "max value (width - taper_width)")
        if self.wg_sep < self.taper_width:
            raise ValueError("Warning! Waveguide separation is smaller than the "
                             "minimum value (taper_width)")

    def build_cell(self):
        """
        Sequentially build all the geometric shapes using gdspy path functions
        then add it to the Cell
        """
        if self.resist=='-':
            path1 = gdspy.Path(self.wgt.wg_width, self.port)
            path1.segment(self.taper_length, direction='+x', final_width=self.taper_width, **self.spec)
            path2 = gdspy.Path(self.width, (self.port[0]+self.taper_length, self.port[1]))
            path2.segment(self.length, direction='+x', **self.spec)
            path3 = gdspy.Path(self.wgt.wg_width, (self.port[0]+2*self.taper_length+self.length, self.port[1]+self.wg_sep/2.0))
            path3.segment(self.taper_length, direction='-x',final_width=self.taper_width, **self.spec)
            path4 = gdspy.Path(self.wgt.wg_width, (self.port[0]+2*self.taper_length+self.length, self.port[1]-self.wg_sep/2.0))
            path4.segment(self.taper_length, direction='-x', final_width=self.taper_width, **self.spec)
        elif self.resist=='+':
            path1 = gdspy.Path(self.wgt.clad_width, self.port, number_of_paths=2,
                               distance=self.wgt.wg_width+self.wgt.clad_width)
            path1.segment(self.taper_length, direction='+x', final_distance=self.taper_width+self.wgt.clad_width,
                          **self.spec)
            path2 = gdspy.Path(self.wgt.clad_width, (self.port[0]+self.taper_length, self.port[1]),
                               number_of_paths=2, distance=self.width+self.wgt.clad_width)
            path2.segment(self.length, direction='+x', **self.spec)
            path3 = gdspy.Path(self.wgt.clad_width, (self.port[0]+2*self.taper_length+self.length, self.port[1]),
                               number_of_paths=2, distance=self.wgt.wg_width+self.wg_sep+self.wgt.clad_width)
            path3.segment(self.taper_length, direction='-x', final_distance=self.taper_width+self.wg_sep+self.wgt.clad_width,
                          **self.spec)
            path4 = gdspy.Path(self.wg_sep-self.wgt.wg_width, (self.port[0]+2*self.taper_length+self.length, self.port[1]))
            path4.segment(self.taper_length, direction='-x', final_width=self.wg_sep-self.taper_width, **self.spec)

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

        self.add(path1)
        self.add(path2)
        self.add(path3)
        self.add(path4)

    def build_ports(self):
        """ Portlist format:
            example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        """
        self.portlist["input"] = {'port':self.port, 'direction':tk.flip_direction(self.direction)}
        self.portlist["output_top"] = {'port':self.output_port_top, 'direction':self.direction}
        self.portlist["output_bot"] = {'port':self.output_port_bot, 'direction':self.direction}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')

    wg1=Waveguide([(0, 0), (0, -100)], wgt)
    tk.add(top, wg1)

    mmi = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, **wg1.portlist["output"])
    tk.add(top, mmi)

    gdspy.LayoutViewer()

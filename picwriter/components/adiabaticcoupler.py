# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk
from picwriter.components.waveguide import Waveguide

class AdiabaticCoupler(tk.PICcomponent):
    """ Adiabatic Coupler Cell class (subclass of gdspy.Cell).  Design based on asymmetric adiabatic 3dB coupler designs, such as those from https://doi.org/10.1364/CLEO.2010.CThAA2, https://doi.org/10.1364/CLEO_SI.2017.SF1I.5, and https://doi.org/10.1364/CLEO_SI.2018.STh4B.4.

    In this design, Region I is the first half of the input S-bend waveguide where the input waveguides widths taper by +dw and -dw, Region II is the second half of the S-bend waveguide with constant, unbalanced widths, Region III is the region where the two asymmetric waveguides gradually come together, Region IV is the coupling region where the waveguides taper back to the original width at a fixed distance from one another, and Region IV is the  output S-bend waveguide.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length1** (float): Length of the region that gradually brings the two assymetric waveguides together
           * **length2** (float): Length of the coupling region, where the asymmetric waveguides gradually become the same width.
           * **gap** (float): Distance between the two waveguides.
           * **fargap** (float): Largest distance between the two waveguides (Region III).
           * **dw** (float): Change in waveguide width.  Top arm tapers to the waveguide width - dw, bottom taper to width - dw.

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6.
           * **port** (tuple): Cartesian coordinate of the input port (top left).  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to 'EAST'.

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input_top'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['input_bot'] = {'port': (x2,y2), 'direction': 'dir1'}
           * portlist['output_top'] = {'port': (x3, y3), 'direction': 'dir3'}
           * portlist['output_bot'] = {'port': (x4, y4), 'direction': 'dir4'}

        Where in the above (x1,y1) is the same as the input 'port', (x3, y3), and (x4, y4) are the two output port locations.  Directions 'dir1', 'dir2', etc. are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, 
                 wgt, 
                 length1, 
                 length2,
                 gap, 
                 fargap,
                 dw, 
                 angle=np.pi/6.0, 
                 port=(0,0), 
                 direction='EAST'):
        tk.PICcomponent.__init__(self, "AdiabaticCoupler")

        self.portlist = {}

        self.port = port
        self.direction = direction

        if angle > np.pi/2.0 or angle < 0:
            raise ValueError("Warning! Improper angle specified ("+str(angle)+").  Must be between 0 and pi/2.0.")
        self.angle = angle
        self.length1 = length1
        self.length2 = length2
        self.gap = gap
        self.fargap = fargap
        self.dw = dw
        self.wgt = wgt
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()
        
        """ The _hash_cell_ function makes sure that duplicate cells are not created.
        Pass to it all the unique properties of this cell, which are used to check for duplicates.
        Do *not* include properties like port, direction.  These are specific to Cell References only.
        """
        self._hash_cell_(wgt, length1, length2, gap, fargap, dw, angle)

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        angle_x_dist = 2*self.wgt.bend_radius*np.sin(self.angle)

        angle_y_dist = 2*self.wgt.bend_radius*(1-np.cos(self.angle))
        distx = 2*angle_x_dist + self.length1 + self.length2
        disty1 = (2*abs(angle_y_dist) + self.fargap + self.wgt.wg_width)
        disty2 = (2*abs(angle_y_dist) + self.gap + self.wgt.wg_width)

        x0, y0 = 0.0, 0.0 #shift to port location after rotation later

        """ Build the adiabatic DC from gdspy Path derivatives """
        """ First the top waveguide """
        wg_top = gdspy.Path(self.wgt.wg_width, (x0, y0))
        wg_top.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+self.dw, **self.wg_spec)
        wg_top.turn(self.wgt.bend_radius, self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)
        
        pts = [(wg_top.x, wg_top.y + self.wgt.wg_width/2.0 + self.dw/2.0),
               (wg_top.x, wg_top.y - self.wgt.wg_width/2.0 - self.dw/2.0),
               (wg_top.x + self.length1, wg_top.y - self.wgt.wg_width/2.0 - (self.fargap-self.gap)/2.0 - self.dw/2.0),
               (wg_top.x + self.length1, wg_top.y + self.wgt.wg_width/2.0 - (self.fargap-self.gap)/2.0 + self.dw/2.0)]
        taper_top = gdspy.Polygon(pts, **self.wg_spec)
        
        wg_top2 = gdspy.Path(self.wgt.wg_width + self.dw, (wg_top.x+self.length1, wg_top.y - (self.fargap-self.gap)/2.0))
        wg_top2.segment(self.length2, final_width=self.wgt.wg_width, **self.wg_spec)
        wg_top2.turn(self.wgt.bend_radius, self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)
        wg_top2.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width, **self.wg_spec)

        wg_top_clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, (x0, y0))
        wg_top_clad.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_top_clad.segment(self.length1 + self.length2, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)

        """ Next, the bottom waveguide """
        x1, y1 = 0.0, -disty1
        wg_bot = gdspy.Path(self.wgt.wg_width, (x1, y1))
        wg_bot.turn(self.wgt.bend_radius, +self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width-self.dw, **self.wg_spec)
        wg_bot.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)
        
        pts = [(wg_bot.x, wg_bot.y - self.wgt.wg_width/2.0 + self.dw/2.0),
               (wg_bot.x, wg_bot.y + self.wgt.wg_width/2.0 - self.dw/2.0),
               (wg_bot.x + self.length1, wg_bot.y + self.wgt.wg_width/2.0 + (self.fargap-self.gap)/2.0 - self.dw/2.0),
               (wg_bot.x + self.length1, wg_bot.y - self.wgt.wg_width/2.0 + (self.fargap-self.gap)/2.0 + self.dw/2.0)]
        taper_bot = gdspy.Polygon(pts, **self.wg_spec)
        
        wg_bot2 = gdspy.Path(self.wgt.wg_width - self.dw, (wg_bot.x+self.length1, wg_bot.y + (self.fargap-self.gap)/2.0))
        wg_bot2.segment(self.length2, final_width=self.wgt.wg_width, **self.wg_spec)
        wg_bot2.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)
        wg_bot2.turn(self.wgt.bend_radius, +self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width, **self.wg_spec)

        wg_bot_clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, (x1, y1))
        wg_bot_clad.turn(self.wgt.bend_radius, +self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_bot_clad.segment(self.length1 + self.length2, **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, -self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, +self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)

        port_dy = (self.fargap - self.gap)/2.0

        self.portlist_input_top = (0,0)
        self.portlist_input_bot = (0, -disty1)
        self.portlist_output_top = (distx, -port_dy)
        self.portlist_output_bot = (distx, -disty1+port_dy)

        self.cell.add(wg_top)
        self.cell.add(wg_bot)
        self.cell.add(wg_top_clad)
        self.cell.add(wg_bot_clad)
        self.cell.add(taper_top)
        self.cell.add(taper_bot)
        self.cell.add(wg_top2)
        self.cell.add(wg_bot2)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input_top"] = {'port':self.portlist_input_top, 'direction':tk.flip_direction(self.direction)}
        self.portlist["input_bot"] = {'port':self.portlist_input_bot, 'direction':tk.flip_direction(self.direction)}
        self.portlist["output_top"] = {'port':self.portlist_output_top, 'direction':self.direction}
        self.portlist["output_bot"] = {'port':self.portlist_output_bot, 'direction':self.direction}

if __name__ == "__main__":
    from . import *
    from picwriter.components.waveguide import WaveguideTemplate
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(wg_width=2.0, bend_radius=100, resist='+')

    wg1=Waveguide([(0,0), (100,200)], wgt)
    tk.add(top, wg1)

    ac = AdiabaticCoupler(wgt, 
                          length1=60.0, 
                          length2=50.0,
                          gap=0.5, 
                          fargap=6.0,
                          dw=1.0, 
                          angle=np.pi/16.0, 
                          **wg1.portlist["output"])
    tk.add(top, ac)
    
    ac2 = AdiabaticCoupler(wgt, 
                          length1=60.0, 
                          length2=50.0,
                          gap=0.5, 
                          fargap=6.0,
                          dw=1.0, 
                          angle=np.pi/16.0, 
                          **ac.portlist["output_bot"])
    tk.add(top, ac2)
    
    for p in ac.portlist.keys():
        print(str(p)+": "+str(ac.portlist[p]['port']))

    gdspy.LayoutViewer()
#    gdspy.write_gds('ac.gds', unit=1.0e-6, precision=1.0e-9)

# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk
from picwriter.components.waveguide import Waveguide

class AdiabaticCoupler(gdspy.Cell):
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
           * **parity** (integer -1 or 1): If -1, mirror-flips the structure so that the input port is actually the *bottom* port.  Default = 1.
           * **port** (tuple): Cartesian coordinate of the input port (AT TOP if parity=1, AT BOTTOM if parity=-1).  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to 'EAST'.

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input_top'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['input_bot'] = {'port': (x2,y2), 'direction': 'dir1'}
           * portlist['output_top'] = {'port': (x3, y3), 'direction': 'dir3'}
           * portlist['output_bot'] = {'port': (x4, y4), 'direction': 'dir4'}

        Where in the above (x1,y1) (or (x2,y2) if parity=-1) is the same as the input 'port', (x3, y3), and (x4, y4) are the two output port locations.  Directions 'dir1', 'dir2', etc. are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
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
                 parity=1, 
                 port=(0,0), 
                 direction='EAST'):
        gdspy.Cell.__init__(self, tk.getCellName("AdiabaticCoupler"))

        self.portlist = {}

        self.port = port
        self.direction = direction

        if angle > np.pi/2.0 or angle < 0:
            raise ValueError("Warning! Improper angle specified ("+str(angle)+").  Must be between 0 and pi/2.0.")
        self.angle = angle
        if parity != 1 and parity!=-1:
            raise ValueError("Warning!  Parity input *must* be 1 or -1.  Received parity="+str(parity)+" instead.")
        self.parity = parity
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

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        p = self.parity
        angle_x_dist = 2*self.wgt.bend_radius*np.sin(self.angle)

        angle_y_dist = 2*self.wgt.bend_radius*(1-np.cos(self.angle))
        distx = 2*angle_x_dist + self.length1 + self.length2
        disty1 = p*(2*abs(angle_y_dist) + self.fargap + self.wgt.wg_width)
        disty2 = p*(2*abs(angle_y_dist) + self.gap + self.wgt.wg_width)

        x0, y0 = self.port[0],self.port[1] #shift to port location after rotation later

        """ Build the adiabatic DC from gdspy Path derivatives """
        """ First the top waveguide """
        wg_top = gdspy.Path(self.wgt.wg_width, (x0, y0))
        wg_top.turn(self.wgt.bend_radius, -p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+self.dw, **self.wg_spec)
        wg_top.turn(self.wgt.bend_radius, p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)
        
        pts = [(wg_top.x, wg_top.y + self.wgt.wg_width/2.0 + self.dw/2.0),
               (wg_top.x, wg_top.y - self.wgt.wg_width/2.0 - self.dw/2.0),
               (wg_top.x + self.length1, wg_top.y - self.wgt.wg_width/2.0 - (self.fargap-self.gap)/2.0 - self.dw/2.0),
               (wg_top.x + self.length1, wg_top.y + self.wgt.wg_width/2.0 - (self.fargap-self.gap)/2.0 + self.dw/2.0)]
        taper_top = gdspy.Polygon(pts, **self.wg_spec)
        
        wg_top2 = gdspy.Path(self.wgt.wg_width + self.dw, (wg_top.x+self.length1, wg_top.y - (self.fargap-self.gap)/2.0))
        wg_top2.segment(self.length2, final_width=self.wgt.wg_width, **self.wg_spec)
        wg_top2.turn(self.wgt.bend_radius, p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)
        wg_top2.turn(self.wgt.bend_radius, -p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width, **self.wg_spec)

        wg_top_clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, (x0, y0))
        wg_top_clad.turn(self.wgt.bend_radius, -p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_top_clad.segment(self.length1 + self.length2, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, -p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)

        """ Next, the bottom waveguide """
        x1, y1 = self.port[0], self.port[1] - disty1
        wg_bot = gdspy.Path(self.wgt.wg_width, (x1, y1))
        wg_bot.turn(self.wgt.bend_radius, +p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width-self.dw, **self.wg_spec)
        wg_bot.turn(self.wgt.bend_radius, -p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)
        
        pts = [(wg_bot.x, wg_bot.y - self.wgt.wg_width/2.0 + self.dw/2.0),
               (wg_bot.x, wg_bot.y + self.wgt.wg_width/2.0 - self.dw/2.0),
               (wg_bot.x + self.length1, wg_bot.y + self.wgt.wg_width/2.0 + (self.fargap-self.gap)/2.0 - self.dw/2.0),
               (wg_bot.x + self.length1, wg_bot.y - self.wgt.wg_width/2.0 + (self.fargap-self.gap)/2.0 + self.dw/2.0)]
        taper_bot = gdspy.Polygon(pts, **self.wg_spec)
        
        wg_bot2 = gdspy.Path(self.wgt.wg_width - self.dw, (wg_bot.x+self.length1, wg_bot.y + (self.fargap-self.gap)/2.0))
        wg_bot2.segment(self.length2, final_width=self.wgt.wg_width, **self.wg_spec)
        wg_bot2.turn(self.wgt.bend_radius, -p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.wg_spec)
        wg_bot2.turn(self.wgt.bend_radius, +p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width, **self.wg_spec)

        wg_bot_clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, (x1, y1))
        wg_bot_clad.turn(self.wgt.bend_radius, +p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, -p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_bot_clad.segment(self.length1 + self.length2, **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, -p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, +p*self.angle, number_of_points=self.wgt.get_num_points(self.angle), **self.clad_spec)

        port_dy = (self.fargap - self.gap)/2.0
        if self.direction=="WEST":
            angle = np.pi
            self.portlist_output_straight = (self.port[0]-distx, self.port[1] + port_dy)
            self.portlist_output_cross = (self.port[0]-distx, self.port[1] + disty1-port_dy)
            self.portlist_input_cross = (self.port[0], self.port[1] + disty1)
        elif self.direction=="SOUTH":
            angle = -np.pi/2.0
            self.portlist_output_straight = (self.port[0]-port_dy, self.port[1]-distx)
            self.portlist_output_cross = (self.port[0]-disty1+port_dy, self.port[1]-distx)
            self.portlist_input_cross = (self.port[0]-disty1, self.port[1])
        elif self.direction=="EAST":
            angle = 0
            self.portlist_output_straight = (self.port[0]+distx, self.port[1] - port_dy)
            self.portlist_output_cross = (self.port[0]+distx, self.port[1]-disty1+port_dy)
            self.portlist_input_cross = (self.port[0], self.port[1]-disty1)
        elif self.direction=="NORTH":
            angle = np.pi/2.0
            self.portlist_output_straight = (self.port[0]+port_dy, self.port[1]+distx)
            self.portlist_output_cross = (self.port[0]+disty1-port_dy, self.port[1]+distx)
            self.portlist_input_cross = (self.port[0]+disty1, self.port[1])
        elif isinstance(self.direction, float):
            angle = self.direction
            self.portlist_output_straight = (self.port[0]+distx*np.cos(self.direction)-(-port_dy)*np.sin(self.direction), self.port[1]+distx*np.sin(self.direction)+(-port_dy)*np.cos(self.direction))
            self.portlist_input_cross = (self.port[0]-(-disty1)*np.sin(self.direction), self.port[1]+(-disty1)*np.cos(self.direction))
            self.portlist_output_cross = (self.port[0]-(-disty1+port_dy)*np.sin(self.direction)+distx*np.cos(self.direction), self.port[1]+(-disty1 + port_dy)*np.cos(self.direction)+distx*np.sin(self.direction))

        wg_top.rotate(angle, self.port)
        wg_bot.rotate(angle, self.port)
        wg_top_clad.rotate(angle, self.port)
        wg_bot_clad.rotate(angle, self.port)
        taper_top.rotate(angle, self.port)
        taper_bot.rotate(angle, self.port)
        wg_top2.rotate(angle, self.port)
        wg_bot2.rotate(angle, self.port)

        self.add(wg_top)
        self.add(wg_bot)
        self.add(wg_top_clad)
        self.add(wg_bot_clad)
        self.add(taper_top)
        self.add(taper_bot)
        self.add(wg_top2)
        self.add(wg_bot2)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        if self.parity==1:
            self.portlist["input_top"] = {'port':self.port, 'direction':tk.flip_direction(self.direction)}
            self.portlist["input_bot"] = {'port':self.portlist_input_cross, 'direction':tk.flip_direction(self.direction)}
            self.portlist["output_top"] = {'port':self.portlist_output_straight, 'direction':self.direction}
            self.portlist["output_bot"] = {'port':self.portlist_output_cross, 'direction':self.direction}
        elif self.parity==-1:
            self.portlist["input_top"] = {'port':self.portlist_input_cross, 'direction':tk.flip_direction(self.direction)}
            self.portlist["input_bot"] = {'port':self.port, 'direction':tk.flip_direction(self.direction)}
            self.portlist["output_top"] = {'port':self.portlist_output_cross, 'direction':self.direction}
            self.portlist["output_bot"] = {'port':self.portlist_output_straight, 'direction':self.direction}

if __name__ == "__main__":
    from . import *
    from picwriter.components.waveguide import WaveguideTemplate
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(wg_width=2.0, bend_radius=100, resist='+')

    wg1=Waveguide([(0,0), (100,0)], wgt)
    tk.add(top, wg1)

    ac = AdiabaticCoupler(wgt, 
                          length1=60.0, 
                          length2=50.0,
                          gap=0.5, 
                          fargap=6.0,
                          dw=1.0, 
                          angle=np.pi/16.0, 
                          parity=1, 
                          **wg1.portlist["output"])
    tk.add(top, ac)
    for p in ac.portlist.keys():
        print(str(p)+": "+str(ac.portlist[p]['port']))

    gdspy.LayoutViewer()
#    gdspy.write_gds('ac.gds', unit=1.0e-6, precision=1.0e-9)

# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk
from picwriter.components.waveguide import Waveguide

class ContraDirectionalCoupler(gdspy.Cell):
    """ Grating-Assisted Contra-Directional Coupler Cell class (subclass of gdspy.Cell).

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length** (float): Length of the coupling region.
           * **gap** (float): Distance between the two waveguides.
           * **period** (float): Period of the grating.
           * **dc** (float): Duty cycle of the grating. Must be between 0 and 1.

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6.
           * **width_top** (float): Width of the top waveguide in the coupling region.  Defaults to the WaveguideTemplate wg width.
           * **width_bot** (float): Width of the bottom waveguide in the coupling region.  Defaults to the WaveguideTemplate wg width.
           * **dw_top** (float): Amplitude of the width variation on the top.  Default=gap/2.0.
           * **dw_bot** (float): Amplitude of the width variation on the bottom.  Default=gap/2.0.
           * **input_bot** (boolean): If `True`, will make the default input the bottom waveguide (rather than the top).  Default=`False`
           * **fins** (boolean): If `True`, adds fins to the input/output waveguides.  In this case a different template for the component must be specified.  This feature is useful when performing electron-beam lithography and using different beam currents for fine features (helps to reduce stitching errors).  Defaults to `False`
           * **fin_size** ((x,y) Tuple): Specifies the x- and y-size of the `fins`.  Defaults to 200 nm x 50 nm
           * **contradc_wgt** (WaveguideTemplate): If `fins` above is True, a WaveguideTemplate (contradc_wgt) must be specified.  This defines the layertype / datatype of the ContraDC (which will be separate from the input/output waveguides).  Defaults to `None`
           * **port** (tuple): Cartesian coordinate of the input port (AT TOP if input_bot=False, AT BOTTOM if input_bot=True).  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to 'EAST'.

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input_top'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['input_bot'] = {'port': (x2,y2), 'direction': 'dir1'}
           * portlist['output_top'] = {'port': (x3, y3), 'direction': 'dir3'}
           * portlist['output_bot'] = {'port': (x4, y4), 'direction': 'dir4'}

        Where in the above (x1,y1) (or (x2,y2) if input_bot=False) is the same as the input 'port', (x3, y3), and (x4, y4) are the two output port locations.  Directions 'dir1', 'dir2', etc. are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, wgt, length, gap, period, dc, angle=np.pi/6.0, width_top=None, width_bot=None, dw_top=None, dw_bot=None, input_bot=False, fins=False, fin_size=(0.2, 0.05), contradc_wgt=None, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "ContraDC--"+str(uuid.uuid4()))

        self.portlist = {}

        self.port = port
        self.direction = direction

        if angle > np.pi/2.0 or angle < 0:
            raise ValueError("Warning! Improper angle specified ("+str(angle)+").  Must be between 0 and pi/2.0.")
        self.angle = angle
        if dc > 1.0 or dc < 0.0:
            raise ValueError("Warning!  Dutycycle must be between 0 and 1.  Received dc="+str(dc)+" instead.")

        if width_top is not None:
            self.width_top=width_top
        else:
            self.width_top=wgt.wg_width
        if width_bot is not None:
            self.width_bot=width_bot
        else:
            self.width_bot=wgt.wg_width
        if input_bot:
            self.parity = -1
        else:
            self.parity = 1

        self.dw_top = gap/2.0 if dw_top==None else dw_top
        self.dw_bot = gap/2.0 if dw_bot==None else dw_bot
        self.length = length
        self.gap = gap
        self.dc = dc
        self.period = period

        self.fins = fins
        self.fin_size = fin_size

        if fins:
            self.wgt = contradc_wgt
            self.side_wgt = wgt
            self.wg_spec = {'layer': contradc_wgt.wg_layer, 'datatype': contradc_wgt.wg_datatype}
            self.clad_spec = {'layer': contradc_wgt.clad_layer, 'datatype': contradc_wgt.clad_datatype}
            self.fin_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
            if contradc_wgt is None:
                raise ValueError("Warning! A waveguide template for the ContraDirectionalCoupler (contradc_wgt) must be specified.")
        else:
            self.wgt = wgt
            self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
            self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.build_cell()
        self.build_ports()

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell

        # Calculate some values useful for placing contra DC object later
        dlx = abs(self.wgt.bend_radius*np.tan((self.angle)/2.0))
        angle_x_dist = 2.0*(dlx)*np.cos(self.angle)
        angle_y_dist = 2.0*(dlx)*np.sin(self.angle)
        distx = 4*dlx+2*angle_x_dist+self.length
        disty = (2*abs(angle_y_dist) + self.gap + (self.width_top+self.width_bot)/2.0)*self.parity

        if self.parity==1:
            shift = 0
        elif self.parity==-1:
            shift = (2*angle_y_dist + self.gap + (self.width_top+self.width_bot)/2.0)

        x01, y01 = self.port[0],self.port[1]+shift #shift to port location after rotation later

        """ Build the contra-DC from gdspy Path derivatives """
        wg_top = gdspy.Path(self.wgt.wg_width, (x01, y01))
        wg_top.turn(self.wgt.bend_radius, -self.angle, number_of_points=0.1, **self.wg_spec)
        wg_top.turn(self.wgt.bend_radius, self.angle, number_of_points=0.1, final_width=self.width_top, **self.wg_spec)
        wg_top.segment(self.length, **self.wg_spec)
        wg_top.turn(self.wgt.bend_radius, self.angle, number_of_points=0.1, final_width=self.wgt.wg_width, **self.wg_spec)
        wg_top.turn(self.wgt.bend_radius, -self.angle, number_of_points=0.1, **self.wg_spec)

        wg_top_clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, (x01, y01))
        wg_top_clad.turn(self.wgt.bend_radius, -self.angle, number_of_points=0.1, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, self.angle, number_of_points=0.1, final_width=self.width_top+2*self.wgt.clad_width, **self.clad_spec)
        wg_top_clad.segment(self.length, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, self.angle, number_of_points=0.1, final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, -self.angle, number_of_points=0.1, **self.clad_spec)

        x02, y02 = self.port[0], self.port[1] - (2*angle_y_dist + self.gap + (self.width_top+self.width_bot)/2.0) + shift

        wg_bot = gdspy.Path(self.wgt.wg_width, (x02, y02))
        wg_bot.turn(self.wgt.bend_radius, self.angle, number_of_points=0.1, **self.wg_spec)
        wg_bot.turn(self.wgt.bend_radius, -self.angle, number_of_points=0.1, final_width=self.width_bot, **self.wg_spec)
        wg_bot.segment(self.length, **self.wg_spec)
        wg_bot.turn(self.wgt.bend_radius, -self.angle, number_of_points=0.1, final_width=self.wgt.wg_width, **self.wg_spec)
        wg_bot.turn(self.wgt.bend_radius, self.angle, number_of_points=0.1, **self.wg_spec)

        wg_bot_clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, (x02, y02))
        wg_bot_clad.turn(self.wgt.bend_radius, self.angle, number_of_points=0.1, **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, -self.angle, number_of_points=0.1, final_width=2*self.wgt.clad_width+self.width_bot, **self.clad_spec)
        wg_bot_clad.segment(self.length, **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, -self.angle, number_of_points=0.1, final_width=2*self.wgt.clad_width+self.wgt.wg_width, **self.clad_spec)
        wg_bot_clad.turn(self.wgt.bend_radius, self.angle, number_of_points=0.1, **self.clad_spec)

        """ Now add the periodic PhC components """
        num_blocks = (self.length)//self.period
        blockx = self.period*self.dc
        startx = self.port[0] + distx/2.0 -(num_blocks-1)*self.period/2.0 - blockx/2.0
        y0 = self.port[1] - angle_y_dist - self.gap/2.0 - self.width_top/2.0 + shift
        block_list = []
        for i in range(int(num_blocks)):
            x = startx + i*self.period
            block_list.append(gdspy.Rectangle((x, y0-self.gap/2.0), (x+blockx, y0-self.gap/2.0+self.dw_bot), **self.wg_spec))
            block_list.append(gdspy.Rectangle((x, y0+self.gap/2.0), (x+blockx, y0+self.gap/2.0-self.dw_top), **self.wg_spec))

        """ And add the 'fins' if self.fins==True """
        if self.fins:
            num_fins = self.wgt.wg_width//(2*self.fin_size[1])
            x0, y0 = x01, y01 - num_fins*(2*self.fin_size[1])/2.0 + self.fin_size[1]/2.0
            xend = x01+distx
            for i in range(int(num_fins)):
                y = y0 + i*2*self.fin_size[1]
                block_list.append(gdspy.Rectangle((x0, y+shift), (x0+self.fin_size[0], y+self.fin_size[1]+shift), **self.fin_spec))
                block_list.append(gdspy.Rectangle((x0, y-disty+shift), (x0+self.fin_size[0], y-disty+self.fin_size[1]+shift), **self.fin_spec))
                block_list.append(gdspy.Rectangle((x0+distx-self.fin_size[0], y+shift), (x0+distx, y+self.fin_size[1]+shift), **self.fin_spec))
                block_list.append(gdspy.Rectangle((x0+distx-self.fin_size[0], y-disty+shift), (x0+distx, y-disty+self.fin_size[1]+shift), **self.fin_spec))

        if self.direction=="WEST":
            angle = np.pi
            self.portlist_output_straight = (self.port[0]-distx, self.port[1])
            self.portlist_output_cross = (self.port[0]-distx, self.port[1] + disty)
            self.portlist_input_cross = (self.port[0], self.port[1] + disty)
        elif self.direction=="SOUTH":
            angle = -np.pi/2.0
            self.portlist_output_straight = (self.port[0], self.port[1]-distx)
            self.portlist_output_cross = (self.port[0]-disty, self.port[1]-distx)
            self.portlist_input_cross = (self.port[0]-disty, self.port[1])
        elif self.direction=="EAST":
            angle = 0
            self.portlist_output_straight = (self.port[0]+distx, self.port[1])
            self.portlist_output_cross = (self.port[0]+distx, self.port[1]-disty)
            self.portlist_input_cross = (self.port[0], self.port[1]-disty)
        elif self.direction=="NORTH":
            angle = np.pi/2.0
            self.portlist_output_straight = (self.port[0], self.port[1]+distx)
            self.portlist_output_cross = (self.port[0]+disty, self.port[1]+distx)
            self.portlist_input_cross = (self.port[0]+disty, self.port[1])
        elif isinstance(self.direction, float):
            angle = self.direction
            self.portlist_output_straight = (self.port[0]+distx*np.cos(self.direction), self.port[1]+distx*np.sin(self.direction))
            self.portlist_input_cross = (self.port[0]-(-disty)*np.sin(self.direction), self.port[1]+(-disty)*np.cos(self.direction))
            self.portlist_output_cross = (self.port[0]-(-disty)*np.sin(self.direction)+distx*np.cos(self.direction), self.port[1]+(-disty)*np.cos(self.direction)+distx*np.sin(self.direction))

        wg_top.rotate(angle, self.port)
        wg_bot.rotate(angle, self.port)
        wg_top_clad.rotate(angle, self.port)
        wg_bot_clad.rotate(angle, self.port)
        self.add(wg_top)
        self.add(wg_bot)
        self.add(wg_top_clad)
        self.add(wg_bot_clad)
        for block in block_list:
            block.rotate(angle, self.port)
            self.add(block)

    def build_ports(self):
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
    wgt = WaveguideTemplate(wg_width=2.0, bend_radius=50, resist='+')

    # wg1=Waveguide([(0,0), (0, 20)], wgt)
    # tk.add(top, wg1)

    contradc_wgt = WaveguideTemplate(bend_radius=50, resist='+', wg_layer=3, wg_datatype=0)

    # cdc = ContraDirectionalCoupler(wgt, length=30.0, gap=1.0, period=0.5, dc=0.5, angle=np.pi/12.0, width_top=3.0, width_bot=2.0, input_bot=True, **wg1.portlist["output"])
    # tk.add(top, cdc)

    # wg1=Waveguide([(0,0), (0,100), (50,200), (50, 215)], wgt)
    wg1=Waveguide([(0,0), (100,0)], wgt)
    tk.add(top, wg1)

    cdc2 = ContraDirectionalCoupler(wgt, length=30.0, gap=1.0, period=0.5, dc=0.5, angle=np.pi/12.0, width_top=3.0, width_bot=2.0, dw_top=0.4, dw_bot=0.2, input_bot=False, contradc_wgt=contradc_wgt, fins=True, **wg1.portlist["output"])
    tk.add(top, cdc2)

    # x0,y0 = cdc2.portlist["input_bot"]["port"]
    # wg2=Waveguide([(x0,y0), (x0,y0-15), (x0+50,y0-115), (x0+50, y0-215)], wgt)
    # tk.add(top, wg2)

    # dc1 = ContraDirectionalCoupler(wgt, length=30.0, gap=0.5, period=0.220, dc=0.5, angle=np.pi/6.0, width_top=2.0, width_bot=0.75, input_bot=False, **wg1.portlist["output"])
    # dc2 = ContraDirectionalCoupler(wgt, length=30.0, gap=0.5, period=0.220, dc=0.5, angle=np.pi/6.0, width_top=2.0, width_bot=0.75, input_bot=True, **dc1.portlist["output_top"])
    # dc3 = ContraDirectionalCoupler(wgt, length=30.0, gap=0.5, period=0.220, dc=0.5, angle=np.pi/6.0, width_top=2.0, width_bot=0.75, input_bot=False, **dc1.portlist["output_bot"])
    # dc4 = ContraDirectionalCoupler(wgt, length=30.0, gap=0.5, period=0.220, dc=0.5, angle=np.pi/6.0, width_top=2.0, width_bot=0.75, input_bot=False, **dc2.portlist["output_bot"])
    # dc5 = ContraDirectionalCoupler(wgt, length=30.0, gap=0.5, period=0.220, dc=0.5, angle=np.pi/6.0, width_top=2.0, width_bot=0.75, input_bot=True, **dc2.portlist["output_top"])
    # dc6 = ContraDirectionalCoupler(wgt, length=30.0, gap=0.5, period=0.220, dc=0.5, angle=np.pi/6.0, width_top=2.0, width_bot=0.75, input_bot=False, **dc3.portlist["output_bot"])
    # tk.add(top, dc1)
    # tk.add(top, dc2)
    # tk.add(top, dc3)
    # tk.add(top, dc4)
    # tk.add(top, dc5)
    # tk.add(top, dc6)

    # gdspy.LayoutViewer(cells=top)
    gdspy.write_gds('contradc.gds', unit=1.0e-6, precision=1.0e-9)

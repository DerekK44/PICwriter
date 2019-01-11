# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk
from picwriter.components.waveguide import Waveguide

class SWGContraDirectionalCoupler(gdspy.Cell):
    """ SWG Contra-Directional Coupler Cell class (subclass of gdspy.Cell).

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length** (float): Length of the coupling region.
           * **gap** (float): Distance between the two waveguides.
           * **period** (float): Period of the grating.
           * **dc** (float): Duty cycle of the grating. Must be between 0 and 1.
           * **taper_length** (float): Length of the taper region
           * **w_phc_bot** (float): Width of the thin section of the bottom waveguide.  w_phc_bot = 0 corresponds to disconnected periodic blocks.

        Keyword Args:
           * **top_angle** (float): Angle in radians (between 0 and pi/2) at which the *top* waveguide bends towards the coupling region.  Default=pi/6.
           * **width_top** (float): Width of the top waveguide in the coupling region.  Defaults to the WaveguideTemplate wg width.
           * **width_bot** (float): Width of the bottom waveguide in the coupling region.  Defaults to the WaveguideTemplate wg width.
           * **extra_swg_length** (float): Extra length of SWG waveguide between coupling region and taper.  Default=0.0.
           * **input_bot** (boolean): If `True`, will make the default input the bottom waveguide (rather than the top).  Default=`False`
           * **apodization_top** (boolean): If `True`, will apodize the *coupling_gap* distance for the top waveguide using a Gaussian profile.
           * **apodization_far_dist** (float): If `apodization_top`=`True`, then this parameter sets how far away the coupling gap *starts*.  The minimum coupling gap is defined by `gap`.  Defaults to 1um.
           * **apodization_curv** (float): If `apodization_top`=`True`, then this parameter sets the curvature for the Gaussian apodization.  Defaults to (10.0/length)**2.
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
    def __init__(self, wgt, length, gap, period, dc, taper_length, w_phc_bot,
                 top_angle=np.pi/6.0, width_top=None, width_bot=None, extra_swg_length=0.0,
                 input_bot=False, apodization_top=False, apodization_far_dist=1.0,
                 apodization_curv=None, fins=False, fin_size=(0.2, 0.05), contradc_wgt=None,
                 port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "SWGContraDC--"+str(uuid.uuid4()))

        self.portlist = {}

        self.port = port
        self.direction = direction

        if top_angle > np.pi/2.0 or top_angle < 0:
            raise ValueError("Warning! Improper top_angle specified ("+str(top_angle)+").  Must be between 0 and pi/2.0.")
        self.top_angle = top_angle

        if dc > 1.0 or dc < 0.0:
            raise ValueError("Warning!  Dutycycle must be between 0 and 1.  Received dc="+str(dc)+" instead.")
        if 2*taper_length > length:
            raise ValueError("Warning! 2*taper_length must be greater than the total coupling region length.")

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

        self.length = length
        self.gap = gap
        self.dc = dc
        self.taper_length = taper_length
        self.w_phc_bot = w_phc_bot
        self.period = period
        self.extra_swg_length = extra_swg_length

        self.apodization_top = apodization_top
        self.apodization_far_dist = apodization_far_dist
        self.apodization_curv = (10.0/length)**2 if apodization_curv==None else apodization_curv
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
        if self.apodization_top:
            min_gap = self.gap
            self.gap = self.apodization_far_dist

        angle_x_dist = 2*self.wgt.bend_radius*np.sin(self.top_angle)
        if self.extra_swg_length + self.taper_length > angle_x_dist:
            raise ValueError("Warning! taper_length + extra_swg_length is greater than the top-waveguide x-length.  You can fix this by increasing bend_radius or top_angle.")

        angle_y_dist_top = 2*self.wgt.bend_radius*(1-np.cos(self.top_angle))
        distx = 2*angle_x_dist + self.length
        disty = (abs(angle_y_dist_top) + self.gap + (self.width_top+self.width_bot)/2.0)*self.parity

        if self.parity==1:
            shift = 0
        elif self.parity==-1:
            shift = (angle_y_dist_top + self.gap + (self.width_top+self.width_bot)/2.0)

        x01, y01 = self.port[0],self.port[1]+shift #shift to port location after rotation later

        """ Build the contra-DC from gdspy Path derivatives """
        """ First the top waveguide """

        def gaussian_top(t): #Gaussian path only used for apodized coupler gaps, t varies from 0 to 1
            x = x01 + angle_x_dist + t*(self.length)
            xcent = x01 + angle_x_dist + 0.5*self.length
            y_gauss_start = y01 - angle_y_dist_top
            y_gauss_mag = self.gap - min_gap/2.0
            y = y_gauss_start - y_gauss_mag*np.exp(-self.apodization_curv*(x - xcent)**2)
            return (x, y)

        wg_top = gdspy.Path(self.wgt.wg_width, (x01, y01))
        wg_top.turn(self.wgt.bend_radius, -self.top_angle, number_of_points=0.1, final_width=self.width_top, **self.wg_spec)
        wg_top.turn(self.wgt.bend_radius, self.top_angle, number_of_points=0.1, **self.wg_spec)
        if self.apodization_top:
            wg_apod = gdspy.Path(self.width_top, (0, 0))
            wg_apod.direction='+x'
            wg_apod.parametric(gaussian_top, number_of_evaluations=600, **self.wg_spec)# **self.fin_spec)
            wg_top.x, wg_top.y = wg_apod.x, wg_apod.y
        else:
            wg_top.segment(self.length, **self.wg_spec)
        wg_top.turn(self.wgt.bend_radius, self.top_angle, number_of_points=0.1, **self.wg_spec)
        wg_top.turn(self.wgt.bend_radius, -self.top_angle, number_of_points=0.1, final_width=self.wgt.wg_width, **self.wg_spec)

        wg_top_clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, (x01, y01))
        wg_top_clad.turn(self.wgt.bend_radius, -self.top_angle, number_of_points=0.1, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, self.top_angle, number_of_points=0.1, final_width=self.width_top+2*self.wgt.clad_width, **self.clad_spec)
        wg_top_clad.segment(self.length, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, self.top_angle, number_of_points=0.1, final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)
        wg_top_clad.turn(self.wgt.bend_radius, -self.top_angle, number_of_points=0.1, **self.clad_spec)


        """ Add the bottom waveguide
        """
        x02, y02 = self.port[0], self.port[1] - (angle_y_dist_top + self.gap + (self.width_top+self.width_bot)/2.0) + shift
        wg_bot = gdspy.Path(self.wgt.wg_width, (x02, y02))
        if self.w_phc_bot > 1E-6:
            wg_bot.segment(angle_x_dist-self.taper_length-self.extra_swg_length, final_width=self.width_bot, **self.wg_spec)
            wg_bot.segment(self.taper_length, final_width=self.w_phc_bot, **self.wg_spec)
            wg_bot.segment(self.length+2*self.extra_swg_length, **self.wg_spec)
            wg_bot.segment(self.taper_length, final_width=self.width_bot, **self.wg_spec)
            wg_bot.segment(angle_x_dist-self.taper_length-self.extra_swg_length, final_width=self.wgt.wg_width, **self.wg_spec)
        else: # Unconnected bottom SWG waveguides (2 paths)
            wg_bot.segment(angle_x_dist-self.taper_length-self.extra_swg_length, final_width=self.width_bot, **self.wg_spec)
            wg_bot.segment(self.taper_length, final_width=0.0, **self.wg_spec)
            wg_bot2 = gdspy.Path(self.wgt.wg_width, (x02+distx, y02))
            wg_bot2.direction='-x'
            wg_bot2.segment(angle_x_dist-self.taper_length-self.extra_swg_length, final_width=self.width_bot, **self.wg_spec)
            wg_bot2.segment(self.taper_length, final_width=0.0, **self.wg_spec)

        wg_bot_clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, (x02, y02))
        wg_bot_clad.segment(angle_x_dist, final_width=self.width_bot+2*self.wgt.clad_width, **self.clad_spec)
        wg_bot_clad.segment(self.length, **self.clad_spec)
        wg_bot_clad.segment(angle_x_dist, final_width=self.wgt.wg_width+2*self.wgt.clad_width, **self.clad_spec)

        """ Now add the periodic PhC components """
        num_blocks = (self.length+2*(self.taper_length+self.extra_swg_length))//self.period
        blockx = self.period*self.dc
        startx = self.port[0] + distx/2.0 - (num_blocks-1)*self.period/2.0 - blockx/2.0
        y0 = self.port[1] - angle_y_dist_top - self.gap/2.0 - self.width_top/2.0 + shift
        block_list = []
        for i in range(int(num_blocks)):
            x = startx + i*self.period
            if abs(self.w_phc_bot-self.width_bot)>1E-6:
                block_list.append(gdspy.Rectangle((x, y0-self.gap/2.0), (x+blockx, y0-self.gap/2.0-self.width_bot), **self.wg_spec))

        """ And add the 'fins' if self.fins==True """
        if self.fins:
            num_fins = self.wgt.wg_width//(2*self.fin_size[1])
            x0, y0 = self.port[0], self.port[1] - num_fins*(2*self.fin_size[1])/2.0 + self.fin_size[1]/2.0
            for i in range(int(num_fins)):
                y = y0 + i*2*self.fin_size[1]
                block_list.append(gdspy.Rectangle((x0, y), (x0+self.fin_size[0], y+self.fin_size[1]), **self.fin_spec))
                block_list.append(gdspy.Rectangle((x0, y-disty), (x0+self.fin_size[0], y-disty+self.fin_size[1]), **self.fin_spec))
                block_list.append(gdspy.Rectangle((x0+distx-self.fin_size[0], y), (x0+distx, y+self.fin_size[1]), **self.fin_spec))
                block_list.append(gdspy.Rectangle((x0+distx-self.fin_size[0], y-disty), (x0+distx, y-disty+self.fin_size[1]), **self.fin_spec))

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
        if self.w_phc_bot <= 1E-6: # Unconnected bottom SWG waveguides (2 paths)
            wg_bot2.rotate(angle, self.port)
            self.add(wg_bot2)
        if self.apodization_top:
            wg_apod.rotate(angle, self.port)
            self.add(wg_apod)
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

    contradc_wgt = WaveguideTemplate(bend_radius=50, resist='+', wg_layer=3, wg_datatype=0)

    wg1=Waveguide([(0,0), (100,0)], wgt)
    tk.add(top, wg1)

    cdc = SWGContraDirectionalCoupler(wgt, length=50.0, gap=0.2, period=0.5, dc=0.5, taper_length=5.0,
                                      w_phc_bot=0.0,
                                      apodization_top=True,
                                      apodization_far_dist=1.0,
                                      apodization_curv=(6.0/50.0)**2,
                                      top_angle=np.pi/8,
                                      extra_swg_length=10.0,
                                      width_top=2.0,
                                      width_bot=1.0,
                                      input_bot=False,
                                      contradc_wgt=contradc_wgt,
                                      fins=True,
                                      **wg1.portlist["output"])
#    cdc = SWGContraDirectionalCoupler(wgt, length=40.0, gap=0.5, period=0.5, dc=0.5, taper_length=5.0,
#                                      w_phc_bot=0.0,
#                                      apodization_top=False,
#                                      top_angle=np.pi/8,
#                                      width_top=2.0,
#                                      width_bot=1.0,
#                                      extra_swg_length=10.0,
#                                      input_bot=True,
#                                      contradc_wgt=contradc_wgt,
#                                      fins=True,
#                                      **wg1.portlist["output"])
    tk.add(top, cdc)

#    gdspy.LayoutViewer(cells=top)
    gdspy.write_gds('swgcontradc.gds', unit=1.0e-6, precision=1.0e-9)

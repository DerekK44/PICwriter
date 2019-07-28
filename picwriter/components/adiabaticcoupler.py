# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk
from picwriter.components.waveguide import Waveguide
from picwriter.components.bbend import BBend
from picwriter.components.taper import Taper

class AdiabaticCoupler(tk.Component):
    """ Adiabatic Coupler Cell class.  Design based on asymmetric adiabatic 3dB coupler designs, such as those from https://doi.org/10.1364/CLEO.2010.CThAA2, https://doi.org/10.1364/CLEO_SI.2017.SF1I.5, and https://doi.org/10.1364/CLEO_SI.2018.STh4B.4.  Uses Bezier curves for the input, with poles set to half of the x-length of the S-bend.

    In this design, Region I is the first half of the input S-bend waveguide where the input waveguides widths taper by +dw and -dw, Region II is the second half of the S-bend waveguide with constant, unbalanced widths, Region III is the region where the two asymmetric waveguides gradually come together, Region IV is the coupling region where the waveguides taper back to the original width at a fixed distance from one another, and Region IV is the  output S-bend waveguide.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length1** (float): Length of the region that gradually brings the two assymetric waveguides together.  In this region the waveguide widths gradually change to be different by `dw`.
           * **length2** (float): Length of the coupling region, where the asymmetric waveguides gradually become the same width.
           * **length3** (float): Length of the output region where the two waveguides separate.
           * **wg_sep** (float): Distance between the two waveguides, center-to-center, in the coupling region (Region 2).
           * **input_wg_sep** (float): Separation of the two waveguides at the input, center-to-center.
           * **output_wg_sep** (float): Separation of the two waveguides at the output, center-to-center.
           * **dw** (float): Change in waveguide width.  In Region 1, the top arm tapers to the waveguide width+dw/2.0, bottom taper to width-dw/2.0.

        Keyword Args:
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
                 length3,
                 wg_sep, 
                 input_wg_sep,
                 output_wg_sep,
                 dw, 
                 port=(0,0), 
                 direction='EAST'):
        tk.Component.__init__(self, "AdiabaticCoupler", locals())

        self.portlist = {}

        self.port = port
        self.direction = direction

        self.length1 = length1
        self.length2 = length2
        self.length3 = length3
        self.wg_sep = wg_sep
        self.input_wg_sep = input_wg_sep
        self.output_wg_sep = output_wg_sep
        self.dw = dw
        self.wgt = wgt
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.yc = -input_wg_sep/2.0

        self.portlist_input_top = (0,0)
        self.portlist_input_bot = (0,-input_wg_sep)
        self.portlist_output_top = (length1+length2+length3, self.yc + self.output_wg_sep/2.0)
        self.portlist_output_bot = (length1+length2+length3, self.yc - self.output_wg_sep/2.0)

        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell

        """ Add the Region 1 S-bend waveguides with Bezier curves """
        poles = [(0,0),
                 (self.length1/2.0, 0),
                 (self.length1/2.0, self.yc + self.wg_sep/2.0),
                 (self.length1, self.yc + self.wg_sep/2.0)]
        input_top_bezier = BBend(self.wgt, poles, end_width=self.wgt.wg_width+self.dw/2.0)
        self.add(input_top_bezier)
        
        poles = [(0,-self.input_wg_sep),
                 (self.length1/2.0, -self.input_wg_sep),
                 (self.length1/2.0, self.yc - self.wg_sep/2.0),
                 (self.length1, self.yc - self.wg_sep/2.0)]
        input_bot_bezier = BBend(self.wgt, poles, end_width=self.wgt.wg_width-self.dw/2.0)
        self.add(input_bot_bezier)

        """ Add the Region 2 tapered waveguide part """
        taper_top = Taper(self.wgt, self.length2, end_width=self.wgt.wg_width, start_width=self.wgt.wg_width+self.dw/2.0, **input_top_bezier.portlist["output"])
        self.add(taper_top)
        taper_bot = Taper(self.wgt, self.length2, end_width=self.wgt.wg_width, start_width=self.wgt.wg_width-self.dw/2.0, **input_bot_bezier.portlist["output"])
        self.add(taper_bot)
        
        """ Add the Region 3 S-bend output waveguides with Bezier curves """
        poles = [(self.length1+self.length2, self.yc+self.wg_sep/2.0),
                 (self.length1+self.length2+self.length3/2.0, self.yc+self.wg_sep/2.0),
                 (self.length1+self.length2+self.length3/2.0, self.yc + self.output_wg_sep/2.0),
                 (self.length1+self.length2+self.length3, self.yc + self.output_wg_sep/2.0)]
        output_top_bezier = BBend(self.wgt, poles)
        self.add(output_top_bezier)
        
        poles = [(self.length1+self.length2, self.yc-self.wg_sep/2.0),
                 (self.length1+self.length2+self.length3/2.0, self.yc-self.wg_sep/2.0),
                 (self.length1+self.length2+self.length3/2.0, self.yc - self.output_wg_sep/2.0),
                 (self.length1+self.length2+self.length3, self.yc - self.output_wg_sep/2.0)]
        output_bot_bezier = BBend(self.wgt, poles)
        self.add(output_bot_bezier)
        
    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input_top"] = {'port':self.portlist_input_top, 'direction':'WEST'}
        self.portlist["input_bot"] = {'port':self.portlist_input_bot, 'direction':'WEST'}
        self.portlist["output_top"] = {'port':self.portlist_output_top, 'direction':'EAST'}
        self.portlist["output_bot"] = {'port':self.portlist_output_bot, 'direction':'EAST'}

if __name__ == "__main__":
    from . import *
    from picwriter.components.waveguide import WaveguideTemplate
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(wg_width=0.5, bend_radius=100, resist='+')

    wg1=Waveguide([(0,0), (0.1,0)], wgt)
    tk.add(top, wg1)

    ac = AdiabaticCoupler(wgt, 
                          length1=30.0, 
                          length2=50.0,
                          length3=20.0,
                          wg_sep=1.0,
                          input_wg_sep = 3.0,
                          output_wg_sep = 3.0,
                          dw=0.1,
                          **wg1.portlist["output"])
    tk.add(top, ac)
    
    ac2 = AdiabaticCoupler(wgt, 
                          length1=20.0, 
                          length2=50.0,
                          length3=30.0,
                          wg_sep=1.0,
                          input_wg_sep = 3.0,
                          output_wg_sep = 3.0,
                          dw=0.1,
                          **ac.portlist["output_bot"])
    tk.add(top, ac2)
    
    for p in ac.portlist.keys():
        print(str(p)+": "+str(ac.portlist[p]['port']))

    gdspy.LayoutViewer()
    gdspy.write_gds('ac.gds', unit=1.0e-6, precision=1.0e-9)

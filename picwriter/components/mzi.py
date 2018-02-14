# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk
from picwriter.components.mmi1x2 import MMI1x2
from picwriter.components.waveguide import Waveguide
from picwriter.components.electrical import MetalRoute

class MachZehnder(gdspy.Cell):
    """ Standard Mach-Zehnder Cell class with thermo-optic option (subclass of gdspy.Cell).  It is possible to generate your own Mach-Zehnder from the waveguide and MMI1x2 classes, but this class is simply a shorthand (with some extra type-checking).  Defaults to a *balanced* Mach Zehnder.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **MMIlength** (float): Length of the 1x2 MMI region (along direction of propagation)
           * **MMIwidth** (float): Width of the 1x2 MMI region (perpendicular to direction of propagation).

        Keyword Args:
           * **MMItaper_width** (float): Maximum width of the 1x2 MMI taper region (default = wg_width from wg_template).  Defaults to None (waveguide width).
           * **MMItaper_length** (float): Length of the taper leading up to the 1x2 MMI.  Defaults to None (taper_length=20).
           * **MMIwg_sep** (float): Separation between waveguides on the 2-port side of the 1x2 MMI (defaults to width/3.0)
           * **arm1** (float): Additional length of the top arm (when going `'EAST'`).  Defaults to zero.
           * **arm2** (float): Additional length of the bottom arm (when going `'EAST'`).  Defaults to zero.
           * **heater** (boolean): If true, adds heater on-top of one MZI arm.  Defaults to False.
           * **heater_length** (float): Specifies the length of the heater along the waveguide. Doesn't include the length of the 180 degree bend.  Defaults to 400.0.
           * **mt** (MetalTemplate): If 'heater' is true, must specify a Metal Template that defines heater & heater cladding layers.
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the taper will point *towards*, must be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.  Defaults to `'EAST'`

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}
           * portlist['heater_top_in'] = {'port', (x3, y3), 'direction': 'dir3'}
           * portlist['heater_top_out'] = {'port', (x4, y4), 'direction': 'dir4'}
           * portlist['heater_bot_in'] = {'port', (x5, y5), 'direction': 'dir5'}
           * portlist['heater_bot_out'] = {'port', (x6, y6), 'direction': 'dir6'}

        Where in the above (x1,y1) is the input port, (x2, y2) is the top output port, and the directions are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.
        Four additional ports are created for the heaters if the `heater` argument is True.  Metals are not generated, but should be connected to the specified 'heater' ports.

    """
    def __init__(self, wgt, MMIlength, MMIwidth, MMItaper_width=None, MMItaper_length=None, MMIwg_sep=None,
                 arm1=0, arm2=0, heater=False, heater_length=400, mt=None, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "MZI--"+str(uuid.uuid4()))

        self.portlist = {}

        self.wgt = wgt
        self.arm1 = arm1
        self.arm2 = arm2

        self.MMIlength = MMIlength
        self.MMIwidth = MMIwidth
        self.MMItaper_width = wgt.wg_width if MMItaper_width==None else MMItaper_width
        self.MMItaper_length = 20 if MMItaper_length==None else MMItaper_length
        self.MMIwg_sep = MMIwidth/3.0 if MMIwg_sep==None else MMIwg_sep

        self.mmilength = self.MMIlength + 2*self.MMItaper_length

        self.heater = heater
        if heater:
            self.heater_length = heater_length
            self.mt = mt
        else:
            self.heater_length = 0

        self.port = port
        self.direction = direction

        self.build_cell()
        self.build_ports()

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # then add it to the Cell

        mmi1 = MMI1x2(self.wgt, self.MMIlength, self.MMIwidth, self.MMItaper_width, self.MMItaper_length, self.MMIwg_sep,
                      port=(0,0), direction='EAST')
        mmi2 = MMI1x2(self.wgt, self.MMIlength, self.MMIwidth, self.MMItaper_width, self.MMItaper_length, self.MMIwg_sep,
                      port=(0+2*self.mmilength+4*self.wgt.bend_radius, 0), direction='WEST')

        (x0, y0) = mmi1.portlist["output_top"]["port"]
        trace1 = [(x0, y0),
                  (x0+self.wgt.bend_radius, y0),
                  (x0+self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y0),
                  (x0+4*self.wgt.bend_radius, y0)]
        wg_top = Waveguide(trace1, self.wgt)

        (x1, y1) = mmi1.portlist["output_bot"]["port"]
        trace2 = [(x1, y1),
                  (x1+self.wgt.bend_radius, y1),
                  (x1+self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y1),
                  (x1+4*self.wgt.bend_radius, y1)]
        wg_bot = Waveguide(trace2, self.wgt)

        if self.heater:
            heater_trace1 = [(x0+self.wgt.bend_radius, y0+self.arm1/2.0+self.wgt.bend_radius),
                             (x0+self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                             (x0+3*self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                             (x0+3*self.wgt.bend_radius, y0+self.arm1/2.0+self.wgt.bend_radius)]
            heater_top = MetalRoute(heater_trace1, self.mt)
            heater_trace2 = [(x0+self.wgt.bend_radius, y1-self.arm2/2.0-self.wgt.bend_radius),
                             (x0+self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                             (x0+3*self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                             (x0+3*self.wgt.bend_radius, y1-self.arm2/2.0-self.wgt.bend_radius)]
            heater_bot = MetalRoute(heater_trace2, self.mt)

        if self.direction=='EAST':
            angle=0
            self.port_output = (self.port[0]+2*self.mmilength+4*self.wgt.bend_radius, self.port[1])
            self.htr_top_in_dir ='WEST'
            self.htr_top_out_dir = 'EAST'
            self.htr_bot_in_dir = 'WEST'
            self.htr_bot_out_dir = 'EAST'
        elif self.direction=='NORTH':
            angle=90
            self.port_output = (self.port[0], self.port[1]+2*self.mmilength+4*self.wgt.bend_radius)
            self.htr_top_in_dir ='SOUTH'
            self.htr_top_out_dir = 'NORTH'
            self.htr_bot_in_dir = 'SOUTH'
            self.htr_bot_out_dir = 'NORTH'
        elif self.direction=='WEST':
            angle=180
            self.port_output = (self.port[0]-2*self.mmilength-4*self.wgt.bend_radius, self.port[1])
            self.htr_top_in_dir ='EAST'
            self.htr_top_out_dir = 'WEST'
            self.htr_bot_in_dir = 'EAST'
            self.htr_bot_out_dir = 'WEST'
        elif self.direction=='SOUTH':
            angle=-90
            self.port_output = (self.port[0], self.port[1]-2*self.mmilength-4*self.wgt.bend_radius)
            self.htr_top_in_dir ='NORTH'
            self.htr_top_out_dir = 'SOUTH'
            self.htr_bot_in_dir = 'NORTH'
            self.htr_bot_out_dir = 'SOUTH'

        htr_top_in = (x0+self.wgt.bend_radius, y0+self.arm1/2.0+self.wgt.bend_radius+self.mt.width/2.0)
        htr_top_out = (x0+3*self.wgt.bend_radius, y0+self.arm1/2.0+self.wgt.bend_radius+self.mt.width/2.0)
        htr_bot_in = (x0+self.wgt.bend_radius, y1-self.arm2/2.0-self.wgt.bend_radius-self.mt.width/2.0)
        htr_bot_out = (x0+3*self.wgt.bend_radius, y1-self.arm2/2.0-self.wgt.bend_radius-self.mt.width/2.0)
        R = np.array([[np.cos(angle*np.pi/180.0), -np.sin(angle*np.pi/180.0)],
                     [np.sin(angle*np.pi/180.0), np.cos(angle*np.pi/180.0)]])
        hti = np.dot(R, htr_top_in)
        hto = np.dot(R, htr_top_out)
        hbi = np.dot(R, htr_bot_in)
        hbo = np.dot(R, htr_bot_out)
        self.htr_top_in = (hti[0]+self.port[0], hti[1]+self.port[1])
        self.htr_top_out = (hto[0]+self.port[0], hto[1]+self.port[1])
        self.htr_bot_in = (hbi[0]+self.port[0], hbi[1]+self.port[1])
        self.htr_bot_out = (hbo[0]+self.port[0], hbo[1]+self.port[1])

        """ Add all the components """
        components = [mmi1, mmi2, wg_top, wg_bot, heater_top, heater_bot]
        for c in components:
            self.add(gdspy.CellReference(c, origin=self.port, rotation=angle))

    def build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}

        self.portlist["input"] = {'port':self.port, 'direction':tk.flip_direction(self.direction)}
        self.portlist["output"] = {'port':self.port_output, 'direction':self.direction}
        if self.heater:
            self.portlist["heater_top_in"] = {'port': self.htr_top_in, 'direction':self.htr_top_in_dir}
            self.portlist["heater_top_out"] = {'port': self.htr_top_out, 'direction':self.htr_top_out_dir}
            self.portlist["heater_bot_in"] = {'port': self.htr_bot_in, 'direction':self.htr_bot_in_dir}
            self.portlist["heater_bot_out"] = {'port': self.htr_bot_out, 'direction':self.htr_bot_out_dir}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')
    htr_mt = MetalTemplate(width=25, clad_width=25, bend_radius=wgt.bend_radius, resist='+', fab="ETCH", metal_layer=13, metal_datatype=0, clad_layer=14, clad_datatype=0)
    mt = MetalTemplate(width=25, clad_width=25, resist='+', fab="ETCH", metal_layer=11, metal_datatype=0, clad_layer=12, clad_datatype=0)

    wg_in = Waveguide([(0,0), (300,0)], wgt)
    tk.add(top, wg_in)
    mzi = MachZehnder(wgt, MMIlength=50, MMIwidth=10, MMItaper_width=2.0, MMIwg_sep=3, arm1=0, arm2=100, heater=True, heater_length=400, mt=htr_mt, **wg_in.portlist["output"])
    tk.add(top, mzi)
    wg_out = Waveguide([mzi.portlist["output"]["port"], (mzi.portlist["output"]["port"][0]+300, mzi.portlist["output"]["port"][1])], wgt)
    tk.add(top, wg_out)

    mt1=MetalRoute([mzi.portlist["heater_top_in"]["port"],
                    (mzi.portlist["heater_top_in"]["port"][0]-150, mzi.portlist["heater_top_in"]["port"][1]),
                    (mzi.portlist["heater_top_in"]["port"][0]-150, mzi.portlist["heater_top_in"]["port"][1]+200)], mt)
    mt2=MetalRoute([mzi.portlist["heater_top_out"]["port"],
                    (mzi.portlist["heater_top_out"]["port"][0]+150, mzi.portlist["heater_top_out"]["port"][1]),
                    (mzi.portlist["heater_top_out"]["port"][0]+150, mzi.portlist["heater_top_out"]["port"][1]+200)], mt)
    mt3=MetalRoute([mzi.portlist["heater_bot_in"]["port"],
                    (mzi.portlist["heater_bot_in"]["port"][0]-150, mzi.portlist["heater_bot_in"]["port"][1]),
                    (mzi.portlist["heater_bot_in"]["port"][0]-150, mzi.portlist["heater_bot_in"]["port"][1]-200)], mt)
    mt4=MetalRoute([mzi.portlist["heater_bot_out"]["port"],
                    (mzi.portlist["heater_bot_out"]["port"][0]+150, mzi.portlist["heater_bot_out"]["port"][1]),
                    (mzi.portlist["heater_bot_out"]["port"][0]+150, mzi.portlist["heater_bot_out"]["port"][1]-200)], mt)
    tk.add(top, mt1)
    tk.add(top, mt2)
    tk.add(top, mt3)
    tk.add(top, mt4)
    tk.add(top, Bondpad(mt, **mt1.portlist["output"]))
    tk.add(top, Bondpad(mt, **mt2.portlist["output"]))
    tk.add(top, Bondpad(mt, **mt3.portlist["output"]))
    tk.add(top, Bondpad(mt, **mt4.portlist["output"]))

    gdspy.LayoutViewer()
    # gdspy.write_gds('mzi.gds', unit=1.0e-6, precision=1.0e-9)

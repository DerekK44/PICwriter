# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk
from picwriter.components.mmi1x2 import MMI1x2
from picwriter.components.mmi2x2 import MMI2x2
from picwriter.components.waveguide import Waveguide
from picwriter.components.electrical import MetalRoute
from picwriter.components.directionalcoupler import DirectionalCoupler

class MachZehnder(gdspy.Cell):
    """ Mach-Zehnder Cell class with thermo-optic option (subclass of gdspy.Cell).  It is possible to generate your own Mach-Zehnder from the waveguide and MMI1x2 classes, but this class is simply a shorthand (with some extra type-checking).  Defaults to a *balanced* Mach Zehnder.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **MMIlength** (float): Length of the 1x2 MMI region (along direction of propagation)
           * **MMIwidth** (float): Width of the 1x2 MMI region (perpendicular to direction of propagation).

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6.
           * **MMItaper_width** (float): Maximum width of the 1x2 MMI taper region (default = wg_width from wg_template).  Defaults to None (waveguide width).
           * **MMItaper_length** (float): Length of the taper leading up to the 1x2 MMI.  Defaults to None (taper_length=20).
           * **MMIwg_sep** (float): Separation between waveguides on the 2-port side of the 1x2 MMI (defaults to width/3.0)
           * **arm1** (float): Additional length of the top arm (when going `'EAST'`).  Defaults to zero.
           * **arm2** (float): Additional length of the bottom arm (when going `'EAST'`).  Defaults to zero.
           * **heater** (boolean): If true, adds heater on-top of one MZI arm.  Defaults to False.
           * **heater_length** (float): Specifies the length of the heater along the waveguide. Doesn't include the length of the 180 degree bend.  Defaults to 400.0.
           * **mt** (MetalTemplate): If 'heater' is true, must specify a Metal Template that defines heater & heater cladding layers.
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians). Defaults to `'EAST'` (0 radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}
           * portlist['heater_top_in'] = {'port', (x3, y3), 'direction': 'dir3'}
           * portlist['heater_top_out'] = {'port', (x4, y4), 'direction': 'dir4'}
           * portlist['heater_bot_in'] = {'port', (x5, y5), 'direction': 'dir5'}
           * portlist['heater_bot_out'] = {'port', (x6, y6), 'direction': 'dir6'}

        Where in the above (x1,y1) is the input port, (x2, y2) is the output port, and the directions are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.
        Four additional ports are created for the heaters if the `heater` argument is True.  Metals are not generated, but should be connected to the specified 'heater' ports.

    """
    def __init__(self, wgt, MMIlength, MMIwidth, angle=np.pi/6.0, MMItaper_width=None, MMItaper_length=None, MMIwg_sep=None,
                 arm1=0, arm2=0, heater=False, heater_length=400, mt=None, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "MZI--"+str(uuid.uuid4()))

        self.portlist = {}

        self.wgt = wgt
        self.arm1 = arm1
        self.arm2 = arm2

        if angle > np.pi/2.0 or angle < 0:
            raise ValueError("Warning! Improper angle specified ("+str(angle)+").  Must be between 0 and pi/2.0.")
        self.angle = angle

        self.MMIlength = MMIlength
        self.MMIwidth = MMIwidth
        self.MMItaper_width = wgt.wg_width if MMItaper_width==None else MMItaper_width
        self.MMItaper_length = 20 if MMItaper_length==None else MMItaper_length
        self.MMIwg_sep = MMIwidth/3.0 if MMIwg_sep==None else MMIwg_sep

        angle_x_dist = 2*self.wgt.bend_radius*np.sin(self.angle)
#        angle_y_dist = 2*self.wgt.bend_radius*(1-np.cos(self.angle))
        self.mmilength = self.MMIlength + angle_x_dist + self.MMItaper_length

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

        mmi1 = MMI1x2(self.wgt, self.MMIlength, self.MMIwidth,
                      angle = self.angle,
                      taper_width=self.MMItaper_width,
                      taper_length=self.MMItaper_length,
                      wg_sep=self.MMIwg_sep,
                      port=(0,0), direction='EAST')
        mmi2 = MMI1x2(self.wgt, self.MMIlength, self.MMIwidth,
                      angle=self.angle,
                      taper_width=self.MMItaper_width,
                      taper_length=self.MMItaper_length,
                      wg_sep=self.MMIwg_sep,
                      port=(0+2*self.mmilength+4*self.wgt.bend_radius, 0), direction='WEST')

        y_end_top, y_end_bot = mmi2.portlist["output_top"]["port"][1], mmi2.portlist["output_bot"]["port"][1]

        (x0, y0) = mmi1.portlist["output_top"]["port"]
        trace1 = [(x0, y0),
                  (x0+self.wgt.bend_radius, y0),
                  (x0+self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y_end_bot),
                  (x0+4*self.wgt.bend_radius, y_end_bot)]
        wg_top = Waveguide(trace1, self.wgt)

        (x1, y1) = mmi1.portlist["output_bot"]["port"]
        trace2 = [(x1, y1),
                  (x1+self.wgt.bend_radius, y1),
                  (x1+self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y_end_top),
                  (x1+4*self.wgt.bend_radius, y_end_top)]
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

        totallen = 2*self.mmilength+4*self.wgt.bend_radius
        if self.direction=='EAST':
            angle=0
            self.port_output = (self.port[0]+totallen, self.port[1])
            self.htr_top_in_dir ='WEST'
            self.htr_top_out_dir = 'EAST'
            self.htr_bot_in_dir = 'WEST'
            self.htr_bot_out_dir = 'EAST'
        elif self.direction=='NORTH':
            angle=90
            self.port_output = (self.port[0], self.port[1]+totallen)
            self.htr_top_in_dir ='SOUTH'
            self.htr_top_out_dir = 'NORTH'
            self.htr_bot_in_dir = 'SOUTH'
            self.htr_bot_out_dir = 'NORTH'
        elif self.direction=='WEST':
            angle=180
            self.port_output = (self.port[0]-totallen, self.port[1])
            self.htr_top_in_dir ='EAST'
            self.htr_top_out_dir = 'WEST'
            self.htr_bot_in_dir = 'EAST'
            self.htr_bot_out_dir = 'WEST'
        elif self.direction=='SOUTH':
            angle=-90
            self.port_output = (self.port[0], self.port[1]-totallen)
            self.htr_top_in_dir ='NORTH'
            self.htr_top_out_dir = 'SOUTH'
            self.htr_bot_in_dir = 'NORTH'
            self.htr_bot_out_dir = 'SOUTH'
        elif isinstance(self.direction, float):
            angle = 180.0*self.direction/np.pi
            self.port_output = (self.port[0] + totallen*np.cos(self.direction), self.port[1] + totallen*np.sin(self.direction))
            self.htr_top_in_dir = self.direction + np.pi/2.0
            self.htr_top_out_dir = self.direction + 3*np.pi/2.0
            self.htr_bot_in_dir = self.direction + np.pi/2.0
            self.htr_bot_out_dir = self.direction + 3*np.pi/2.0

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

class MachZehnderSwitch1x2(gdspy.Cell):
    """ Standard Mach-Zehnder Optical Switch Cell class with heaters on each arm (subclass of gdspy.Cell).  It is possible to generate your own Mach-Zehnder from the waveguide and MMI1x2 classes, but this class is simply a shorthand (with some extra type-checking).  Defaults to a *balanced* Mach Zehnder.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **MMI1x2length** (float): Length of the 1x2 MMI region (along direction of propagation)
           * **MMI1x2width** (float): Width of the 1x2 MMI region (perpendicular to direction of propagation).
           * **MMI2x2length** (float): Length of the 2x2 MMI region (along direction of propagation)
           * **MMI2x2width** (float): Width of the 2x2 MMI region (perpendicular to direction of propagation).

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6.
           * **MMI1x2taper_width** (float): Maximum width of the 1x2 MMI taper region (default = wg_width from wg_template).  Defaults to None (waveguide width).
           * **MMI1x2taper_length** (float): Length of the taper leading up to the 1x2 MMI.  Defaults to None (taper_length=20).
           * **MMI1x2wg_sep** (float): Separation between waveguides on the 2-port side of the 1x2 MMI (defaults to width/3.0)
           * **MMI2x2taper_width** (float): Maximum width of the 2x2 MMI taper region (default = wg_width from wg_template).  Defaults to None (waveguide width).
           * **MMI2x2taper_length** (float): Length of the taper leading up to the 2x2 MMI.  Defaults to None (taper_length=20).
           * **MMI2x2wg_sep** (float): Separation between waveguides of the 2x2 MMI (defaults to width/3.0)
           * **arm1** (float): Additional length of the top arm (when going `'EAST'`).  Defaults to zero.
           * **arm2** (float): Additional length of the bottom arm (when going `'EAST'`).  Defaults to zero.
           * **heater** (boolean): If true, adds heater on-top of one MZI arm.  Defaults to False.
           * **heater_length** (float): Specifies the length of the heater along the waveguide. Doesn't include the length of the 180 degree bend.  Defaults to 400.0.
           * **mt** (MetalTemplate): If 'heater' is true, must specify a Metal Template that defines heater & heater cladding layers.
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the taper will point *towards*, must be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to `'EAST'` (0 radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output_top'] = {'port': (x2, y2), 'direction': 'dir2'}
           * portlist['output_bot'] = {'port': (x3, y3), 'direction': 'dir3'}
           * portlist['heater_top_in'] = {'port', (x4, y4), 'direction': 'dir4'}
           * portlist['heater_top_out'] = {'port', (x5, y5), 'direction': 'dir5'}
           * portlist['heater_bot_in'] = {'port', (x6, y6), 'direction': 'dir6'}
           * portlist['heater_bot_out'] = {'port', (x7, y7), 'direction': 'dir7'}

        Where in the above (x1,y1) is the input port, (x2, y2) is the top output port, (x3, y3) is the bottom output port, and the directions are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.
        Four additional ports are created for the heaters if the `heater` argument is True.  Metals are not generated, but should be connected to the specified 'heater' ports.

    """
    def __init__(self, wgt, MMI1x2length, MMI1x2width, MMI2x2length, MMI2x2width, angle=np.pi/6.0, MMI1x2taper_width=None,
                 MMI1x2taper_length=None, MMI1x2wg_sep=None, MMI2x2taper_width=None, MMI2x2taper_length=None, MMI2x2wg_sep=None,
                 arm1=0, arm2=0, heater=False, heater_length=400, mt=None, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "MZISwitch1x2--"+str(uuid.uuid4()))

        self.portlist = {}

        self.wgt = wgt
        self.arm1 = arm1
        self.arm2 = arm2

        if angle > np.pi/2.0 or angle < 0:
            raise ValueError("Warning! Improper angle specified ("+str(angle)+").  Must be between 0 and pi/2.0.")
        self.angle = angle

        self.MMI1x2length = MMI1x2length
        self.MMI1x2width = MMI1x2width
        self.MMI1x2taper_width = wgt.wg_width if MMI1x2taper_width==None else MMI1x2taper_width
        self.MMI1x2taper_length = 20 if MMI1x2taper_length==None else MMI1x2taper_length
        self.MMI1x2wg_sep = MMI1x2width/3.0 if MMI1x2wg_sep==None else MMI1x2wg_sep

        self.MMI2x2length = MMI2x2length
        self.MMI2x2width = MMI2x2width
        self.MMI2x2taper_width = wgt.wg_width if MMI2x2taper_width==None else MMI2x2taper_width
        self.MMI2x2taper_length = 20 if MMI2x2taper_length==None else MMI2x2taper_length
        self.MMI2x2wg_sep = MMI2x2width/3.0 if MMI2x2wg_sep==None else MMI2x2wg_sep

        self.angle_x_dist = 2*self.wgt.bend_radius*np.sin(self.angle)
        self.angle_y_dist = 2*self.wgt.bend_radius*(1-np.cos(self.angle))

        self.mmi1x2length = self.MMI1x2length + self.MMI1x2taper_length + self.angle_x_dist
        self.mmi2x2length = self.MMI2x2length + 2*self.angle_x_dist

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

        mmi1 = MMI1x2(self.wgt, self.MMI1x2length, self.MMI1x2width,
                      angle=self.angle,
                      taper_width=self.MMI1x2taper_width,
                      taper_length=self.MMI1x2taper_length,
                      wg_sep=self.MMI1x2wg_sep,
                      port=(0,0), direction='EAST')
        mmi2 = MMI2x2(self.wgt, self.MMI2x2length, self.MMI2x2width,
                      angle=self.angle,
                      taper_width=self.MMI2x2taper_width,
                      taper_length=self.MMI2x2taper_length,
                      wg_sep=self.MMI2x2wg_sep,
                      port=(self.mmi2x2length+self.mmi1x2length+4*self.wgt.bend_radius, -self.MMI2x2wg_sep/2.0-self.angle_y_dist), direction='WEST')

        y_end_top, y_end_bot = mmi2.portlist["output_top"]["port"][1], mmi2.portlist["output_bot"]["port"][1]

        (x0, y0) = mmi1.portlist["output_top"]["port"]
        trace1 = [(x0, y0),
                  (x0+self.wgt.bend_radius, y0),
                  (x0+self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y_end_bot),
                  (x0+4*self.wgt.bend_radius, y_end_bot)]
        wg_top = Waveguide(trace1, self.wgt)

        (x1, y1) = mmi1.portlist["output_bot"]["port"]
        trace2 = [(x1, y1),
                  (x1+self.wgt.bend_radius, y1),
                  (x1+self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y_end_top),
                  (x1+4*self.wgt.bend_radius, y_end_top)]
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

        totalxlen = self.mmi2x2length+self.mmi1x2length+4*self.wgt.bend_radius
        if self.direction=='EAST':
            angle=0
            self.port_output_top = (self.port[0]+totalxlen, self.port[1]+self.MMI2x2wg_sep/2.0+self.angle_y_dist)
            self.port_output_bot = (self.port[0]+totalxlen, self.port[1]-self.MMI2x2wg_sep/2.0-self.angle_y_dist)
            self.htr_top_in_dir ='WEST'
            self.htr_top_out_dir = 'EAST'
            self.htr_bot_in_dir = 'WEST'
            self.htr_bot_out_dir = 'EAST'
        elif self.direction=='NORTH':
            angle=90
            self.port_output_top = (self.port[0]-self.MMI2x2wg_sep/2.0-self.angle_y_dist, self.port[1]+totalxlen)
            self.port_output_bot = (self.port[0]+self.MMI2x2wg_sep/2.0+self.angle_y_dist, self.port[1]+totalxlen)
            self.htr_top_in_dir ='SOUTH'
            self.htr_top_out_dir = 'NORTH'
            self.htr_bot_in_dir = 'SOUTH'
            self.htr_bot_out_dir = 'NORTH'
        elif self.direction=='WEST':
            angle=180
            self.port_output_top = (self.port[0]-totalxlen, self.port[1]-self.MMI2x2wg_sep/2.0-self.angle_y_dist)
            self.port_output_bot = (self.port[0]-totalxlen, self.port[1]+self.MMI2x2wg_sep/2.0+self.angle_y_dist)
            self.htr_top_in_dir ='EAST'
            self.htr_top_out_dir = 'WEST'
            self.htr_bot_in_dir = 'EAST'
            self.htr_bot_out_dir = 'WEST'
        elif self.direction=='SOUTH':
            angle=-90
            self.port_output_top = (self.port[0]+self.MMI2x2wg_sep/2.0+self.angle_y_dist, self.port[1]-totalxlen)
            self.port_output_bot = (self.port[0]-self.MMI2x2wg_sep/2.0-self.angle_y_dist, self.port[1]-totalxlen)
            self.htr_top_in_dir ='NORTH'
            self.htr_top_out_dir = 'SOUTH'
            self.htr_bot_in_dir = 'NORTH'
            self.htr_bot_out_dir = 'SOUTH'
        elif isinstance(self.direction, float):
            angle = 180.0*self.direction/np.pi
            self.port_output_top = (self.port[0] + totalxlen*np.cos(self.direction) - (self.MMI2x2wg_sep/2.0+self.angle_y_dist)*np.sin(self.direction), self.port[1] + totalxlen*np.sin(self.direction) + (self.MMI2x2wg_sep/2.0+self.angle_y_dist)*np.cos(self.direction))
            self.port_output_bot = (self.port[0] + totalxlen*np.cos(self.direction) - (-self.MMI2x2wg_sep/2.0-self.angle_y_dist)*np.sin(self.direction), self.port[1] + totalxlen*np.sin(self.direction) + (-self.MMI2x2wg_sep/2.0-self.angle_y_dist)*np.cos(self.direction))

            self.htr_top_in_dir = self.direction + np.pi/2.0
            self.htr_top_out_dir = self.direction + 3*np.pi/2.0
            self.htr_bot_in_dir = self.direction + np.pi/2.0
            self.htr_bot_out_dir = self.direction + 3*np.pi/2.0

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
        self.portlist["output_top"] = {'port':self.port_output_top, 'direction':self.direction}
        self.portlist["output_bot"] = {'port':self.port_output_bot, 'direction':self.direction}
        if self.heater:
            self.portlist["heater_top_in"] = {'port': self.htr_top_in, 'direction':self.htr_top_in_dir}
            self.portlist["heater_top_out"] = {'port': self.htr_top_out, 'direction':self.htr_top_out_dir}
            self.portlist["heater_bot_in"] = {'port': self.htr_bot_in, 'direction':self.htr_bot_in_dir}
            self.portlist["heater_bot_out"] = {'port': self.htr_bot_out, 'direction':self.htr_bot_out_dir}

class MachZehnderSwitchDC1x2(gdspy.Cell):
    """ Standard Mach-Zehnder Optical Switch Cell class with heaters on each arm and a directional coupler (subclass of gdspy.Cell).  It is possible to generate your own Mach-Zehnder from the other classes, but this class is simply a shorthand (with some extra type-checking).  Defaults to a *balanced* Mach Zehnder.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **MMI1x2length** (float): Length of the 1x2 MMI region (along direction of propagation)
           * **MMI1x2width** (float): Width of the 1x2 MMI region (perpendicular to direction of propagation).
           * **DClength** (float): Length of the directional coupler region
           * **DCgap** (float): Size of the directional coupler gap

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region (same for MMI & DC).  Default=pi/6.
           * **MMI1x2taper_width** (float): Maximum width of the 1x2 MMI taper region (default = wg_width from wg_template).  Defaults to None (waveguide width).
           * **MMI1x2taper_length** (float): Length of the taper leading up to the 1x2 MMI.  Defaults to None (taper_length=20).
           * **MMI1x2wg_sep** (float): Separation between waveguides on the 2-port side of the 1x2 MMI (defaults to width/3.0)
           * **arm1** (float): Additional length of the top arm (when going `'EAST'`).  Defaults to zero.
           * **arm2** (float): Additional length of the bottom arm (when going `'EAST'`).  Defaults to zero.
           * **heater** (boolean): If true, adds heater on-top of one MZI arm.  Defaults to False.
           * **heater_length** (float): Specifies the length of the heater along the waveguide. Doesn't include the length of the 180 degree bend.  Defaults to 400.0.
           * **mt** (MetalTemplate): If 'heater' is true, must specify a Metal Template that defines heater & heater cladding layers.
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the taper will point *towards*, must be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to `'EAST'` (0 radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output_top'] = {'port': (x2, y2), 'direction': 'dir2'}
           * portlist['output_bot'] = {'port': (x3, y3), 'direction': 'dir3'}
           * portlist['heater_top_in'] = {'port', (x4, y4), 'direction': 'dir4'}
           * portlist['heater_top_out'] = {'port', (x5, y5), 'direction': 'dir5'}
           * portlist['heater_bot_in'] = {'port', (x6, y6), 'direction': 'dir6'}
           * portlist['heater_bot_out'] = {'port', (x7, y7), 'direction': 'dir7'}

        Where in the above (x1,y1) is the input port, (x2, y2) is the top output port, (x3, y3) is the bottom output port, and the directions are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.
        Four additional ports are created for the heaters if the `heater` argument is True.  Metals are not generated, but should be connected to the specified 'heater' ports.

    """
    def __init__(self, wgt, MMI1x2length, MMI1x2width, DClength, DCgap, angle=np.pi/6.0, MMI1x2taper_width=None,
                 MMI1x2taper_length=None, MMI1x2wg_sep=None,
                 arm1=0, arm2=0, heater=False, heater_length=400, mt=None, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "MZISwitchDC1x2--"+str(uuid.uuid4()))

        self.portlist = {}

        self.wgt = wgt
        self.arm1 = arm1
        self.arm2 = arm2

        if angle > np.pi/2.0 or angle < 0:
            raise ValueError("Warning! Improper angle specified ("+str(angle)+").  Must be between 0 and pi/2.0.")
        self.angle = angle

        self.MMI1x2length = MMI1x2length
        self.MMI1x2width = MMI1x2width
        self.MMI1x2taper_width = wgt.wg_width if MMI1x2taper_width==None else MMI1x2taper_width
        self.MMI1x2taper_length = 20 if MMI1x2taper_length==None else MMI1x2taper_length
        self.MMI1x2wg_sep = MMI1x2width/3.0 if MMI1x2wg_sep==None else MMI1x2wg_sep

        self.DClength = DClength
        self.DCgap = DCgap

        self.angle_x_dist = 2*self.wgt.bend_radius*np.sin(self.angle)
        self.angle_y_dist = 2*self.wgt.bend_radius*(1-np.cos(self.angle))

        padding = 0.01
        dlx = abs(self.wgt.bend_radius*np.tan((self.angle)/2.0))
        self.angle_x_distDC = 2*dlx+2.0*(dlx+padding)*np.cos(self.angle)
        self.angle_y_distDC = 2.0*(dlx+padding)*np.sin(self.angle)

        self.mmi1x2length = self.MMI1x2length + self.MMI1x2taper_length + self.angle_x_dist
        self.dclength = self.DClength + 2*self.angle_x_distDC

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

        mmi1 = MMI1x2(self.wgt, self.MMI1x2length, self.MMI1x2width,
                      angle=self.angle,
                      taper_width=self.MMI1x2taper_width,
                      taper_length=self.MMI1x2taper_length,
                      wg_sep=self.MMI1x2wg_sep,
                      port=(0,0), direction='EAST')
        dc_out = DirectionalCoupler(self.wgt,
                                    self.DClength,
                                    self.DCgap,
                                    angle=self.angle,
                                    port=(self.dclength+self.mmi1x2length+4*self.wgt.bend_radius, -self.DCgap/2.0-self.wgt.wg_width/2.0-self.angle_y_distDC), direction='WEST')

        y_end_top, y_end_bot = dc_out.portlist["output_top"]["port"][1], dc_out.portlist["output_bot"]["port"][1]

        (x0, y0) = mmi1.portlist["output_top"]["port"]
        trace1 = [(x0, y0),
                  (x0+self.wgt.bend_radius, y0),
                  (x0+self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y_end_bot),
                  (x0+4*self.wgt.bend_radius, y_end_bot)]
        wg_top = Waveguide(trace1, self.wgt)

        (x1, y1) = mmi1.portlist["output_bot"]["port"]
        trace2 = [(x1, y1),
                  (x1+self.wgt.bend_radius, y1),
                  (x1+self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y_end_top),
                  (x1+4*self.wgt.bend_radius, y_end_top)]
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

        totalxlen = self.dclength+self.mmi1x2length+4*self.wgt.bend_radius
        if self.direction=='EAST':
            angle=0
            self.port_output_top = (self.port[0]+totalxlen, self.port[1]+self.DCgap/2.0+self.wgt.wg_width/2.0+self.angle_y_distDC)
            self.port_output_bot = (self.port[0]+totalxlen, self.port[1]-self.DCgap/2.0-self.wgt.wg_width/2.0-self.angle_y_distDC)
            self.htr_top_in_dir ='WEST'
            self.htr_top_out_dir = 'EAST'
            self.htr_bot_in_dir = 'WEST'
            self.htr_bot_out_dir = 'EAST'
        elif self.direction=='NORTH':
            angle=90
            self.port_output_top = (self.port[0]-self.DCgap/2.0-self.wgt.wg_width/2.0-self.angle_y_distDC, self.port[1]+totalxlen)
            self.port_output_bot = (self.port[0]+self.DCgap/2.0+self.wgt.wg_width/2.0+self.angle_y_distDC, self.port[1]+totalxlen)
            self.htr_top_in_dir ='SOUTH'
            self.htr_top_out_dir = 'NORTH'
            self.htr_bot_in_dir = 'SOUTH'
            self.htr_bot_out_dir = 'NORTH'
        elif self.direction=='WEST':
            angle=180
            self.port_output_top = (self.port[0]-totalxlen, self.port[1]-self.DCgap/2.0-self.wgt.wg_width/2.0-self.angle_y_distDC)
            self.port_output_bot = (self.port[0]-totalxlen, self.port[1]+self.DCgap/2.0+self.wgt.wg_width/2.0+self.angle_y_distDC)
            self.htr_top_in_dir ='EAST'
            self.htr_top_out_dir = 'WEST'
            self.htr_bot_in_dir = 'EAST'
            self.htr_bot_out_dir = 'WEST'
        elif self.direction=='SOUTH':
            angle=-90
            self.port_output_top = (self.port[0]+self.DCgap/2.0+self.wgt.wg_width/2.0+self.angle_y_distDC, self.port[1]-totalxlen)
            self.port_output_bot = (self.port[0]-self.DCgap/2.0-self.wgt.wg_width/2.0-self.angle_y_distDC, self.port[1]-totalxlen)
            self.htr_top_in_dir ='NORTH'
            self.htr_top_out_dir = 'SOUTH'
            self.htr_bot_in_dir = 'NORTH'
            self.htr_bot_out_dir = 'SOUTH'
        elif isinstance(self.direction, float):
            angle = 180.0*self.direction/np.pi
            self.port_output_top = (self.port[0] + totalxlen*np.cos(self.direction) - (self.DCgap/2.0+self.wgt.wg_width/2.0+self.angle_y_distDC)*np.sin(self.direction), self.port[1] + totalxlen*np.sin(self.direction) + (self.DCgap/2.0+self.wgt.wg_width/2.0+self.angle_y_distDC)*np.cos(self.direction))
            self.port_output_bot = (self.port[0] + totalxlen*np.cos(self.direction) - (-self.DCgap/2.0-self.wgt.wg_width/2.0-self.angle_y_distDC)*np.sin(self.direction), self.port[1] + totalxlen*np.sin(self.direction) + (-self.DCgap/2.0-self.wgt.wg_width/2.0-self.angle_y_distDC)*np.cos(self.direction))

            self.htr_top_in_dir = self.direction + np.pi/2.0
            self.htr_top_out_dir = self.direction + 3*np.pi/2.0
            self.htr_bot_in_dir = self.direction + np.pi/2.0
            self.htr_bot_out_dir = self.direction + 3*np.pi/2.0

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
        components = [mmi1, dc_out, wg_top, wg_bot, heater_top, heater_bot]
        for c in components:
            self.add(gdspy.CellReference(c, origin=self.port, rotation=angle))

    def build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}

        self.portlist["input"] = {'port':self.port, 'direction':tk.flip_direction(self.direction)}
        self.portlist["output_top"] = {'port':self.port_output_top, 'direction':self.direction}
        self.portlist["output_bot"] = {'port':self.port_output_bot, 'direction':self.direction}
        if self.heater:
            self.portlist["heater_top_in"] = {'port': self.htr_top_in, 'direction':self.htr_top_in_dir}
            self.portlist["heater_top_out"] = {'port': self.htr_top_out, 'direction':self.htr_top_out_dir}
            self.portlist["heater_bot_in"] = {'port': self.htr_bot_in, 'direction':self.htr_bot_in_dir}
            self.portlist["heater_bot_out"] = {'port': self.htr_bot_out, 'direction':self.htr_bot_out_dir}

class MachZehnderSwitchDC2x2(gdspy.Cell):
    """ Standard Mach-Zehnder Optical Switch Cell class with heaters on each arm and a directional coupler (subclass of gdspy.Cell) for both input and output.  It is possible to generate your own Mach-Zehnder from the other classes, but this class is simply a shorthand (with some extra type-checking).  Defaults to a *balanced* Mach Zehnder.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **DC1length** (float): Length of the directional coupler region at the input
           * **DC1gap** (float): Size of the directional coupler gap at the input
           * **DC2length** (float): Length of the directional coupler region at the output
           * **DC2gap** (float): Size of the directional coupler gap at the output

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6.
           * **arm1** (float): Additional length of the top arm (when going `'EAST'`).  Defaults to zero.
           * **arm2** (float): Additional length of the bottom arm (when going `'EAST'`).  Defaults to zero.
           * **heater** (boolean): If true, adds heater on-top of one MZI arm.  Defaults to False.
           * **heater_length** (float): Specifies the length of the heater along the waveguide. Doesn't include the length of the 180 degree bend.  Defaults to 400.0.
           * **mt** (MetalTemplate): If 'heater' is true, must specify a Metal Template that defines heater & heater cladding layers.
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the taper will point *towards*, must be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to `'EAST'` (0 radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input_top'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['input_bot'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output_top'] = {'port': (x2, y2), 'direction': 'dir2'}
           * portlist['output_bot'] = {'port': (x3, y3), 'direction': 'dir3'}
           * portlist['heater_top_in'] = {'port', (x4, y4), 'direction': 'dir4'}
           * portlist['heater_top_out'] = {'port', (x5, y5), 'direction': 'dir5'}
           * portlist['heater_bot_in'] = {'port', (x6, y6), 'direction': 'dir6'}
           * portlist['heater_bot_out'] = {'port', (x7, y7), 'direction': 'dir7'}

        Where in the above (x1,y1) is the input port, (x2, y2) is the top output port, (x3, y3) is the bottom output port, and the directions are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.
        Four additional ports are created for the heaters if the `heater` argument is True.  Metals are not generated, but should be connected to the specified 'heater' ports.

    """
    def __init__(self, wgt, DC1length, DC1gap, DC2length, DC2gap, angle=np.pi/6.0,
                 arm1=0, arm2=0, heater=False, heater_length=400, mt=None, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "MZISwitchDC2x2--"+str(uuid.uuid4()))

        self.portlist = {}

        self.wgt = wgt
        self.arm1 = arm1
        self.arm2 = arm2

        if angle > np.pi/2.0 or angle < 0:
            raise ValueError("Warning! Improper angle specified ("+str(angle)+").  Must be between 0 and pi/2.0.")
        self.angle = angle

        self.DC1length = DC1length
        self.DC1gap = DC1gap

        self.DC2length = DC2length
        self.DC2gap = DC2gap

#        self.angle_x_dist = 2*self.wgt.bend_radius*np.sin(self.angle)
#        self.angle_y_dist = 2*self.wgt.bend_radius*(1-np.cos(self.angle))

        padding = 0.01
        dlx = abs(self.wgt.bend_radius*np.tan((self.angle)/2.0))
        self.angle_x_dist = 2*dlx+2.0*(dlx+padding)*np.cos(self.angle)
        self.angle_y_dist = 2.0*(dlx+padding)*np.sin(self.angle)

        self.dc1length = self.DC1length + 2*self.angle_x_dist
        self.dc2length = self.DC2length + 2*self.angle_x_dist

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
        dc_in  = DirectionalCoupler(self.wgt,
                                    self.DC1length,
                                    self.DC1gap,
                                    angle=self.angle,
                                    port=(0, 0), direction='EAST')

        dc_out = DirectionalCoupler(self.wgt,
                                    self.DC2length,
                                    self.DC2gap,
                                    angle=self.angle,
                                    port=(self.dc1length+self.dc2length+4*self.wgt.bend_radius, -self.DC2gap-self.wgt.wg_width-2*self.angle_y_dist), direction='WEST')

        y_end_top, y_end_bot = dc_out.portlist["output_top"]["port"][1], dc_out.portlist["output_bot"]["port"][1]

        (x0, y0) = dc_in.portlist["output_top"]["port"]
        trace1 = [(x0, y0),
                  (x0+self.wgt.bend_radius, y0),
                  (x0+self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y0+2*self.wgt.bend_radius + self.arm1/2.0 + self.heater_length/2.0),
                  (x0+3*self.wgt.bend_radius, y_end_bot),
                  (x0+4*self.wgt.bend_radius, y_end_bot)]
        wg_top = Waveguide(trace1, self.wgt)

        (x1, y1) = dc_in.portlist["output_bot"]["port"]
        trace2 = [(x1, y1),
                  (x1+self.wgt.bend_radius, y1),
                  (x1+self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y1-2*self.wgt.bend_radius - self.arm2/2.0 - self.heater_length/2.0),
                  (x1+3*self.wgt.bend_radius, y_end_top),
                  (x1+4*self.wgt.bend_radius, y_end_top)]
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

        totalxlen = self.dc1length+self.dc2length+4*self.wgt.bend_radius
        dy_output = self.DC2gap/2.0 + self.wgt.wg_width/2.0 + self.angle_y_dist
        dy_input =  self.DC1gap/2.0 + self.wgt.wg_width/2.0 + self.angle_y_dist
        if self.direction=='EAST':
            angle=0
            self.port_output_top = (self.port[0]+totalxlen, self.port[1])
            self.port_output_bot = (self.port[0]+totalxlen, self.port[1] - 2*dy_output)
            self.port_input_top = (0.0, 0.0)
            self.port_input_bot = (0.0, -2*dy_input)
            self.htr_top_in_dir ='WEST'
            self.htr_top_out_dir = 'EAST'
            self.htr_bot_in_dir = 'WEST'
            self.htr_bot_out_dir = 'EAST'
        elif self.direction=='NORTH':
            angle=90
            self.port_output_top = (self.port[0], self.port[1]+totalxlen)
            self.port_output_bot = (self.port[0] + 2*dy_output, self.port[1]+totalxlen)
            self.port_input_top = (0.0, 0.0)
            self.port_input_bot = (2*dy_input, 0.0)
            self.htr_top_in_dir ='SOUTH'
            self.htr_top_out_dir = 'NORTH'
            self.htr_bot_in_dir = 'SOUTH'
            self.htr_bot_out_dir = 'NORTH'
        elif self.direction=='WEST':
            angle=180
            self.port_output_top = (self.port[0]-totalxlen, self.port[1])
            self.port_output_bot = (self.port[0]-totalxlen, self.port[1] + 2*dy_output)
            self.port_input_top = (0.0, 0.0)
            self.port_input_bot = (0.0, 2*dy_input)
            self.htr_top_in_dir ='EAST'
            self.htr_top_out_dir = 'WEST'
            self.htr_bot_in_dir = 'EAST'
            self.htr_bot_out_dir = 'WEST'
        elif self.direction=='SOUTH':
            angle=-90
            self.port_output_top = (self.port[0], self.port[1]-totalxlen)
            self.port_output_bot = (self.port[0] - 2*dy_output, self.port[1]-totalxlen)
            self.port_input_top = (0.0, 0.0)
            self.port_input_bot = (-2*dy_input, 0.0)
            self.htr_top_in_dir ='NORTH'
            self.htr_top_out_dir = 'SOUTH'
            self.htr_bot_in_dir = 'NORTH'
            self.htr_bot_out_dir = 'SOUTH'
        elif isinstance(self.direction, float):
            angle = 180.0*self.direction/np.pi
            self.port_output_top = (self.port[0] + totalxlen*np.cos(self.direction), self.port[1] + totalxlen*np.sin(self.direction))
            self.port_output_bot = (self.port[0] + totalxlen*np.cos(self.direction) - (-2*dy_output)*np.sin(self.direction), self.port[1] + totalxlen*np.sin(self.direction) + (-2*dy_output)*np.cos(self.direction))

            self.port_input_top = (self.port[0], self.port[1])
            self.port_input_bot = (self.port[0] - (-2*dy_input)*np.sin(self.direction), self.port[1] + (-2*dy_input)*np.cos(self.direction))

            self.htr_top_in_dir = self.direction + np.pi/2.0
            self.htr_top_out_dir = self.direction + 3*np.pi/2.0
            self.htr_bot_in_dir = self.direction + np.pi/2.0
            self.htr_bot_out_dir = self.direction + 3*np.pi/2.0

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
        components = [dc_in, dc_out, wg_top, wg_bot, heater_top, heater_bot]
        for c in components:
            self.add(gdspy.CellReference(c, origin=self.port, rotation=angle))

    def build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}

        self.portlist["input_top"] = {'port':self.port_input_top, 'direction':tk.flip_direction(self.direction)}
        self.portlist["input_bot"] = {'port':self.port_input_bot, 'direction':tk.flip_direction(self.direction)}
        self.portlist["output_top"] = {'port':self.port_output_top, 'direction':self.direction}
        self.portlist["output_bot"] = {'port':self.port_output_bot, 'direction':self.direction}
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

#    mzi = MachZehnder(wgt, MMIlength=50, MMIwidth=10, MMItaper_width=2.0, MMIwg_sep=3, arm1=0, arm2=100, heater=True, heater_length=400, mt=htr_mt, **wg_in.portlist["output"])
#    mzi = MachZehnderSwitchDC1x2(wgt, MMI1x2length=50, MMI1x2width=10, MMI1x2taper_width=2.0, MMI1x2wg_sep=3, DClength=100, DCgap=0.5,
#                                 arm1=0, arm2=0, heater=True, heater_length=400, mt=htr_mt, port=(0,0), direction='EAST')

    mzi = MachZehnderSwitchDC2x2(wgt, DC1length=200, DC1gap=0.5, DC2length=100, DC2gap=1.5,
                                    arm1=0, arm2=0, heater=True, heater_length=400, mt=htr_mt, **wg_in.portlist["output"])
    print("input_top = "+str(mzi.portlist["input_top"]["port"]))
    print("input_bot = "+str(mzi.portlist["input_bot"]["port"]))

    tk.add(top, mzi)

    x_to, y_to = mzi.portlist["output_top"]["port"]
    wg_out_top = Waveguide([(x_to, y_to),
                       (x_to + wgt.bend_radius*0.75, y_to),
                       (x_to + 1.5*wgt.bend_radius, y_to + wgt.bend_radius),
                       (x_to + wgt.bend_radius+300, y_to + wgt.bend_radius)], wgt)
    tk.add(top, wg_out_top)

    x_bo, y_bo = mzi.portlist["output_bot"]["port"]
    wg_out_bot = Waveguide([(x_bo, y_bo),
                       (x_bo+wgt.bend_radius*0.75, y_bo),
                       (x_bo+1.5*wgt.bend_radius, y_bo-wgt.bend_radius),
                       (x_bo+wgt.bend_radius+300, y_bo-wgt.bend_radius)], wgt)
    tk.add(top, wg_out_bot)

#    wg_out = Waveguide([mzi.portlist["output"]["port"],
#                       (mzi.portlist["output"]["port"][0]+wgt.bend_radius, mzi.portlist["output"]["port"][1]),
#                       (mzi.portlist["output"]["port"][0]+wgt.bend_radius, mzi.portlist["output"]["port"][1]-2*wgt.bend_radius),
#                       (mzi.portlist["output"]["port"][0]+wgt.bend_radius+300, mzi.portlist["output"]["port"][1]-2*wgt.bend_radius)], wgt)
#    tk.add(top, wg_out)

    (x1,y1) = mzi.portlist["heater_top_in"]["port"]
    mt1=MetalRoute([(x1,y1), (x1-150, y1), (x1-150, y1+200)], mt)

    (x2,y2) = mzi.portlist["heater_top_out"]["port"]
    mt2=MetalRoute([(x2,y2), (x2+150, y2), (x2+150, y2+200)], mt)

    (x3, y3) = mzi.portlist["heater_bot_in"]["port"]
    mt3=MetalRoute([(x3,y3), (x3-150.0, y3), (x3-150, y3-200)], mt)

    (x4, y4) = mzi.portlist["heater_bot_out"]["port"]
    mt4=MetalRoute([(x4, y4), (x4+150, y4), (x4+150, y4-200)], mt)

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

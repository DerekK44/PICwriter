# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class Disk(gdspy.Cell):
    """ Standard Disk Resonator Cell class (subclass of gdspy.Cell).

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **radius** (float): Radius of the resonator
           * **coupling_gap** (float): Distance between the bus waveguide and resonator

        Keyword Args:
           * **parity** (1 or -1): If 1, resonator to left of bus waveguide, if -1 resonator to the right
           * **port** (tuple): Cartesian coordinate of the input port (x1, y1)
           * **direction** (string): Direction that the taper will point *towards*, must be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) is the same as the 'port' input, (x2, y2) is the end of the taper, and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.

    """
    def __init__(self, wgt, radius, coupling_gap, parity=1, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "Taper--"+str(uuid.uuid4()))

        self.portlist = {}

        self.port = port
        self.trace=[port, tk.translate_point(port, 2*radius, direction)]
        self.direction = direction

        self.radius = radius
        self.coupling_gap = coupling_gap
        self.parity = parity
        self.resist = wgt.resist
        self.wgt = wgt
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.build_cell()
        self.build_ports()

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell

        # Add bus waveguide with cladding
        path = gdspy.Path(self.wgt.wg_width, self.trace[0])
        path.segment(2*self.radius, direction='+x', **self.wg_spec)
        clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, self.trace[0])
        clad.segment(2*self.radius, direction='+x', **self.clad_spec)

        # Ring resonator
        if self.parity==1:
            ring = gdspy.Round((self.port[0]+self.radius, self.port[1]+self.radius+self.wgt.wg_width + self.coupling_gap),
                                self.radius+self.wgt.wg_width/2.0, number_of_points=0.1, **self.wg_spec)
            clad_ring = gdspy.Round((self.port[0]+self.radius, self.port[1]+self.radius+self.wgt.wg_width + self.coupling_gap),
                                     self.radius+self.wgt.wg_width/2.0+self.wgt.clad_width, number_of_points=0.1, **self.clad_spec)
        elif self.parity==-1:
            ring = gdspy.Round((self.port[0]+self.radius, self.port[1]-self.radius-self.wgt.wg_width - self.coupling_gap),
                                self.radius+self.wgt.wg_width/2.0, number_of_points=0.1, **self.wg_spec)
            clad_ring = gdspy.Round((self.port[0]+self.radius, self.port[1] - self.radius - self.wgt.wg_width - self.coupling_gap),
                                     self.radius+self.wgt.wg_width/2.0+self.wgt.clad_width, number_of_points=0.1, **self.clad_spec)
        else:
            raise ValueError("Warning!  Parity value is not an acceptable value (must be +1 or -1).")

        angle=0
        if self.direction=="EAST":
            angle=0
        elif self.direction=="NORTH":
            angle=np.pi/2.0
        elif self.direction=="WEST":
            angle=np.pi
        elif self.direction=="SOUTH":
            angle=-np.pi/2.0

        ring.rotate(angle, self.port)
        clad_ring.rotate(angle, self.port)
        path.rotate(angle, self.port)
        clad.rotate(angle, self.port)

        self.add(ring)
        self.add(clad_ring)
        self.add(path)
        self.add(clad)

    def build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':self.trace[0],
                                    'direction':tk.flip_direction(self.direction)}
        self.portlist["output"] = {'port':self.trace[1],
                                    'direction':self.direction}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+')

    wg1=Waveguide([(0,0), (100,0)], wgt)
    tk.add(top, wg1)

    r1 = Disk(wgt, 60.0, 1.0, parity=1, **wg1.portlist["output"])

    wg2=Waveguide([r1.portlist["output"]["port"], (r1.portlist["output"]["port"][0]+100, r1.portlist["output"]["port"][1])], wgt)
    tk.add(top, wg2)

    r2 = Disk(wgt, 50.0, 0.8, parity=1, **wg2.portlist["output"])

    wg3=Waveguide([r2.portlist["output"]["port"], (r2.portlist["output"]["port"][0]+100, r2.portlist["output"]["port"][1])], wgt)
    tk.add(top, wg3)

    r3 = Disk(wgt, 40.0, 0.6, parity=1, **wg3.portlist["output"])

    wg4=Waveguide([r3.portlist["output"]["port"], (r3.portlist["output"]["port"][0]+100, r3.portlist["output"]["port"][1])], wgt)
    tk.add(top, wg4)

    tk.add(top, r1)
    tk.add(top, r2)
    tk.add(top, r3)

    # gdspy.LayoutViewer()
    gdspy.write_gds('disk.gds', unit=1.0e-6, precision=1.0e-9)

# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class StripSlotYCoupler(gdspy.Cell):
    """ Strip-to-Slot Y-Coupler Cell class (subclass of gdspy.Cell).

        Args:
           * **wgt_strip** (WaveguideTemplate):  WaveguideTemplate object for *strip* waveguide.
           * **wgt_slot** (WaveguideTemplate):  WaveguideTemplate object for *slot* waveguide.
           * **length** (float): Length of the tapered region.
           * **d** (float): Distance between the outer edge of the strip waveguide and the start of the slot waveguide rail.

        Keyword Args:
           * **end_strip_width** (float): End width of the strip waveguide (at the narrow tip).  Defaults to 0.
           * **end_slot_width** (float): End width of the slot waveguide (at the narrow tip).  Defaults to 0.
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) is the same as the 'port' input, (x2, y2) is the end of the taper, and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

        Note: The waveguide and cladding layer/datatype are taken from the `wgt_slot` by default.

    """
    def __init__(self, wgt_strip, wgt_slot, length, d, end_strip_width=0, end_slot_width=0, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "StripSlotYCoupler--"+str(uuid.uuid4()))

        self.portlist = {}

        self.wgt_strip = wgt_strip
        self.wgt_slot = wgt_slot
        self.wg_spec = {'layer': wgt_slot.wg_layer, 'datatype': wgt_slot.wg_datatype}
        self.clad_spec = {'layer': wgt_slot.clad_layer, 'datatype': wgt_slot.clad_datatype}

        self.length = length
        self.d = d
        self.end_strip_width = end_strip_width
        self.end_slot_width = end_slot_width

        self.port = port
        self.trace=[port, tk.translate_point(port, length, direction)]
        self.direction = direction

        self.build_cell()
        self.build_ports()

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell

        angle = tk.get_exact_angle(self.trace[0], self.trace[1])
        angle_opp = tk.get_exact_angle(self.trace[1], self.trace[0])

        # Add strip waveguide taper
        path_strip = gdspy.Path(self.wgt_strip.wg_width, self.trace[0])
        path_strip.segment(self.length, final_width=self.end_strip_width, direction=angle, **self.wg_spec)

        # Add slot waveguide taper
        path_slot = gdspy.Path(self.wgt_slot.rail, self.trace[1], number_of_paths=2, distance=self.wgt_slot.rail_dist)
        path_slot.segment(self.length, final_width=self.end_slot_width, final_distance=(self.wgt_strip.wg_width+2*self.d+self.wgt_slot.rail), direction=angle_opp, **self.wg_spec)

        # Cladding for waveguide taper
        path_clad = gdspy.Path(2*self.wgt_strip.clad_width+self.wgt_strip.wg_width, self.trace[0])
        path_clad.segment(self.length, final_width=2*self.wgt_slot.clad_width+self.wgt_slot.wg_width, direction=angle, **self.clad_spec)

        self.add(path_strip)
        self.add(path_slot)
        self.add(path_clad)

    def build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':self.trace[0], 'direction':tk.flip_direction(self.direction)}
        self.portlist["output"] = {'port':self.trace[1], 'direction':self.direction}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt_strip = WaveguideTemplate(bend_radius=50, wg_type='strip', wg_width=0.7)
    wgt_slot = WaveguideTemplate(bend_radius=50, wg_type='slot', wg_width=0.7, slot=0.2)

    wg1=Waveguide([(0,0), (100,0)], wgt_strip)
    tk.add(top, wg1)

    ycoup = StripSlotYCoupler(wgt_strip, wgt_slot, 10.0, 0.2, end_slot_width=0, **wg1.portlist["output"])
    tk.add(top, ycoup)

    (x1,y1)=ycoup.portlist["output"]["port"]
    wg2=Waveguide([(x1, y1), (x1+100, y1)], wgt_slot)
    tk.add(top, wg2)

#    gdspy.LayoutViewer()
    gdspy.write_gds('stripslotycoupler.gds', unit=1.0e-6, precision=1.0e-9)

# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class Taper(gdspy.Cell):
    """ Standard Taper Cell class (subclass of gdspy.Cell).

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length** (float): Length of the taper
           * **end_width** (float): Final width of the taper (initial width received from WaveguieTemplate)

        Keyword Args:
           * **port** (tuple): Cartesian coordinate of the input port
           * **direction** (string): Direction that the taper will point *towards*, must be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) is the same as the 'port' input, (x2, y2) is the end of the taper, and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`.

    """
    def __init__(self, wgt, length, end_width, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "Taper--"+str(uuid.uuid4()))

        self.portlist = {}

        self.port = port
        self.trace=[port, tk.translate_point(port, length, direction)]
        self.direction = direction
        self.start_width = wgt.wg_width
        self.end_width = end_width
        self.resist = wgt.resist
        self.wgt = wgt
        self.spec = {'layer': wgt.layer, 'datatype': wgt.datatype}

        self.type_check_trace()
        self.build_cell()
        self.build_ports()

    def type_check_trace(self):
        trace = []
        """ Round each trace value to the nearest 1e-6 -- prevents
        some typechecking errors
        """
        for t in self.trace:
            trace.append((round(t[0], 6), round(t[1], 5)))
        self.trace = trace
        """ Make sure all waypoints specify 90degree angles.  This might be
        updated in the future to allow for 45deg, or arbitrary bends.  For now,
        though, rotations are supported via gdspy library
        """
        dx = abs(self.trace[1][0]-self.trace[0][0])
        dy = abs(self.trace[1][1]-self.trace[0][1])
        if dx>=1e-6 and dy>=1e-6:
            raise ValueError("Warning! Both waypoints *must* specify horizontal "
                             "or vertical tapers.")

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        angle = tk.get_angle(self.trace[0], self.trace[1])
        if self.resist=='-':
            path = gdspy.Path(self.wgt.wg_width, self.trace[0])
            path.segment(tk.dist(self.trace[0], self.trace[1]),
                         direction=angle, final_width=self.end_width, **self.spec)
        elif self.resist=='+':
            path = gdspy.Path(self.wgt.clad_width, self.trace[0], number_of_paths=2,
                              distance=self.wgt.wg_width + self.wgt.clad_width)
            path.segment(tk.dist(self.trace[0], self.trace[1]), direction=angle,
                         final_distance=self.end_width+self.wgt.clad_width, **self.spec)

        self.add(path)

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

    wg1=Waveguide([(50,0), (250,0), (250,500)], wgt)
    tk.add(top, wg1)

    tp1 = Taper(wgt, 100.0, 0.3, **wg1.portlist["input"])
    tp2 = Taper(wgt, 100.0, 0.0, **wg1.portlist["output"])
    tk.add(top, tp1)
    tk.add(top, tp2)

    gdspy.LayoutViewer()

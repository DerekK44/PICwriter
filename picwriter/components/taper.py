#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class Taper(gdspy.Cell):
    def __init__(self, trace, wgt, end_width):
        """
        First initiate super properties (gdspy.Cell)
        trace = list of TWO points [(x1, y1), (x2, y2)] that determine orientation
        start_width = width at first trace point (determined through wgt)
        end_width = width at second trace point
        resist = type of resist used, determined through wgt
        """
        gdspy.Cell.__init__(self, "Taper--"+str(uuid.uuid4()))

        self.portlist = {}

        self.trace = trace
        self.start_width = wgt.wg_width
        self.end_width = end_width
        self.resist = wgt.resist
        self.wgt = wgt
        self.spec = {'layer': wgt.layer, 'datatype': wgt.datatype}

        self.type_check_trace()
        self.build_cell()
        self.build_ports()

    def type_check_trace(self):
        """ Round each trace value to the nearest 1e-6 -- prevents
        some typechecking errors
        """
        trace = []
        for t in self.trace:
            trace.append((round(t[0], 6), round(t[1], 5)))
        self.trace = trace
        print(self.trace)
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
        """
        Sequentially build all the geometric shapes using gdspy path functions
        then add it to the Cell
        """
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
        """ Portlist format:  (x_position, y_position)
        will maybe add on an exit angle at some point
        ¯\_(ツ)_/¯ """
        self.portlist["input"] = (self.trace[0][0], self.trace[0][1])
        self.portlist["output"] = (self.trace[1][0], self.trace[1][1])

if __name__ == "__main__":
    from picwriter.components.waveguide import Waveguide, WaveguideTemplate
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+')

    wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
    top.add(wg1)

    tp1 = Taper([(500,500), (700,500)], wgt, 0.3)
    tp2 = Taper([(50,0), (0,0)], wgt, 0.0)
    top.add(tp1)
    top.add(tp2)

    gdspy.LayoutViewer()

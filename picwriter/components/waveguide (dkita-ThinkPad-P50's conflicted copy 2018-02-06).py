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

class WaveguideTemplate:
    def __init__(self, bend_radius=50.0, wg_width=2.0, clad_width=10.0,
                 fab='ETCH', resist='+', layer=1, datatype=2):
        """
        wg_width = width of the target waveguide [um]
        bend_radius = bend radius [um]
        clad_width = spacing on either side (for '+' resist type ONLY!)
        resist = determines type for 'ETCH' type applications
        layer, datatype = layer & datatype for GDS file
        """
        self.wg_width = wg_width
        self.bend_radius = bend_radius
        self.clad_width = clad_width
        if resist != '+' and resist != '-':
            raise ValueError("Warning, invalid input for type resist in "
                             "WaveguideTemplate")
        if fab=='ETCH':
            self.resist = resist #default state assumes 'etching'
        else: #reverse waveguide type if liftoff or something else
            self.resist = '+' if resist=='-' else '-'

        self.layer = layer
        self.datatype = datatype

class Waveguide(gdspy.Cell):
    def __init__(self, trace, wgt):
        """
        First initiate super properties (gdspy.Cell)
        trace = list of points [(x1, y1), (x2, y2), ..]
        wgt = WaveguideTemplate type class
        resist = type of resist used, determined through wgt
        """
        gdspy.Cell.__init__(self,"Waveguide--"+str(uuid.uuid4()))

        self.portlist = {}

        self.trace = trace
        self.wgt = wgt
        self.resist = wgt.resist
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

        """ Make sure that each waypoint is spaced > 2*bend_radius apart
        as a conservative estimate ¯\_(ツ)_/¯
        Make sure all waypoints specify 90degree angles.  This might be
        updated in the future to allow for 45deg, or arbitrary bends
        """
        prev_dx, prev_dy = 1,1 #initialize to safe value
        for i in range(len(self.trace)-1):
            dx = abs(self.trace[i+1][0]-self.trace[i][0])
            dy = abs(self.trace[i+1][1]-self.trace[i][1])
            if (dx < 2*self.wgt.bend_radius and dy < 2*self.wgt.bend_radius) and (i != 0) and (i!=len(self.trace)-2):
                raise ValueError("Warning!  All waypoints *must* be greater than "
                                 "two waveguide bend radii apart.")
            if ((i == 0) or (i==len(self.trace)-2)) and (dx < self.wgt.bend_radius and dy < self.wgt.bend_radius):
                raise ValueError("Warning! Start and end waypoints *must be greater "
                                 "than one waveguide bend radius apart.")
            if dx>=1e-6 and dy>=1e-6:
                raise ValueError("Warning! All waypoints *must* specify turns "
                                 "that are 90degrees")
            if ((prev_dx <= 1e-6 and dx<=1e-6) or (prev_dy <= 1e-6 and dy<=1e-6)):
                raise ValueError("Warning! Unnecessary waypoint specified.  All"
                                 " waypoints must specify a valid 90deg bend")
            prev_dx, prev_dy = dx, dy

    def build_cell(self):
        """
        Sequentially build all the geometric shapes using gdspy path functions
        for waveguide, then add it to the Cell
        """
        br = self.wgt.bend_radius

        if self.resist=='-':
            path = gdspy.Path(self.wgt.wg_width, self.trace[0])
        elif self.resist=='+':
            path = gdspy.Path(self.wgt.clad_width, self.trace[0], number_of_paths=2,
                              distance=self.wgt.wg_width + self.wgt.clad_width)

        prior_direction = tk.get_direction(self.trace[0], self.trace[1])
        path.segment(tk.dist(self.trace[0], self.trace[1])-br,
                     direction=tk.get_angle(self.trace[0], self.trace[1]),
                     **self.spec)
        for i in range(len(self.trace)-2):
            direction = tk.get_direction(self.trace[i+1], self.trace[i+2])
            turn = tk.get_turn(prior_direction, direction)
            path.turn(br, turn, **self.spec)
            if tk.dist(self.trace[i+1], self.trace[i+2])-2*br > 0: #ONLY False for last points if spaced br < distance < 2br
                path.segment(tk.dist(self.trace[i+1], self.trace[i+2])-2*br,
                            **self.spec)
            prior_direction = direction
        if tk.dist(self.trace[-2],self.trace[-1]) > br:
            print("Adding segment at end "+str(tk.dist(self.trace[-2],self.trace[-1])))
            path.segment(br, **self.spec)

        self.add(path)

    def build_ports(self):
        """ Portlist format:
            example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        """
        self.portlist["input"] = {'port':(self.trace[0][0], self.trace[0][1]),
                                  'direction': tk.get_direction(self.trace[1], self.trace[0])}
        self.portlist["output"] = {'port':(self.trace[-1][0], self.trace[-1][1]),
                                   'direction':tk.get_direction(self.trace[-2], self.trace[-1])}

if __name__ == "__main__":
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+', fab="ETCH")

    wg1=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
    wg2=Waveguide([(0,0), (0,100), (-250, 100), (-250, -100)], wgt)

    top.add(wg1)
    top.add(wg2)

    gdspy.LayoutViewer()

#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy

class WaveguideTemplate:
    def __init__(self, bend_radius=50.0, wg_width=2.0, clad_width=15.0, 
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
        
class Waveguide:
    def __init__(self, cell, trace, wgt):
        """
        cell = gdspy cell to add the waveguide to
        trace = list of points [(x1, y1), (x2, y2), ..]
        wgt = WaveguideTemplate type class
        """
        self.cell = cell

        self.trace = trace
        self.wgt = wgt
        self.resist = wgt.resist
        self.spec = {'layer': wgt.layer, 'datatype': wgt.datatype}
        
        self.type_check_trace()
        
        self.build_cell()
        
    def type_check_trace(self):
        """ Round each trace value to the nearest 1e-6 -- prevents 
        some typechecking errors 
        """
        trace = []
        for t in self.trace:
            trace.append((round(t[0], 6), round(t[1], 5)))
        self.trace = trace
        print(self.trace)
        
        """ Make sure that each waypoint is spaced > 2*bend_radius apart
        as a conservative estimate ¯\_(ツ)_/¯
        Make sure all waypoints specify 90degree angles.  This might be
        updated in the future to allow for 45deg, or arbitrary bends
        """
        prev_dx, prev_dy = 1,1 #initialize to safe value
        for i in range(len(self.trace)-1):
            dx = abs(self.trace[i+1][0]-self.trace[i][0])
            dy = abs(self.trace[i+1][1]-self.trace[i][1])
            if dx < 2*self.wgt.bend_radius and dy < 2*self.wgt.bend_radius:
                raise ValueError("Warning!  All waypoints *must* be less than "
                                 "one waveguide bend radius apart.")
            if dx>=1e-6 and dy>=1e-6:
                raise ValueError("Warning! All waypoints *must* specify turns "
                                 "that are 90degrees")
            if ((prev_dx <= 1e-6 and dx<=1e-6) or (prev_dy <= 1e-6 and dy<=1e-6)):
                raise ValueError("Warning! Unnecessary waypoint specified.  All"
                                 " waypoints must specify a valid 90deg bend")
            prev_dx, prev_dy = dx, dy
                
    def get_angle(self, pt1, pt2):
        dx, dy = pt2[0]-pt1[0], pt2[1]-pt1[1]
        """ Uncomment below if we want to use real angles in the future
        and not just 90 degree bends
        if dx>0 and dy>0: #quadrant 1
            angle = np.arctan(dy/dx)
        elif dx<=0 and dy>0: #quadrant 2
            angle = 0.5*np.pi + np.arctan(-dx/dy)
        elif dx<0 and dy<=0: #quadrant 3
            angle = np.pi + np.arctan(dy/dx)
        else: #quadrant 4
            angle = 1.5*np.pi + np.arctan(-dx/dy)
        """
        if dx<=1e-6 and dy>0:
            angle=0.5*np.pi
        elif dy<=1e-6 and dx<0:
            angle=np.pi
        elif dx<=1e-6 and dy<0:
            angle=1.5*np.pi
        else:
            angle=0.0
        return angle
    
    def dist(self, pt1, pt2):
        return np.sqrt((pt2[0]-pt1[0])**2 + (pt2[1]-pt1[1])**2)
        
    def build_cell(self):
        """
        Sequentially build all the geometric shapes using gdspy path functions
        for waveguide, then add it to the cell specified
        """
        br = self.wgt.bend_radius
        
        if self.resist=='-':
            path = gdspy.Path(self.wgt.wg_width, self.trace[0])
        elif self.resist=='+':
            clad_region_width = (self.wgt.clad_width-self.wgt.wg_width)/2.0
            path = gdspy.Path(clad_region_width, self.trace[0], number_of_paths=2, 
                              distance=self.wgt.wg_width + clad_region_width)
        
        prior_angle = self.get_angle(self.trace[0], self.trace[1])
        path.segment(self.dist(self.trace[0], self.trace[1])-br, 
                     direction=prior_angle, **self.spec)
        for i in range(len(self.trace)-2):
            angle = self.get_angle(self.trace[i+1], self.trace[i+2])
            path.turn(br, angle-prior_angle, **self.spec)
            path.segment(self.dist(self.trace[i+1], self.trace[i+2])-2*br, 
                        **self.spec)
            prior_angle = angle
        path.segment(br, **self.spec)
        
        self.cell.add(path)
        
        
if __name__ == "__main__":
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+')
    
    wg = Waveguide(top, [(0,0), (250,0), (250,500), (500,500)], wgt)
    
    gdspy.LayoutViewer()
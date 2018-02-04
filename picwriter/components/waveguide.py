#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""

from __future__ import absolute_import, division, print_function, unicode_literals
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
        if fab=='ETCH':
            self.resist = resist #default state assumes 'etching'
        else: #reverse waveguide type if liftoff or something else
            self.resist = '+' if resist=='-' else '-'
            
        self.layer = layer
        self.datatype = datatype
        
class Waveguide:
    def __init__(self, name, trace, waveguide_template):
        """
        name = name of the cell created
        trace = list of points [(x1, y1), (x2, y2), ..]
        waveguide_template = WaveguideTemplate type class
        """
        self.cell = gdspy.Cell(str(name))

        self.trace = trace
        self.round_trace()
        
        self.wg_t = waveguide_template
        
        self.wg_layer = waveguide_template.wg_layer
        self.clad_layer = waveguide_template.clad_layer
        
        self.build_cell()
        
    def round_trace(self):
        """ Round each trace value to the nearest 1e-6 -- prevents 
        some typechecking errors """
        trace = []
        for t in self.trace:
            trace.append([round(t[0], 6), round(t[1], 5)])
        self.trace = trace
        
    def build_cell(self):
        """
        Build all the geometric shapes using mainly gdspy functions
        for waveguide
        """
        
if __name__ == "__main__":
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='-')
    
    wg = Waveguide('wg1', [[0,0], [0,500], [250,500]])
    top.add(wg.cell)
    
    top.show()
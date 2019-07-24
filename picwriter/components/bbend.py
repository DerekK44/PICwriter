# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk
import math

class BBend(tk.Component):
    """ Bezier Cell class.  Creates a Bezier waveguide bend that can be used in waveguide routing.  The number of points is computed based on the waveguide template grid resolution to automatically minimize grid errors.
        
        See https://en.wikipedia.org/wiki/Bezier_curve for more information.
    
        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **poles** (list): List of (x,y) pole coordinates used for routing the waveguide

        Keyword Args:
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) is the same as the 'port' input, (x2, y2) is the end of the taper, and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, wgt, poles):
        tk.Component.__init__(self, "BBend", locals())

        self.portlist = {}
        self.port = (0,0)
        
        self.input_port = (poles[0][0], poles[0][1])
        self.output_port = (poles[-1][0], poles[-1][1])
        
        self.poles = poles
        
        self.input_direction = tk.get_exact_angle(poles[1], poles[0])
        self.output_direction = tk.get_exact_angle(poles[-2], poles[-1])
        
        self.wgt = wgt
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
#        self._auto_transform_()
        
    def _bezier_function(self, t):
        # input (t) goes from 0->1
        # Returns an (x,y) tuple
        n = len(self.poles)-1
        x, y = 0,0
        for i in range(n+1):
            coeff = math.factorial(n)/(math.factorial(i)*math.factorial(n-i))
            x += coeff*((1-t)**(n-i)) * (t**i) * self.poles[i][0]
            y += coeff*((1-t)**(n-i)) * (t**i) * self.poles[i][1]
        return (x,y)

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell

        # Add waveguide s-bend        
        wg = gdspy.Path(self.wgt.wg_width, (0,0))
        wg.parametric(self._bezier_function, tolerance=self.wgt.grid/2.0, max_points=199, **self.wg_spec)
        print(wg.x)
        print(wg.y)
        self.add(wg)
        
        # Add cladding s-bend
        for i in range(len(self.wgt.waveguide_stack)-1):
            cur_width = self.wgt.waveguide_stack[i+1][0]
            cur_spec = {'layer': self.wgt.waveguide_stack[i+1][1][0], 'datatype': self.wgt.waveguide_stack[i+1][1][1]}
            
            clad = gdspy.Path(cur_width, (0,0))
            clad.parametric(self._bezier_function, tolerance=self.wgt.grid/2.0, max_points=199, **cur_spec)
            self.add(clad)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':self.input_port, 'direction':self.input_direction}
        self.portlist["output"] = {'port':self.output_port, 'direction':self.output_direction}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+')

    wg1=Waveguide([(0,0), (100,0)], wgt)
    tk.add(top, wg1)

    bb1 = BBend(wgt, [(100,0),
                      (200,0),
                      (100,100),
                      (200,100)])
    tk.add(top, bb1)
    
    x,y = bb1.portlist["output"]["port"]
    wg2 = Waveguide([(x,y), (x+100, y)], wgt)
    tk.add(top, wg2)

    gdspy.LayoutViewer(cells=top, depth=3)
#    gdspy.write_gds('sbend.gds', unit=1.0e-6, precision=1.0e-9)

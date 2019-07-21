# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk

class SBend(tk.Component):
    """ Sinusoidal S-shaped Bend Cell class.  Creates a sinusoidal waveguide bend that can be used in waveguide routing.  The number of points is computed based on the waveguide template grid resolution to automatically minimize grid errors.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **height** (float): Height of the S-bend
           * **length** (float): Length of the S-bend

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
    def __init__(self, wgt, height, length, port=(0,0), direction='EAST'):
        tk.Component.__init__(self, "SBend", locals())

        self.portlist = {}
        self.direction = direction

        self.port = port
        self.input_port = (0,0)
        self.output_port = (length, height)
        
        self.wgt = wgt
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()
        
    def __sine_function(self, t):
        # input (t) goes from 0->1
        # Returns an (x,y) tuple
        return (self.output_port[0]*t, 0.5*self.output_port[1]*np.sin(np.pi*t-0.5*np.pi) + 0.5*self.output_port[1])

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell

        # Add waveguide s-bend        
        wg = gdspy.Path(self.wgt.wg_width, (0,0))
        wg.parametric(self.__sine_function, tolerance=self.wgt.grid/2.0, max_points=199, **self.wg_spec)
        self.add(wg)
        
        # Add cladding s-bend
        for i in range(len(self.wgt.waveguide_stack)-1):
            cur_width = self.wgt.waveguide_stack[i+1][0]
            cur_spec = {'layer': self.wgt.waveguide_stack[i+1][1][0], 'datatype': self.wgt.waveguide_stack[i+1][1][1]}
            
            clad = gdspy.Path(cur_width, (0,0))
            clad.parametric(self.__sine_function, tolerance=self.wgt.grid/2.0, max_points=199, **cur_spec)
            self.add(clad)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':self.input_port, 'direction':'WEST'}
        self.portlist["output"] = {'port':self.output_port, 'direction':'EAST'}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+')

    wg1=Waveguide([(0,0), (100,0)], wgt)
    tk.add(top, wg1)

    sb1 = SBend(wgt, 100.0, 200.0, **wg1.portlist["output"])
    tk.add(top, sb1)
    
    x,y = sb1.portlist["output"]["port"]
    wg2 = Waveguide([(x,y), (x+100, y)], wgt)
    tk.add(top, wg2)

    gdspy.LayoutViewer(cells=top, depth=3)
#    gdspy.write_gds('sbend.gds', unit=1.0e-6, precision=1.0e-9)

# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk

class StripSlotMMIConverter(tk.Component):
    """ Strip-to-Slot MMI Converter Cell class.  For more information on this specific type of strip to slot mode converter, please see the original papers at https://doi.org/10.1364/OL.39.005665 and https://doi.org/10.1364/OE.24.007347.

        Args:
           * **wgt_input** (WaveguideTemplate):  WaveguideTemplate object for the input waveguide (should be either of type `strip` or `slot`).
           * **wgt_output** (WaveguideTemplate):  WaveguideTemplate object for the output waveguide (should be either of type `strip` or `slot`, opposite of the input type).
           * **w_mmi** (float): Width of the MMI region.
           * **l_mmi** (float): Length of the MMI region.
           * **length** (float): Length of the entire mode converter (MMI region + tapered region on slot waveguide side).

        Keyword Args:
           * **input_strip** (Boolean): If `True`, sets the input port to be the strip waveguide side.  If `False`, slot waveguide is on the input.  Defaults to `None`, in which case the input port waveguide template is used to choose.
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
    def __init__(self, wgt_input, wgt_output, w_mmi, l_mmi, length, input_strip=None, port=(0,0), direction='EAST'):
        tk.Component.__init__(self, "StripSlotMMIConverter", locals())

        self.portlist = {}

        if (not isinstance(input_strip, bool)) and (input_strip != None):
            raise ValueError("Invalid input provided for `input_strip`.  Please specify a boolean.")
        if input_strip == None:
            #Auto-detect based on wgt_input
            self.input_strip = (wgt_input.wg_type=='strip' or wgt_input.wg_type=='swg')
        else:
            #User-override
            self.input_strip = input_strip

        if self.input_strip:
            self.wgt_strip = wgt_input
            self.wgt_slot = wgt_output
        else:
            self.wgt_strip = wgt_output
            self.wgt_slot = wgt_input
        self.wg_spec = {'layer': wgt_output.wg_layer, 'datatype': wgt_output.wg_datatype}
        self.clad_spec = {'layer': wgt_output.clad_layer, 'datatype': wgt_output.clad_datatype}

        self.length = length
        self.w_mmi = w_mmi
        self.l_mmi = l_mmi

        self.port = port
        self.direction = direction

        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell

        # Add MMI region
        path_mmi = gdspy.Path(self.w_mmi, (0,0))
        path_mmi.segment(self.l_mmi, direction=0, **self.wg_spec)

        print("path_mmi_coords = "+str((path_mmi.x, path_mmi.y)))

        # Add slot tapered region
        path_taper = gdspy.Path((self.w_mmi - self.wgt_slot.slot)/2.0,
                                initial_point=(path_mmi.x, path_mmi.y),
                                number_of_paths=2,
                                distance=(self.w_mmi + self.wgt_slot.slot)/2.0)
        path_taper.segment(self.length - self.l_mmi,
                           final_width = self.wgt_slot.rail,
                           final_distance = self.wgt_slot.rail_dist,
                           direction=0,
                           **self.wg_spec)

        # Cladding for waveguide taper
        path_clad = gdspy.Path(2*self.wgt_strip.clad_width+self.wgt_strip.wg_width, (0,0))
        path_clad.segment(self.length, final_width=2*self.wgt_slot.clad_width+self.wgt_slot.wg_width, direction=0, **self.clad_spec)
        
        if not self.input_strip:
            center_pt = (self.length/2.0, 0)
            path_mmi.rotate(np.pi, center_pt)
            path_taper.rotate(np.pi, center_pt)
            path_clad.rotate(np.pi, center_pt)
        
        self.add(path_mmi)
        self.add(path_taper)
        self.add(path_clad)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':(0,0), 'direction':'WEST'}
        self.portlist["output"] = {'port':(self.length,0), 'direction':'EAST'}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt_slot = WaveguideTemplate(bend_radius=50, wg_type='strip', wg_width=0.7)
    wgt_strip = WaveguideTemplate(bend_radius=50, wg_type='slot', wg_width=0.7, slot=0.2)

    wg1=Waveguide([(0,0), (100,30)], wgt_strip)
    tk.add(top, wg1)

    ycoup = StripSlotMMIConverter(wgt_strip, wgt_slot, 2.5, 6.0, 20.0, **wg1.portlist["output"])
    tk.add(top, ycoup)

    (x1,y1)=ycoup.portlist["output"]["port"]
    wg2=Waveguide([(x1, y1), (x1+100, y1)], wgt_slot)
    tk.add(top, wg2)

    gdspy.LayoutViewer(cells=top)
#    gdspy.write_gds('StripSlotMMIConverter.gds', unit=1.0e-6, precision=1.0e-9)

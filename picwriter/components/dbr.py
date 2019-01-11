# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class DBR(gdspy.Cell):
    """ Distributed Bragg Reflector Cell class (subclass of gdspy.Cell).  Tapers the input waveguide to a periodic waveguide structure with varying width (1-D photonic crystal).

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length** (float): Length of the DBR region.
           * **period** (float): Period of the repeated unit.
           * **dc** (float): Duty cycle of the repeated unit (must be a float between 0 and 1.0).
           * **w_phc** (float): Width of the thin section of the waveguide.  w_phc = 0 corresponds to disconnected periodic blocks.

        Keyword Args:
           * **taper_length** (float): Length of the taper between the input/output waveguide and the DBR region.  Defaults to 20.0.
           * **fins** (boolean): If `True`, adds fins to the input/output waveguides.  In this case a different template for the component must be specified.  This feature is useful when performing electron-beam lithography and using different beam currents for fine features (helps to reduce stitching errors).  Defaults to `False`
           * **fin_size** ((x,y) Tuple): Specifies the x- and y-size of the `fins`.  Defaults to 200 nm x 50 nm
           * **dbr_wgt** (WaveguideTemplate): If `fins` above is True, a WaveguideTemplate (dbr_wgt) must be specified.  This defines the layertype / datatype of the DBR (which will be separate from the input/output waveguides).  Defaults to `None`
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) is the same as the 'port' input, (x2, y2) is the end of the DBR, and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, wgt, length, period, dc, w_phc, taper_length=20.0, fins=False, fin_size = (0.2,0.05), dbr_wgt=None, port=(0,0), direction='EAST'):
        gdspy.Cell.__init__(self, "DBR--"+str(uuid.uuid4()))

        self.portlist = {}

        self.port = port
        self.trace=[port, tk.translate_point(port, length+2*taper_length, direction)]
        self.direction = direction
        self.length = length
        self.taper_length = taper_length
        self.period = period
        self.dc = dc
        self.w_phc = w_phc
        self.fins = fins
        self.fin_size = fin_size

        if fins:
            self.wgt = dbr_wgt
            self.side_wgt = wgt
            self.wg_spec = {'layer': dbr_wgt.wg_layer, 'datatype': dbr_wgt.wg_datatype}
            self.clad_spec = {'layer': dbr_wgt.clad_layer, 'datatype': dbr_wgt.clad_datatype}
            self.fin_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
            if dbr_wgt is None:
                raise ValueError("Warning! A waveguide template for the DBR (dbr_wgt) must be specified.")
        else:
            self.wgt = wgt
            self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
            self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

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

        """ Make sure the photonic crystal waveguide width is smaller than the waveguide width """
        if self.w_phc > self.wgt.wg_width:
            raise ValueError("Warning! The w_phc parameter must be smaller than the waveguide template wg_width.")

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        angle = tk.get_exact_angle(self.trace[0], self.trace[1])
        # Add waveguide tapers leading to DBR region
        taper = gdspy.Path(self.wgt.wg_width, self.trace[0])
        taper.segment(self.taper_length, direction=angle, final_width=self.w_phc, **self.wg_spec)
        taper.segment(self.length, **self.wg_spec)
        taper.segment(self.taper_length, final_width=self.wgt.wg_width, **self.wg_spec)
        # Cladding for DBR region
        clad = gdspy.Path(2*self.wgt.clad_width+self.wgt.wg_width, self.trace[0])
        clad.segment(tk.dist(self.trace[0], self.trace[1]), direction=angle, **self.clad_spec)

        self.add(taper)
        self.add(clad)

        """ Now add the periodic PhC components """
        num_blocks = (2*self.taper_length + self.length)//self.period
        blockx = self.period*self.dc
        startx = self.trace[0][0] + self.taper_length + self.length/2.0 -(num_blocks-1)*self.period/2.0 - blockx/2.0
        y0 = self.trace[0][1]
        block_list = []
        for i in range(int(num_blocks)):
            x = startx + i*self.period
            block_list.append(gdspy.Rectangle((x, y0-self.wgt.wg_width/2.0), (x+blockx, y0+self.wgt.wg_width/2.0), **self.wg_spec))

        """ And add the 'fins' if self.fins==True """
        if self.fins:
            num_fins = self.wgt.wg_width//(2*self.fin_size[1])
            x0, y0 = self.trace[0][0], self.trace[0][1] - num_fins*(2*self.fin_size[1])/2.0 + self.fin_size[1]/2.0
            xend = self.trace[0][0] + 2*self.taper_length + self.length
            for i in range(int(num_fins)):
                y = y0 + i*2*self.fin_size[1]
                block_list.append(gdspy.Rectangle((x0, y), (x0+self.fin_size[0], y+self.fin_size[1]), **self.fin_spec))
                block_list.append(gdspy.Rectangle((xend-self.fin_size[0], y), (xend, y+self.fin_size[1]), **self.fin_spec))

        angle=0
        if self.direction=="NORTH":
            angle=np.pi/2.0
        elif self.direction=="WEST":
            angle=np.pi
        elif self.direction=="SOUTH":
            angle=-np.pi/2.0
        elif isinstance(self.direction, float):
            angle = self.direction
        for block in block_list:
            block.rotate(angle, self.trace[0])
            self.add(block)

    def build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':self.trace[0], 'direction':tk.flip_direction(self.direction)}
        self.portlist["output"] = {'port':self.trace[1], 'direction':self.direction}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+')
    dbr_wgt = WaveguideTemplate(bend_radius=50, resist='+', wg_layer=3, wg_datatype=0)

    wg1=Waveguide([(0,0), (100,0)], wgt)
    tk.add(top, wg1)

    dbr1 = DBR(wgt, 10.0, 0.85, 0.5, 0.4, fins=True, dbr_wgt=dbr_wgt, **wg1.portlist["output"])
    tk.add(top, dbr1)

    (x1, y1) = dbr1.portlist["output"]["port"]
    wg2=Waveguide([(x1,y1),
                   (x1+100,y1),
                   (x1+100,y1+100)], wgt)
    tk.add(top, wg2)

    dbr2 = DBR(wgt, 10.0, 0.85, 0.5, 0.6, fins=True, dbr_wgt=dbr_wgt, **wg2.portlist["output"])
    tk.add(top, dbr2)

    (x2, y2) = dbr2.portlist["output"]["port"]
    wg3=Waveguide([(x2,y2), (x2, y2+100.0),(x2+100,y2+200),(x2+100,y2+300)], wgt)
    tk.add(top, wg3)

    gdspy.LayoutViewer()
    # gdspy.write_gds('dbr.gds', unit=1.0e-6, precision=1.0e-9)

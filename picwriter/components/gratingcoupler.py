# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class GratingCouplerStraight(gdspy.Cell):
    """ Straight Grating Coupler Cell class (subclass of gdspy.Cell).

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object

        Keyword Args:
           * **port** (tuple): Cartesian coordinate of the input port
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)
           * **width** (float): Width of the grating region
           * **length** (float): Length of the grating region
           * **taper_length** (float): Length of the taper before the grating coupler
           * **period** (float): Grating period
           * **dutycycle** (float): dutycycle, determines the size of the 'gap' by dutycycle=(period-gap)/period.

        Members:
           **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           portlist['output'] = {'port': (x1,y1), 'direction': 'dir1'}

        Where in the above (x1,y1) is the same as the 'port' input, and 'dir1' is of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, wgt, port=(0,0), direction='EAST', width=20, length=50,
                 taper_length=20, period=1.0, dutycycle=0.5):
        gdspy.Cell.__init__(self, "GratingCouplerStraight--"+str(uuid.uuid4()))

        self.portlist = {}

        self.port = port
        self.direction = direction
        self.wgt = wgt
        self.resist = wgt.resist

        self.width = width
        self.length = length
        self.taper_length = taper_length
        self.period = period
        if dutycycle>1.0 or dutycycle<0.0:
            raise ValueError("Warning! Dutycycle *must* specify a valid number "
                             "between 0 and 1.")
        self.dc = dutycycle
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.build_cell()
        self.build_ports()

    def build_cell(self):
        #Sequentially build all the geometric shapes using gdspy path functions
        #then add it to the Cell
        num_teeth = int(self.length//self.period)
        """ Create a straight grating GratingCoupler
        """
        gap = self.period - (self.period*self.dc)
        path = gdspy.Path(self.wgt.wg_width, self.port)
        path.segment(self.taper_length, direction='+y',
                     final_width=self.width, **self.wg_spec)
        teeth = gdspy.L1Path((self.port[0]-0.5*self.width, gap+self.taper_length+self.port[1]+0.5*(num_teeth-1+self.dc)*self.period),
                            '+x', self.period*self.dc, [self.width], [], num_teeth, self.period, **self.wg_spec)

        clad_path = gdspy.Path(self.wgt.wg_width + 2*self.wgt.clad_width, self.port)
        clad_path.segment(self.taper_length, direction='+y',
                     final_width=self.width+2*self.wgt.clad_width, **self.clad_spec)
        clad_path.segment(self.length, direction='+y', **self.clad_spec)

        if self.direction=="WEST":
            teeth.rotate(np.pi/2.0, self.port)
            path.rotate(np.pi/2.0, self.port)
            clad_path.rotate(np.pi/2.0, self.port)
        elif self.direction=="SOUTH":
            teeth.rotate(np.pi, self.port)
            path.rotate(np.pi, self.port)
            clad_path.rotate(np.pi, self.port)
        elif self.direction=="EAST":
            teeth.rotate(-np.pi/2.0, self.port)
            path.rotate(-np.pi/2.0, self.port)
            clad_path.rotate(-np.pi/2.0, self.port)
        elif isinstance(self.direction, float):
            teeth.rotate(self.direction - np.pi/2.0, self.port)
            path.rotate(self.direction -np.pi/2.0, self.port)
            clad_path.rotate(self.direction-np.pi/2.0, self.port)
        self.add(teeth)
        self.add(path)
        self.add(clad_path)

    def build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["output"] = {'port':self.port, 'direction':tk.flip_direction(self.direction)}

class GratingCouplerFocusing(gdspy.Cell):
    """ Standard Focusing Grating Coupler Cell class (subclass of gdspy.Cell).

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object

        Keyword Args:
           * **port** (tuple): Cartesian coordinate of the input port
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)
           * **focus_distance** (float): Distance over which the light is focused to the waveguide port
           * **width** (float): Width of the grating region
           * **length** (float): Length of the grating region
           * **period** (float): Grating period
           * **dutycycle** (float): dutycycle, determines the size of the 'gap' by dutycycle=(period-gap)/period.
           * **wavelength** (float): free space wavelength of the light
           * **sin_theta** (float): sine of the incident angle
           * **evaluations** (int): number of parameteric evaluations of path.parametric

        Members:
           **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           portlist['output'] = {'port': (x1,y1), 'direction': 'dir1'}

        Where in the above (x1,y1) is the same as the 'port' input, and 'dir1' is of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, wgt, port=(0,0), direction='EAST', focus_distance=None,
                    width=20, length=50, period=1.0, dutycycle=0.5,
                    wavelength=1.55, sin_theta=np.sin(np.pi * 8 / 180),
                    evaluations=99):
        gdspy.Cell.__init__(self, "GratingCouplerFocusing--"+str(uuid.uuid4()))

        self.portlist = {}

        self.port = port
        self.direction = direction
        self.wgt = wgt
        self.resist = wgt.resist

        self.focus_distance = focus_distance
        self.width = width
        self.length = length
        self.period = period
        if dutycycle>1.0 or dutycycle<0.0:
            raise ValueError("Warning! Dutycycle *must* specify a valid number "
                             "between 0 and 1.")
        self.dc = dutycycle
        self.wavelength = wavelength
        self.sin_theta = sin_theta
        self.evaluations = evaluations
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.build_cell()
        self.build_ports()

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # then add it to the Cell

        num_teeth = int(self.length//self.period)
        if self.focus_distance < self.width/2.0 - self.period:
            raise ValueError("Warning! The focus_distance is smaller than the allowed value of width/2.0 - period.")
        neff = self.wavelength / float(self.period) + self.sin_theta
        qmin = int(self.focus_distance / float(self.period) + 0.5)
        max_points = 199
        c3 = neff**2 - self.sin_theta**2
        w = 0.5 * self.width
        path = gdspy.Path(self.wgt.clad_width, self.port, number_of_paths=2,
                          distance=self.wgt.wg_width + self.wgt.clad_width)

        teeth = gdspy.Path(self.period * self.dc, self.port)
        for q in range(qmin, qmin + num_teeth):
            c1 = q * self.wavelength * self.sin_theta
            c2 = (q * self.wavelength)**2
            teeth.parametric(lambda t: (self.width * t - w, (c1 + neff
                            * np.sqrt(c2 - c3 * (self.width * t - w)**2)) / c3),
                            number_of_evaluations=self.evaluations,
                            max_points=max_points,
                            **self.wg_spec)
            teeth.x = self.port[0]
            teeth.y = self.port[1]
        teeth.polygons[0] = np.vstack(
            (teeth.polygons[0][:self.evaluations, :],
             ([(self.port[0] + 0.5 * self.wgt.wg_width, self.port[1]),
               (self.port[0] - 0.5 * self.wgt.wg_width, self.port[1])])))
        teeth.fracture()

        clad_path = gdspy.Path(self.wgt.wg_width + 2*self.wgt.clad_width, self.port)
        clad_path.segment(self.focus_distance, direction='+y',
                     final_width=self.width+2*self.wgt.clad_width, **self.clad_spec)
        clad_path.segment(self.length, direction='+y', **self.clad_spec)

        if self.direction=="WEST":
            teeth.rotate(np.pi/2.0, self.port)
            path.rotate(np.pi/2.0, self.port)
            clad_path.rotate(np.pi/2.0, self.port)
        if self.direction=="SOUTH":
            teeth.rotate(np.pi, self.port)
            path.rotate(np.pi, self.port)
            clad_path.rotate(np.pi, self.port)
        if self.direction=="EAST":
            teeth.rotate(-np.pi/2.0, self.port)
            path.rotate(-np.pi/2.0, self.port)
            clad_path.rotate(-np.pi/2.0, self.port)
        elif isinstance(self.direction, float):
            teeth.rotate(self.direction - np.pi/2.0, self.port)
            path.rotate(self.direction -np.pi/2.0, self.port)
            clad_path.rotate(self.direction-np.pi/2.0, self.port)
        self.add(teeth)
        self.add(path)
        self.add(clad_path)

    def build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["output"] = {'port':self.port, 'direction':tk.flip_direction(self.direction)}

if __name__ == "__main__":
    from picwriter.components.waveguide import Waveguide, WaveguideTemplate
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist='+', fab='ETCH')

    wg1=Waveguide([(0,0), (250,0), (250,500), (500,500)], wgt)
    tk.add(top, wg1)

    gc1 = GratingCouplerStraight(wgt, width=20, length=50, taper_length=20, period=1.0, dutycycle=0.7, **wg1.portlist["output"])
    tk.add(top, gc1)

    gc2 = GratingCouplerFocusing(wgt, focus_distance=20.0, width=20, length=50, period=1.0, dutycycle=0.7, **wg1.portlist["input"])
    tk.add(top,gc2)

    gdspy.LayoutViewer()
    # gdspy.write_gds('gratingcoupler.gds', unit=1.0e-6, precision=1.0e-9)

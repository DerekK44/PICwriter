# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk

class GratingCoupler(tk.Component):
    """ Typical Grating Coupler Cell class.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object

        Keyword Args:
           * **port** (tuple): Cartesian coordinate of the input port
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)
           * **theta** (float): Angle of the waveguide.  Defaults to pi/4.0
           * **length** (float): Length of the total grating coupler region, measured from the output port.  Defaults to 30.0
           * **taper_length** (float): Length of the taper before the grating coupler.  Defaults to 10.0
           * **period** (float): Grating period.  Defaults to 1.0
           * **dutycycle** (float): dutycycle, determines the size of the 'gap' by dutycycle=(period-gap)/period.  Defaults to 0.7
           * **ridge** (boolean): If True, adds another layer to the grating coupler that can be used for partial etched gratings
           * **ridge_layers** (tuple): Tuple specifying the layer/datatype of the ridge region.  Defaults to (3,0)
           * **teeth_list** (list): Can optionally pass a list of (gap, width) tuples to be used as the gap and teeth widths for irregularly spaced gratings.  For example, [(0.6, 0.2), (0.7, 0.3), ...] would be a gap of 0.6, then a tooth of width 0.2, then gap of 0.7 and tooth of 0.3, and so on.  Overrides *period*, *dutycycle*, and *length*.  Defaults to None.
           
        Members:
           **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           portlist['output'] = {'port': (x1,y1), 'direction': 'dir1'}

        Where in the above (x1,y1) is the same as the 'port' input, and 'dir1' is of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, 
                 wgt, 
                 theta=np.pi/4.0, 
                 length=30.0,
                 taper_length = 10.0,
                 period=1.0, 
                 dutycycle=0.7, 
                 ridge=False,
                 ridge_layers=(3,0),
                 teeth_list = None,
                 port=(0,0), 
                 direction='EAST'):
        tk.Component.__init__(self, "GratingCoupler", locals())

        self.portlist = {}
        self.port = port
        self.direction = direction
        
        self.wgt = wgt
        self.theta = theta
        self.length = length
        self.taper_length = taper_length
        self.period = period
        if dutycycle>1.0 or dutycycle<0.0:
            raise ValueError("Warning! Dutycycle *must* specify a valid number "
                             "between 0 and 1.")
        self.dc = dutycycle
        
        self.ridge = ridge
        self.ridge_layers = ridge_layers
        
        self.teeth_list = teeth_list
        if teeth_list != None:
            self.length = self.taper_length + sum([l[0]+l[1] for l in teeth_list])
        
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()
        
    def __build_cell(self):
        #Sequentially build all the geometric shapes using gdspy path functions
        #then add it to the Cell
        """ Create a straight grating GratingCoupler
        """
        
        # First the input taper
        taper = gdspy.Round((0,0),
                            radius=self.taper_length,
                            inner_radius=0,
                            initial_angle=-self.theta/2.0,
                            final_angle=+self.theta/2.0,
                            number_of_points=self.wgt.get_num_points_curve(self.theta, self.taper_length)+1,
                            **self.wg_spec)
        
        if self.ridge:
            ridge_region = gdspy.Round((0,0),
                                        radius=self.length,
                                        inner_radius=0,
                                        initial_angle=-self.theta/2.0,
                                        final_angle=+self.theta/2.0,
                                        number_of_points=self.wgt.get_num_points_curve(self.theta, self.taper_length)+1,
                                        layer=self.ridge_layers[0],
                                        datatype=self.ridge_layers[1])
            self.add(ridge_region)
        
        # Then the input waveguide stub
        stub_length = (self.wgt.wg_width/2.0)/np.tan(self.theta/2.0)
        stub = gdspy.Path(self.wgt.wg_width, (0,0))
        stub.segment(stub_length+0.1, **self.wg_spec)
        self.add(stub)
        
        if self.teeth_list == None:
            """ Fixed pitch grating coupler """
            num_teeth = int((self.length-self.taper_length)//self.period)
            gap = self.period - (self.period*self.dc)
            for i in range(num_teeth):
                inner_rad = self.taper_length + i*self.period + gap
                outer_rad = self.taper_length + (i+1)*self.period
                line = gdspy.Round((0,0),
                                   radius=outer_rad,
                                   inner_radius=inner_rad,
                                   initial_angle=-self.theta/2.0,
                                   final_angle=+self.theta/2.0,
                                   number_of_points=2*self.wgt.get_num_points_curve(self.theta, outer_rad),
                                   **self.wg_spec)
                self.add(line)
        else:
            """ User specified gap/width grating coupler """
            cur_pos = self.taper_length
            for i in range(len(self.teeth_list)):
                (gap, width) = self.teeth_list[i]
                inner_rad = cur_pos + gap
                outer_rad = cur_pos + gap + width
                line = gdspy.Round((0,0),
                                   radius=outer_rad,
                                   inner_radius=inner_rad,
                                   initial_angle=-self.theta/2.0,
                                   final_angle=+self.theta/2.0,
                                   number_of_points=2*self.wgt.get_num_points_curve(self.theta, outer_rad),
                                   **self.wg_spec)
                self.add(line)
                cur_pos = outer_rad

        clad_path = gdspy.Path(self.wgt.wg_width + 2*self.wgt.clad_width, (0,0))
        clad_path.segment(self.length, direction='+x',
                          final_width=2*np.sin(self.theta/2.0)*self.length+2*self.wgt.clad_width, **self.clad_spec)
        clad_path.segment(self.wgt.clad_width, **self.clad_spec)

        self.add(taper)
        self.add(clad_path)

    def __build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["output"] = {'port':(0,0), 'direction':'WEST'}

class GratingCouplerStraight(tk.Component):
    """ Straight Grating Coupler Cell class.

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
        tk.Component.__init__(self, "GratingCouplerStraight", locals())

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

        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def __build_cell(self):
        #Sequentially build all the geometric shapes using gdspy path functions
        #then add it to the Cell
        num_teeth = int(self.length//self.period)
        """ Create a straight grating GratingCoupler
        """
        gap = self.period - (self.period*self.dc)
        path = gdspy.Path(self.wgt.wg_width, (0,0))
        path.segment(self.taper_length, direction='+x',
                     final_width=self.width, **self.wg_spec)
        teeth = gdspy.L1Path((gap+self.taper_length+0.5*(num_teeth-1+self.dc)*self.period, -0.5*self.width),
                            '+y', self.period*self.dc, [self.width], [], num_teeth, self.period, **self.wg_spec)

        clad_path = gdspy.Path(self.wgt.wg_width + 2*self.wgt.clad_width, (0,0))
        clad_path.segment(self.taper_length, direction='+x',
                     final_width=self.width+2*self.wgt.clad_width, **self.clad_spec)
        clad_path.segment(self.length, direction='+x', **self.clad_spec)

        self.add(teeth)
        self.add(path)
        self.add(clad_path)

    def __build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["output"] = {'port':(0,0), 'direction':'WEST'}

class GratingCouplerFocusing(tk.Component):
    """ Standard Focusing Grating Coupler Cell class.

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
        tk.Component.__init__(self, "GratingCouplerFocusing", locals())

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

        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def __build_cell(self):
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
        path = gdspy.Path(self.wgt.clad_width, (0,0), number_of_paths=2,
                          distance=self.wgt.wg_width + self.wgt.clad_width)

        teeth = gdspy.Path(self.period * self.dc, (0,0))
        for q in range(qmin, qmin + num_teeth):
            c1 = q * self.wavelength * self.sin_theta
            c2 = (q * self.wavelength)**2
            teeth.parametric(lambda t: (self.width * t - w, (c1 + neff
                            * np.sqrt(c2 - c3 * (self.width * t - w)**2)) / c3),
                            number_of_evaluations=self.evaluations,
                            max_points=max_points,
                            **self.wg_spec)
            teeth.x = 0
            teeth.y = 0
        teeth.polygons[0] = np.vstack(
            (teeth.polygons[0][:self.evaluations, :],
             ([( 0.5 * self.wgt.wg_width, 0),
               (-0.5 * self.wgt.wg_width, 0)])))
        teeth.fracture()

        clad_path = gdspy.Path(self.wgt.wg_width + 2*self.wgt.clad_width, (0,0))
        clad_path.segment(self.focus_distance, direction='+y',
                     final_width=self.width+2*self.wgt.clad_width, **self.clad_spec)
        clad_path.segment(self.length, direction='+y', **self.clad_spec)

        
        teeth.rotate(-np.pi/2.0, (0,0))
        path.rotate(-np.pi/2.0, (0,0))
        clad_path.rotate(-np.pi/2.0, (0,0))
        
        self.add(teeth)
        self.add(path)
        self.add(clad_path)

    def __build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["output"] = {'port':(0,0), 'direction':'WEST'}

if __name__ == "__main__":
    from picwriter.components.waveguide import Waveguide, WaveguideTemplate
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, wg_width=0.5, resist='+', fab='ETCH')

    wg1=Waveguide([(0,0), (250,0), (250,500), (500,500)], wgt)
    tk.add(top, wg1)
    
    gc1 = GratingCoupler(wgt,
                         theta=np.pi/5.0,
                         length=40.0,
                         taper_length=20.0,
                         period=1.0,
                         dutycycle=0.6,
                         ridge=True,
                         **wg1.portlist["output"])
    tk.add(top, gc1)
    
    teeth_list = [(0.2, 0.6), (0.25, 0.55), (0.3, 0.5), (0.25, 0.55), 
                  (0.2, 0.6), (0.25, 0.55), (0.3, 0.5), (0.25, 0.55),
                  (0.2, 0.6), (0.25, 0.55), (0.3, 0.5), (0.25, 0.55),
                  (0.2, 0.6), (0.25, 0.55), (0.3, 0.5), (0.25, 0.55),
                  (0.2, 0.6), (0.25, 0.55), (0.3, 0.5), (0.25, 0.55),
                  (0.2, 0.6), (0.25, 0.55), (0.3, 0.5), (0.25, 0.55),
                  (0.2, 0.6), (0.25, 0.55), (0.3, 0.5), (0.25, 0.55)]
    
    gc2 = GratingCoupler(wgt,
                         theta=np.pi/4.0,
                         length=40.0,
                         taper_length=20.0,
                         period=1.0,
                         dutycycle=0.6,
                         ridge=True,
                         teeth_list = teeth_list,
                         **wg1.portlist["input"])
    tk.add(top, gc2)

#    gc1 = GratingCouplerStraight(wgt, width=20, length=50, taper_length=20, period=1.0, dutycycle=0.7, **wg1.portlist["output"])
#    tk.add(top, gc1)
#
#    gc2 = GratingCouplerFocusing(wgt, focus_distance=20.0, width=20, length=50, period=1.0, dutycycle=0.7, **wg1.portlist["input"])
#    tk.add(top,gc2)

#    gdspy.LayoutViewer()
    gdspy.write_gds('gratingcoupler.gds', unit=1.0e-6, precision=1.0e-9)

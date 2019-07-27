# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
from scipy.special import fresnel
import gdspy
import picwriter.toolkit as tk

class EBend(tk.Component):
    """ Euler shaped Bend Cell class.  Creates a generic Euler waveguide bend that can be used in waveguide routing.  The number of points is computed based on the waveguide template grid resolution to automatically minimize grid errors.
    This class can be automatically called and implemented during waveguide routing by passing `euler_bend=True` to a WaveguideTemplate object.  The smallest radius of curvature on the Euler bend is set to be the `bend_radius` value given by the WaveguideTemplate object passed to this class.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object.  Bend radius is extracted from this object.
           * **turnby** (float): Angle in radians, must be between +np.pi and -np.pi.  It's not recommended that you give a value of np.pi (for 180 bends) as this will result in divergent trig identities.  Instead, use two bends with turnby=Pi/2.

        Keyword Args:
           * **start_width** (float): If a value is provided, overrides the initial waveguide width (otherwise the width is taken from the WaveguideTemplate object).  Currently only works for strip waveguides.
           * **end_width** (float): If a value is provided, overrides the final waveguide width (otherwise the width is taken from the WaveguideTemplate object).  Currently only works for strip waveguides.
           * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)
           * **vertex** (tuple): If a value for `vertex` is given (Cartesian x,y coordinate), then the Euler bend is placed at this location, bypassing the normal `port` value.  This is used in waypoint routing.
           
        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

        Where in the above (x1,y1) is the same as the 'port' input, (x2, y2) is the end of the taper, and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """
    def __init__(self, wgt, turnby, start_width=None, end_width=None, port=(0,0), direction='EAST', vertex=None):
        tk.Component.__init__(self, "EBend", locals())

        # Protected variables
        self.portlist = {}
        self.direction = direction
        # End protected variables
        
        if start_width != None:
            self.start_width = start_width
        else:
            self.start_width = wgt.wg_width
        if end_width != None:
            self.end_width = end_width
        else:
            self.end_width = wgt.wg_width
        
        self.wgt = wgt
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}

        self.input_port = (0,0)        
        if turnby==np.pi: #Edge case, make sure +np.pi doesn't get turned into -np.pi
            self.turnby = turnby
        else: #Normalize so turnby is definitely between -np.pi and +np.pi
            self.turnby = (turnby + np.pi)%(2*np.pi) - np.pi

        self.output_direction = self.turnby
        
        self.sign = np.sign(self.turnby)
        if abs(self.turnby) <= np.pi/2.0:
            # Obtuse angle
            # Compute the value of t analytically
            self.t = np.sqrt( (2/np.pi) * abs(self.turnby/2.0) )
            dy, dx = fresnel(self.t)

            output_x_norm = dx + dx*np.cos(abs(self.turnby)) - (-dy)*np.sin(abs(self.turnby))
            output_y_norm = dy + dx*np.sin(abs(self.turnby)) + (-dy)*np.cos(abs(self.turnby))
            
            self.scale_factor = self.wgt.bend_radius/self.__get_radius_of_curvature()
            
            self.output_port = (self.scale_factor*output_x_norm, self.sign*self.scale_factor*output_y_norm)
            
            dist_to_vertex_norm = output_x_norm - (output_y_norm/np.tan(abs(self.turnby)))
            self.dist_to_vertex = dist_to_vertex_norm*self.scale_factor
            
        else:
            # Acute angle
            # t is equal to a 45 degree bend, the rest is connected by semi-circle joints
            self.t = 1.0/np.sqrt(2.0) #Corresponds to the curve when the slope is equal to 1
            dy, dx = fresnel(self.t)
            
            self.scale_factor = self.wgt.bend_radius/self.__get_radius_of_curvature()
            
            self.circle_angle = abs(self.turnby) - np.pi/2.0
            self.circle_center = (dx*self.scale_factor - self.wgt.bend_radius*np.cos(np.pi/4), 
                             dy*self.scale_factor + self.wgt.bend_radius*np.cos(np.pi/4))
                        
            self.dist_to_vertex = self.circle_center[0] + (self.circle_center[1]/np.tan((np.pi-abs(self.turnby))/2))
            
            self.output_port = (self.dist_to_vertex - self.dist_to_vertex*np.cos(np.pi - abs(self.turnby)),
                                self.sign*self.dist_to_vertex*np.sin(np.pi - abs(self.turnby)))
            
        if vertex==None:
            self.port = port
        else: #Place port according to the geometry & vertex specified
            if self.direction=="EAST": #direction of the input port (which specifies whole component orientation)
                vangle = 0.0
            elif self.direction=="NORTH":
                vangle = np.pi/2.0
            elif self.direction=="WEST":
                vangle = np.pi
            elif self.direction=="SOUTH":
                vangle = 3*np.pi/2.0
            else:
                vangle = self.direction
            self.port = (vertex[0]-self.dist_to_vertex*np.cos(vangle), vertex[1]-self.dist_to_vertex*np.sin(vangle))
            
        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()
        
    def __get_radius_of_curvature(self):
        """ Returns the *normalized* radius of curvature for the Euler curve
        """
        t = self.t
        xp = np.cos((np.pi*t**2)/2.0) # First derivative of x(t) (FresnelC)
        yp = np.sin((np.pi*t**2)/2.0) # First derivative of y(t) (FresnelS)
        xpp = -np.pi*t*np.sin((np.pi*t**2)/2.0) # Second derivative of x(t)
        ypp = np.pi*t*np.cos((np.pi*t**2)/2.0) # Second derivative of y(t)
        return abs(((xp**2 + yp**2)**(3/2)) / (xp*ypp - yp*xpp)) # Radius of curvature: https://en.wikipedia.org/wiki/Radius_of_curvature
        
    def get_bend_length(self):
        """ Returns the length of the Euler S-Bend
        """
        # The length of a parametric curve x(t) y(t) is Integral[ sqrt( (dx/dt)^2 + (dy/dt)^2 ), {t,0,t0}], which for a Fresnel curve, simplifies to just t0
        if abs(self.turnby) <= np.pi/2.0:
            return 2*self.t*self.scale_factor
        else:
            return 2*self.t*self.scale_factor + (2*np.pi*self.wgt.bend_radius)*(self.circle_angle/(2*np.pi))
        
    def __euler_function(self, t):
        # input (t) goes from 0->1
        # Returns an (x,y) tuple
        if t>1.0 or t<0.0:
            raise ValueError("Warning! A value was given to __euler_function not between 0 and 1")
            
        end_t = self.t #(end-point)
        
        if abs(self.turnby) <= np.pi/2.0:
            # Obtuse bend
            if t<0.5:
                y,x = fresnel(2*t*end_t)
                return x*self.scale_factor, self.sign*y*self.scale_factor
            else:
                y,x = fresnel(2*(1-t)*end_t)
                x,y = x*np.cos(-self.sign*self.turnby) - y*np.sin(-self.sign*self.turnby), x*np.sin(-self.sign*self.turnby) + y*np.cos(-self.sign*self.turnby)
                return self.output_port[0]-x*self.scale_factor, self.output_port[1] + self.sign*y*self.scale_factor
            
        else:
            # Acute bend
            if t<0.3:
                # First section of Euler bend
                y,x = fresnel((t/0.3)*end_t)
                return x*self.scale_factor, self.sign*y*self.scale_factor
            elif t<0.7:
                t0 = (t-0.3)/0.4
                return (self.circle_center[0] + self.wgt.bend_radius*np.cos((-self.sign*np.pi/4) + self.sign*self.circle_angle*t0),
                        self.sign*self.circle_center[1] + self.wgt.bend_radius*np.sin((-self.sign*np.pi/4) + self.sign*self.circle_angle*t0))
            else:
                y,x = fresnel(((1-t)/0.3)*end_t)
                x,y = x*np.cos(-self.sign*self.turnby) - y*np.sin(-self.sign*self.turnby), x*np.sin(-self.sign*self.turnby) + y*np.cos(-self.sign*self.turnby)
                return self.output_port[0]-x*self.scale_factor, self.output_port[1] + self.sign*y*self.scale_factor
        
    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
    
        # Uncomment below to plot the function (useful for debugging)
#        import matplotlib.pyplot as plt
#        tvals = np.linspace(0,1,5000)
#        xy = [self.__euler_function(tv) for tv in tvals]
#        plt.scatter(*zip(*xy))
#        plt.show()

        if self.wgt.wg_type=="strip":
            wg = gdspy.Path(self.start_width, (0,0))
        elif self.wgt.wg_type=="slot":
            wg = gdspy.Path(self.wgt.rail, (0,0), number_of_paths=2, distance=self.wgt.rail_dist)
            
        wg.parametric(self.__euler_function, final_width = self.end_width, tolerance=self.wgt.grid/2.0, max_points=199, **self.wg_spec)
        self.add(wg)
        
        # Add cladding
        for i in range(len(self.wgt.waveguide_stack)-1):
            cur_width = self.wgt.waveguide_stack[i+1][0]
            cur_spec = {'layer': self.wgt.waveguide_stack[i+1][1][0], 'datatype': self.wgt.waveguide_stack[i+1][1][1]}
        
            clad = gdspy.Path(cur_width, (0,0))
            clad.parametric(self.__euler_function, tolerance=self.wgt.grid/2.0, max_points=199, **cur_spec)
            self.add(clad)


    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':self.input_port, 'direction':'WEST'}
        self.portlist["output"] = {'port':self.output_port, 'direction':self.output_direction}

class EulerSBend(tk.Component):
    """ Euler shaped S-Bend Cell class.  Creates an S-shaped Euler waveguide bend that can be used in waveguide routing (in place of the sinusoidal S-Bend).  The number of points is computed based on the waveguide template grid resolution to automatically minimize grid errors.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object.  Bend radius is extracted from this object.
           * **height** (float): Height of the Euler S-Bend
           * **length** (float): Length of the Euler S-Bend

        Keyword Args:
           * **start_width** (float): If a value is provided, overrides the initial waveguide width (otherwise the width is taken from the WaveguideTemplate object).  Currently only works for strip waveguides.
           * **end_width** (float): If a value is provided, overrides the final waveguide width (otherwise the width is taken from the WaveguideTemplate object).  Currently only works for strip waveguides.
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
    def __init__(self, wgt, length, height, start_width=None, end_width=None, port=(0,0), direction='EAST'):
        tk.Component.__init__(self, "EulerSBend", locals())

        #Protected variables
        self.port = port
        self.portlist = {}
        self.direction = direction
        #End protected variables
        
        if start_width != None:
            self.start_width = start_width
        else:
            self.start_width = wgt.wg_width
        if end_width != None:
            self.end_width = end_width
        else:
            self.end_width = wgt.wg_width
        
        if length<0:
            raise ValueError("Warning! The length argument must be positive")
        if length<abs(height):
            raise ValueError("Warning! The length of the S-bend must be greater than the height.")
        
        self.wgt = wgt
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype}
        
        self.input_port = (0,0)
        self.input_direction = 'WEST'
        self.output_port = (length, height)
        self.output_direction = 'EAST'
        self.sign = np.sign(height)
        
        self.ls = (height**2 + length**2)/(4*length)# Length between the origin and the vertex (horizontally)
        
        if abs(height)==length: #Edge case to avoid divergent tangent values
            self.turnby = np.pi/2.0
        else:
            self.turnby = np.arctan(abs(height/2)/(length/2.0 - self.ls))
        
        """ Compute Euler parameters, based on an obtuse angle Euler bend """
        self.t = np.sqrt( (2/np.pi) * abs(self.turnby/2.0) )
        dy, dx = fresnel(self.t)

        output_x_norm = dx + dx*np.cos(abs(self.turnby)) - (-dy)*np.sin(abs(self.turnby))
        output_y_norm = dy + dx*np.sin(abs(self.turnby)) + (-dy)*np.cos(abs(self.turnby))
        
        self.scale_factor = abs(height/2.0)/(output_y_norm)
        
        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()
        
    def get_radius_of_curvature(self):
        """ Returns the minimum radius of curvature used to construct the Euler S-Bend
        """
        t = self.t
        # Returns the radius of curvature for a normalized Euler curve at a position t
        xp = np.cos((np.pi*t**2)/2.0) # First derivative of x(t) (FresnelC)
        yp = np.sin((np.pi*t**2)/2.0) # First derivative of y(t) (FresnelS)
        xpp = -np.pi*t*np.sin((np.pi*t**2)/2.0) # Second derivative of x(t)
        ypp = np.pi*t*np.cos((np.pi*t**2)/2.0) # Second derivative of y(t)
        return self.scale_factor * abs(((xp**2 + yp**2)**(3/2)) / (xp*ypp - yp*xpp)) # Radius of curvature: https://en.wikipedia.org/wiki/Radius_of_curvature
        
    def get_bend_length(self):
        """ Returns the length of the Euler S-Bend
        """
        # The length of a parametric curve x(t) y(t) is Integral[ sqrt( (dx/dt)^2 + (dy/dt)^2 ), {t,0,t0}], which for a Fresnel curve, simplifies to just t0
        return 4*self.t*self.scale_factor
        
    def __euler_s_function(self, t):
        # input (t) goes from 0->1
        # Returns an (x,y) tuple
        if t>1.0 or t<0.0:
            raise ValueError("Warning! A value was given to __euler_function not between 0 and 1")
            
        end_t = self.t #(end-point)
        
        if t<0.25:
            y,x = fresnel(4*t*end_t)
            return x*self.scale_factor, self.sign*y*self.scale_factor
        elif t<0.5:
            y,x = fresnel(4*(0.5-t)*end_t)
            x,y = x*np.cos(-self.turnby) - y*np.sin(-self.turnby), x*np.sin(-self.turnby) + y*np.cos(-self.turnby)
            return self.output_port[0]/2-x*self.scale_factor, self.output_port[1]/2 + self.sign*y*self.scale_factor
        elif t<0.75:
            y,x = fresnel(4*(t-0.5)*end_t)
            x,y = x*np.cos(-self.turnby) - y*np.sin(-self.turnby), x*np.sin(-self.turnby) + y*np.cos(-self.turnby)
            return self.output_port[0]/2+x*self.scale_factor, self.output_port[1]/2 - self.sign*y*self.scale_factor
        else:
            y,x = fresnel(4*(t-1)*end_t)
            return self.output_port[0]+x*self.scale_factor, self.output_port[1]+self.sign*y*self.scale_factor
        
    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        
        # Uncomment below to plot the function (useful for debugging)
#        import matplotlib.pyplot as plt
#        tvals = np.linspace(0,1,5000)
#        xy = [self.__euler_s_function(tv) for tv in tvals]
#        plt.scatter(*zip(*xy))
#        plt.show()

        if self.wgt.wg_type=="strip":
            wg = gdspy.Path(self.start_width, (0,0))
        elif self.wgt.wg_type=="slot":
            wg = gdspy.Path(self.wgt.rail, (0,0), number_of_paths=2, distance=self.wgt.rail_dist)
            
        wg.parametric(self.__euler_s_function, final_width=self.end_width, tolerance=self.wgt.grid/2.0, max_points=199, **self.wg_spec)
        self.add(wg)
        
        # Add cladding
        for i in range(len(self.wgt.waveguide_stack)-1):
            cur_width = self.wgt.waveguide_stack[i+1][0]
            cur_spec = {'layer': self.wgt.waveguide_stack[i+1][1][0], 'datatype': self.wgt.waveguide_stack[i+1][1][1]}
        
            clad = gdspy.Path(cur_width, (0,0))
            clad.parametric(self.__euler_s_function, tolerance=self.wgt.grid/2.0, max_points=199, **cur_spec)
            self.add(clad)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':self.input_port, 'direction':'WEST'}
        self.portlist["output"] = {'port':self.output_port, 'direction':'EAST'}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=25, resist='+')

    wg1=Waveguide([(0,0), (25,0)], wgt)
    tk.add(top, wg1)
#
#    eb1 = EBend(wgt, turnby=np.pi/4.0, **wg1.portlist["output"])
#    tk.add(top, eb1)
#    
#    x,y = eb1.portlist["output"]["port"]
#    wg2 = Waveguide([(x,y), (x+25/np.sqrt(2), y+25/np.sqrt(2))], wgt)
#    tk.add(top, wg2)

    esb = EulerSBend(wgt, 200.0, 100.0, **wg1.portlist["output"])
    tk.add(top, esb)
    
    x,y = esb.portlist["output"]["port"]
    wg2 = Waveguide([(x,y), (x+25, y)], wgt)
    tk.add(top, wg2)

    gdspy.LayoutViewer(cells=top, depth=3)
#    gdspy.write_gds('esbend.gds', unit=1.0e-6, precision=1.0e-9)
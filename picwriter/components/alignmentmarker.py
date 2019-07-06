# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk

class AlignmentCross(tk.Component):
    """ Cross Cell class, used for alignment

        Args:
           * **cross_length** (float):  Length of each arm of the cross.
           * **cross_width** (float): Width of the cross arm
           * **center** (tuple): Coordinate (x1, y1) of the center of the cross

        Keyword Args:
           * **small_cross_width** (float): If given, sets the width of the small cross in the center of the big cross.  Defaults to 1/4 the value of cross_width
           * **layer** (int): Layer to place the marker on.  Defaults to 1
           * **datatype** (int): Datatype to place the marker on.  Defaults to 0

    """
    def __init__(self, cross_length, cross_width, small_cross_width=None, center=(0,0), layer=1, datatype=0):
        tk.Component.__init__(self, "AlignmentCross")

        self.cross_length = cross_length
        self.cross_width = cross_width
        self.small_cross_width = cross_width/4.0 if small_cross_width==None else small_cross_width
        self.layer=layer
        self.datatype=datatype
        
        self.port = center
        self.direction = 'EAST'

        self.portlist = {}
        self.__build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()
        
        """ The _hash_cell_ function makes sure that duplicate cells are not created.
        Pass to it all the unique properties of this cell, which are used to check for duplicates.
        Do *not* include properties like port, direction.  These are specific to Cell References only.
        """
        self._hash_cell_(cross_length, cross_width, small_cross_width, layer, datatype)

    def __build_cell(self):
        # Sequentially build all the geometric shapes, then add it to the Cell
        x0,y0 = (0,0)

        #Add big cross arms
        self.add(gdspy.Rectangle((x0-self.cross_length, y0-self.cross_width/2.0), (x0-self.cross_width/2.0, y0+self.cross_width/2.0), layer=self.layer, datatype=self.datatype))
        self.add(gdspy.Rectangle((x0+self.cross_length, y0-self.cross_width/2.0), (x0+self.cross_width/2.0, y0+self.cross_width/2.0), layer=self.layer, datatype=self.datatype))
        self.add(gdspy.Rectangle((x0-self.cross_width/2.0, y0-self.cross_length), (x0+self.cross_width/2.0, y0-self.cross_width/2.0), layer=self.layer, datatype=self.datatype))
        self.add(gdspy.Rectangle((x0-self.cross_width/2.0, y0+self.cross_length), (x0+self.cross_width/2.0, y0+self.cross_width/2.0), layer=self.layer, datatype=self.datatype))

        #Add little cross arms
        self.add(gdspy.Rectangle((x0-self.cross_width/2.0, y0-self.small_cross_width/2.0), (x0+self.cross_width/2.0, y0+self.small_cross_width/2.0), layer=self.layer, datatype=self.datatype))
        self.add(gdspy.Rectangle((x0-self.small_cross_width/2.0, y0-self.cross_width/2.0), (x0+self.small_cross_width/2.0, y0+self.cross_width/2.0), layer=self.layer, datatype=self.datatype))

    def __build_ports(self):
        self.portlist["center"] = {'port':(0,0), 'direction':'WEST'}
        
class AlignmentTarget(tk.Component):
    """ Standard Target Cell class, used for alignment.  Set of concentric circles

        Args:
           * **diameter** (float):  Total diameter of the target marker
           * **ring_width** (float): Width of each ring

        Keyword Args:
           * **num_rings** (float): Number of concentric rings in the target.  Defaults to 10
           * **center** (tuple): Coordinate (x1, y1) of the center of the cross.  Defaults to (0,0)
           * **layer** (int): Layer to place the marker on.  Defaults to 1
           * **datatype** (int): Datatype to place the marker on.  Defaults to 0

    """
    def __init__(self, diameter, ring_width, num_rings=10, center=(0,0), layer=1, datatype=0):
        tk.Component.__init__(self, "AlignmentTarget", locals())

        self.diameter = diameter
        self.ring_width = ring_width
        self.num_rings = num_rings
        self.layer=layer
        self.datatype=datatype
        
        self.port = center
        self.direction = 'EAST'
        self.portlist = {}

        self.build_cell()
        self.__build_ports()
        
        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def build_cell(self):
        # Sequentially build all the geometric shapes, then add it to the Cell
        x0,y0 = (0,0)
        spacing = self.diameter/(4.0*self.num_rings)
        for i in range(self.num_rings):
            self.add(gdspy.Round((x0,y0), 2*(i+1)*spacing, 2*(i+1)*spacing-self.ring_width, layer=self.layer, datatype=self.datatype, number_of_points=0.1))

    def __build_ports(self):
        self.portlist["center"] = {'port':(0,0), 'direction':'WEST'}

if __name__ == "__main__":
    from . import *
    top = gdspy.Cell("top")
#    mark1 = AlignmentCross(500, 1, center=(0,0))
#    mark2 = AlignmentCross(500, 1, center=(100,1000))
    mark1 = AlignmentTarget(200, 3, num_rings=10)
    mark2 = AlignmentTarget(200, 3, num_rings=11, center=(200,300))
    tk.add(top, mark1)
    tk.add(top, mark2)

    gdspy.LayoutViewer()
#    gdspy.write_gds('target.gds', unit=1.0e-6, precision=1.0e-9)

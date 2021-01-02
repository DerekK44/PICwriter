# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk

class Via(tk.Component):
    """ Inter-metal Via Cell class. Creates a square via with top and bottom contacts.

        Args:
            * **mt_bot** (MetalTemplate): The metal template of the lower metal layer. Overrides bot_layer. Defaults to None. Does not create cladding geometry.
            * **mt_top** (MetalTemplate): The metal template of the upper metal layer. Overrides top_layer. Defaults to None. Does not create cladding geometry.
            * **bot_layer** (int): (if mt_bot is not used) Layer used for the bottom metal. No clad is included and the datatype defaults to 0.
            * **top_layer** (int): (if mt_top is not used) Layer used for the top metal. No clad is included and the datatype defaults to 0.
            * **via_layer** (int): Layer used to define the via etch.
            * **size** (float): Size of the via (edge length).

        Keyword Args:
            * **top_bias** (float): Amount to bias the top contact pad, around the via dimension. Defaults to 1 micron. If the top metal trace width is wider than size+2*top_bias, top_bias is increased to match the top connection size with the top trace size.
            * **bot_bias** (float): Amount to bias the bottom contact pad, around the via dimension. Defaults to 1 micron. If the bottom metal trace width is wider than size+2*bot_bias, bot_bias is increased to match the bottom connection size with the bottom trace size.
            * **port**: The center of the via structure.
        Members:
           * **portlist** (dict): Dictionary with the relevant port information. Due to the 90 degree rotation symmetry, "direction" has no meaning for this class.

        Portlist format:
           * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}


       To-do:
       * Add options for having grid arrays of vias
    """
    def __init__(self,
                mt_bot=None,
                mt_top=None,
                via_layer=12,
                bot_layer=11,
                top_layer=13,
                size=5,
                top_bias=1,
                bot_bias=1,
                port=(0,0),
                direction='EAST'):
        tk.Component.__init__(self, "Via", locals())

        self.portlist = {}

        self.port = port
        self.direction = direction

        self.mt_bot=mt_bot
        self.mt_top=mt_top
        self.via_layer=via_layer
        self.bot_layer=bot_layer
        self.top_layer=top_layer
        self.size=size
        self.top_bias=top_bias
        self.bot_bias=bot_bias

        self.__build_cell()
        self.__build_ports()
        self._auto_transform_()


    def __build_cell(self):

        # Build simple shapes using specified parameters or the metal template settings.
        if self.mt_bot is None:
            bot_layer = self.bot_layer
            bot_dtype = 0
            bot_bias = self.bot_bias
        else:
            bot_layer = self.mt_bot.metal_layer
            bot_dtype = self.mt_bot.metal_datatype
            bot_bias = np.max([self.bot_bias, (self.mt_bot.width - self.size)/2.0])

        if self.mt_top is None:
            top_layer = self.top_layer
            top_dtype = 0
            top_bias = self.top_bias
        else:
            top_layer = self.mt_top.metal_layer
            top_dtype = self.mt_top.metal_datatype
            top_bias = np.max([self.top_bias, (self.mt_top.width - self.size)/2.0])

        top_edge = self.size + 2*top_bias
        bot_edge = self.size + 2*bot_bias

        bot_pad = gdspy.Rectangle( (-bot_edge/2,-bot_edge/2), (bot_edge/2,bot_edge/2),
                        layer=bot_layer, datatype=bot_dtype )
        top_pad = gdspy.Rectangle( (-top_edge/2,-top_edge/2), (top_edge/2,top_edge/2),
                        layer=top_layer, datatype=top_dtype)
        via = gdspy.Rectangle( (-self.size/2,-self.size/2), (self.size/2,self.size/2),
                        layer=self.via_layer, datatype=0)


        components =[bot_pad, top_pad, via]
        """ Add all the components """
        for c in components:
            self.add( c )


    def __build_ports(self):
        self.portlist["center"] = {'port':(0,0),
                                    'direction':self.direction}

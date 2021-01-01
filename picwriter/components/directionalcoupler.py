# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk
from picwriter.components.waveguide import Waveguide


class DirectionalCoupler(tk.Component):
    """Directional Coupler Cell class.

    Args:
       * **wgt** (WaveguideTemplate):  WaveguideTemplate object
       * **length** (float): Length of the coupling region.
       * **gap** (float): Distance between the two waveguides.

    Keyword Args:
       * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6.
       * **parity** (integer -1 or 1): If -1, mirror-flips the structure so that the input port is actually the *bottom* port.  Default = 1.
       * **port** (tuple): Cartesian coordinate of the input port (AT TOP if parity=1, AT BOTTOM if parity=-1).  Defaults to (0,0).
       * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to 'EAST'.

    Members:
       * **portlist** (dict): Dictionary with the relevant port information

    Portlist format:
       * portlist['input_top'] = {'port': (x1,y1), 'direction': 'dir1'}
       * portlist['input_bot'] = {'port': (x2,y2), 'direction': 'dir1'}
       * portlist['output_top'] = {'port': (x3, y3), 'direction': 'dir3'}
       * portlist['output_bot'] = {'port': (x4, y4), 'direction': 'dir4'}

    Where in the above (x1,y1) (or (x2,y2) if parity=-1) is the same as the input 'port', (x3, y3), and (x4, y4) are the two output port locations.  Directions 'dir1', 'dir2', etc. are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
    'Direction' points *towards* the waveguide that will connect to it.

    """

    def __init__(
        self,
        wgt,
        length,
        gap,
        angle=np.pi / 6.0,
        parity=1,
        port=(0, 0),
        direction="EAST",
    ):
        tk.Component.__init__(self, "DirectionalCoupler", locals())

        self.portlist = {}

        self.port = port
        self.direction = direction

        if angle > np.pi / 2.0 or angle < 0:
            raise ValueError(
                "Warning! Improper angle specified ("
                + str(angle)
                + "). Must be between 0 and pi/2.0."
            )
        self.angle = angle
        if parity != 1 and parity != -1:
            raise ValueError(
                "Warning! Parity input *must* be 1 or -1. Received parity="
                + str(parity)
                + " instead."
            )
        self.parity = parity
        self.length = length
        self.gap = gap
        self.wgt = wgt
        self.wg_spec = {"layer": wgt.wg_layer, "datatype": wgt.wg_datatype}
        self.clad_spec = {"layer": wgt.clad_layer, "datatype": wgt.clad_datatype}

        self.__build_cell()
        self.__build_ports()

        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell

        x0, y0 = 0, 0  # shift to port location after rotation later

        # X-distance of horizontal waveguide
        dlx = abs(self.wgt.bend_radius * np.tan((self.angle) / 2.0))
        padding = 0.01  # Add extra 10nm to allow room for curves
        angle_x_dist = 2.0 * (dlx + padding) * np.cos(self.angle)
        angle_y_dist = 2.0 * (dlx + padding) * np.sin(self.angle) * self.parity
        tracelist_top = [
            (x0, y0),
            (x0 + dlx + padding, y0),
            (x0 + dlx + padding + angle_x_dist, y0 - angle_y_dist),
            (x0 + 3 * dlx + padding + angle_x_dist + self.length, y0 - angle_y_dist),
            (x0 + 3 * dlx + padding + 2 * angle_x_dist + self.length, y0),
            (x0 + 4 * dlx + 2 * padding + 2 * angle_x_dist + self.length, y0),
        ]
        wg_top = Waveguide(tracelist_top, self.wgt)

        y_bot_start = (
            y0 - (2 * abs(angle_y_dist) + self.gap + self.wgt.wg_width) * self.parity
        )
        tracelist_bot = [
            (x0, y_bot_start),
            (x0 + dlx + padding, y_bot_start),
            (x0 + dlx + padding + angle_x_dist, y_bot_start + angle_y_dist),
            (
                x0 + 3 * dlx + padding + angle_x_dist + self.length,
                y_bot_start + angle_y_dist,
            ),
            (x0 + 3 * dlx + padding + 2 * angle_x_dist + self.length, y_bot_start),
            (x0 + 4 * dlx + 2 * padding + 2 * angle_x_dist + self.length, y_bot_start),
        ]
        wg_bot = Waveguide(tracelist_bot, self.wgt)

        distx = 4 * dlx + 2 * angle_x_dist + self.length
        disty = (2 * abs(angle_y_dist) + self.gap + self.wgt.wg_width) * self.parity

        self.add(wg_top)
        self.add(wg_bot)
        self.portlist_input = (0, 0)
        self.portlist_output_straight = (distx, 0.0)
        self.portlist_output_cross = (distx, -disty)
        self.portlist_input_cross = (0.0, -disty)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        if self.parity == 1:
            self.portlist["input_top"] = {
                "port": self.portlist_input,
                "direction": "WEST",
            }
            self.portlist["input_bot"] = {
                "port": self.portlist_input_cross,
                "direction": "WEST",
            }
            self.portlist["output_top"] = {
                "port": self.portlist_output_straight,
                "direction": "EAST",
            }
            self.portlist["output_bot"] = {
                "port": self.portlist_output_cross,
                "direction": "EAST",
            }
        elif self.parity == -1:
            self.portlist["input_top"] = {
                "port": self.portlist_input_cross,
                "direction": "WEST",
            }
            self.portlist["input_bot"] = {
                "port": self.portlist_input,
                "direction": "WEST",
            }
            self.portlist["output_top"] = {
                "port": self.portlist_output_cross,
                "direction": "EAST",
            }
            self.portlist["output_bot"] = {
                "port": self.portlist_output_straight,
                "direction": "EAST",
            }


if __name__ == "__main__":
    from . import *
    from picwriter.components.waveguide import WaveguideTemplate

    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=100, resist="+")

    wg1 = Waveguide([(0, 0), (100, 0)], wgt)
    tk.add(top, wg1)

    #    dc = DirectionalCoupler(wgt, 20.0, 0.5, angle=np.pi/12.0, parity=1, **wg1.portlist["output"])
    #    tk.add(top, dc)

    dc1 = DirectionalCoupler(
        wgt, 10.0, 0.5, angle=np.pi / 6.0, parity=1, **wg1.portlist["output"]
    )
    dc2 = DirectionalCoupler(
        wgt, 10.0, 0.5, angle=np.pi / 6.0, parity=-1, **dc1.portlist["output_top"]
    )
    dc3 = DirectionalCoupler(
        wgt, 10.0, 0.5, angle=np.pi / 6.0, parity=1, **dc1.portlist["output_bot"]
    )
    dc4 = DirectionalCoupler(
        wgt, 10.0, 0.5, angle=np.pi / 6.0, parity=1, **dc2.portlist["output_bot"]
    )
    dc5 = DirectionalCoupler(
        wgt, 10.0, 0.5, angle=np.pi / 6.0, parity=-1, **dc2.portlist["output_top"]
    )
    dc6 = DirectionalCoupler(
        wgt, 10.0, 0.5, angle=np.pi / 6.0, parity=1, **dc3.portlist["output_bot"]
    )
    tk.add(top, dc1)
    tk.add(top, dc2)
    tk.add(top, dc3)
    tk.add(top, dc4)
    tk.add(top, dc5)
    tk.add(top, dc6)

    print(top.area())

    gdspy.LayoutViewer()
#    gdspy.write_gds('dc2.gds', unit=1.0e-6, precision=1.0e-9)

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import scipy.interpolate
import gdspy
import picwriter.toolkit as tk
from picwriter.components.ebend import EulerSBend
from picwriter.components.taper import Taper


class SplineYSplitter(tk.Component):
    """1x2 Spline based Y Splitter Cell class.
    Based on Zhang et al. (2013) A compact and low loss Y-junction for submicron silicon waveguide https://doi.org/10.1364/OE.21.001310

    Args:
       * **wgt** (WaveguideTemplate):  WaveguideTemplate object
       * **length** (float): Length of the splitter region (along direction of propagation)
       * **widths** (array of floats): Widths of the Spline Curve Splitter region (perpendicular to direction of propagation).  Width values are evenly spaced along the length of the splitter.

    Keyword Args:
       * **wg_sep** (float): Separation between waveguides on the 2-port side (defaults to be flush with the last width in the splitter region). Defaults to None.
       * **taper_width** (float): Ending width of the taper region (default = wg_width from wg_template).  Defaults to None (waveguide width).
       * **taper_length** (float): Length of the input taper leading up to the Y-splitter (single-port side).  Defaults to None (no input taper, port right against the splitter region).
       * **output_length** (float): Length (along x-direction) of the output bends, made with Euler S-Bends.  Defaults to None (no output bend, ports right up againt the splitter region).
       * **output_wg_sep** (float): Distance (along y-direction) between the two output bends, made with Euler S-Bends.  Defaults to None (no output bend, ports right up againt the splitter region).
       * **output_width** (float): Starting width of the output waveguide.  Defaults to None (no change from regular wg_width).
       * **port** (tuple): Cartesian coordinate of the input port.  Defaults to (0,0).
       * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)

    Members:
       * **portlist** (dict): Dictionary with the relevant port information

    Portlist format:
       * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
       * portlist['output_top'] = {'port': (x2, y2), 'direction': 'dir2'}
       * portlist['output_bot'] = {'port': (x3, y3), 'direction': 'dir3'}

    Where in the above (x1,y1) is the input port, (x2, y2) is the top output port, (x3, y3) is the bottom output port, and 'dir1', 'dir2', 'dir3' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
    'Direction' points *towards* the waveguide that will connect to it.

    """

    def __init__(
        self,
        wgt,
        length,
        widths,
        wg_sep=None,
        taper_width=None,
        taper_length=None,
        output_length=None,
        output_wg_sep=None,
        output_width=None,
        port=(0, 0),
        direction="EAST",
    ):
        tk.Component.__init__(self, "YSpline1x2", locals())

        self.port = port
        self.direction = direction
        self.portlist = {}

        self.wgt = wgt
        self.length = length
        self.widths = widths

        self.totlength = length

        if (output_length != None) and (output_wg_sep != None):
            self.output_length = output_length
            self.output_wg_sep = output_wg_sep
            self.output_width = wgt.wg_width if output_width == None else output_width
            self.draw_outputs = True
            self.totlength += self.output_length
        elif (output_length == None) and (output_wg_sep == None):
            self.draw_outputs = False
            self.output_wg_sep = wg_sep
        else:
            raise ValueError(
                "Warning! One of the two output values was None, and the other was provided.  Both must be provided *OR* omitted."
            )

        if (taper_width != None) and (taper_length != None):
            self.taper_width = taper_width
            self.taper_length = taper_length
            self.draw_input = True
            self.totlength += taper_length
        elif (taper_width == None) and (taper_length == None):
            self.draw_input = False
        else:
            raise ValueError(
                "Warning! One of the two input values was None, and the other was provided.  Both must be provided *OR* omitted."
            )

        self.wg_sep = widths[-1] - self.output_width if wg_sep == None else wg_sep

        self.resist = wgt.resist
        self.wg_spec = {"layer": wgt.wg_layer, "datatype": wgt.wg_datatype}
        self.clad_spec = {"layer": wgt.clad_layer, "datatype": wgt.clad_datatype}

        self.input_port = (0, 0)
        self.output_port_top = (self.totlength, self.output_wg_sep / 2.0)
        self.output_port_bot = (self.totlength, -self.output_wg_sep / 2.0)

        self.__type_check_values()
        self.__build_cell()
        self.__build_ports()

        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def __type_check_values(self):
        # Check that the values for the Y Splitter 1x2 are all valid

        if self.wg_sep > (self.widths[-1] - self.output_width):
            raise ValueError(
                "Warning! Waveguide separation is larger than the "
                "max value (width - taper_width)"
            )
        if self.draw_input and self.wg_sep < self.taper_width:
            raise ValueError(
                "Warning! Waveguide separation is smaller than the "
                "minimum value (taper_width)"
            )
        if self.draw_outputs:
            if self.output_length < (self.output_wg_sep - self.wg_sep) / 2.0:
                raise ValueError(
                    "Warning! The output length must be greater than half the output wg separation"
                )

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # then add it to the Cell

        x, y = (0, 0)

        """ Add the input taper """
        if self.draw_input:
            tp = Taper(
                self.wgt,
                self.taper_length,
                self.taper_width,
                port=(x, y),
                direction="EAST",
            )
            tp.addto(self)
            x, y = tp.portlist["output"]["port"]

        """ Add the Coupler region """
        x_widths = np.linspace(0, self.length, len(self.widths))
        x_positions = np.linspace(0, self.length, int(self.length // 0.0025))
        spl = scipy.interpolate.CubicSpline(
            x_widths, self.widths, bc_type="clamped"
        )  # Spline mode still unclear.
        y_positions = spl(x_positions)

        coupler_pts = np.concatenate(
            (
                [x_positions, y_positions / 2],
                [x_positions[::-1], -y_positions[::-1] / 2],
            ),
            axis=1,
        ).T
        coupler_region = gdspy.Polygon(coupler_pts, **self.wg_spec)
        self.add(coupler_region)

        (x, y) = (x + self.length, y)

        clad_region = gdspy.Polygon(
            [
                (x_positions[0], y_positions[0] / 2.0 + self.wgt.clad_width),
                (x_positions[-1], y_positions[-1] / 2.0 + self.wgt.clad_width),
                (x_positions[-1], -y_positions[-1] / 2.0 - self.wgt.clad_width),
                (x_positions[0], -y_positions[0] / 2.0 - self.wgt.clad_width),
            ],
            **self.clad_spec
        )
        self.add(clad_region)

        """ Add the output tapers """
        if self.draw_outputs:
            dy = (self.output_wg_sep - self.wg_sep) / 2.0
            esb_top = EulerSBend(
                self.wgt,
                self.output_length,
                dy,
                self.output_width,
                end_width=self.wgt.wg_width,
                port=(x, y + self.wg_sep / 2.0),
            )
            esb_top.addto(self)

            esb_bot = EulerSBend(
                self.wgt,
                self.output_length,
                -dy,
                self.output_width,
                end_width=self.wgt.wg_width,
                port=(x, y - self.wg_sep / 2.0),
            )
            esb_bot.addto(self)

    def __build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}

        self.portlist["input"] = {"port": self.input_port, "direction": "WEST"}
        self.portlist["output_top"] = {
            "port": self.output_port_top,
            "direction": "EAST",
        }
        self.portlist["output_bot"] = {
            "port": self.output_port_bot,
            "direction": "EAST",
        }


if __name__ == "__main__":
    #    from . import *
    import picwriter.components as pc

    top = gdspy.Cell("top")
    wgt = pc.WaveguideTemplate(bend_radius=50, wg_width=0.5, resist="+")

    # Values from Publication
    spline_widths = [0.5, 0.5, 0.6, 0.7, 0.9, 1.26, 1.4, 1.4, 1.4, 1.4, 1.31, 1.2, 1.2]
    ysplitter = SplineYSplitter(
        wgt,
        length=2,
        widths=spline_widths,
        taper_width=None,
        taper_length=None,
        output_length=10,
        output_wg_sep=5,
        output_width=0.5,
        port=(0, 0),
        direction="EAST",
    )
    wg1 = pc.Waveguide([(-10, 0), ysplitter.portlist["input"]["port"]], wgt)
    ysplitter.addto(top)
    wg1.addto(top)
    gdspy.LayoutViewer()

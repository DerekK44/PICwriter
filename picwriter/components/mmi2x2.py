# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk


class MMI2x2(tk.Component):
    """ 2x2 multi-mode interferometer (MMI) Cell class.  Two input ports, two output ports.

        Args:
           * **wgt** (WaveguideTemplate):  WaveguideTemplate object
           * **length** (float): Length of the MMI region (along direction of propagation)
           * **width** (float): Width of the MMI region (perpendicular to direction of propagation)

        Keyword Args:
           * **angle** (float): Angle in radians (between 0 and pi/2) at which the waveguide bends towards the coupling region.  Default=pi/6. Note: it is possible to generate a MMI with straight tapered outputs (not curved) by setting angle=0 and then connecting a straight Taper object to the desired MMI ports.
           * **taper_width** (float): Maximum width of the taper region (default = wg_width from wg_template)
           * **wg_sep** (float): Separation between waveguides on the 2-port side (defaults to width/3.0)
           * **port** (tuple): Cartesian coordinate of the **top** input port
           * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)

        Members:
           * **portlist** (dict): Dictionary with the relevant port information

        Portlist format:
           * portlist['input_top'] = {'port': (x1,y1), 'direction': 'dir1'}
           * portlist['input_bot'] = {'port': (x2, y2), 'direction': 'dir2'}
           * portlist['output_top'] = {'port': (x3, y3), 'direction': 'dir3'}
           * portlist['output_bot'] = {'port': (x4, y4), 'direction': 'dir4'}

        Where in the above (x1,y1) is the input port, (x2, y2) is the top output port, (x3, y3) is the bottom output port, and 'dir1', 'dir2', 'dir3' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
        'Direction' points *towards* the waveguide that will connect to it.

    """

    def __init__(
        self,
        wgt,
        length,
        width,
        angle=np.pi / 6.0,
        taper_width=None,
        wg_sep=None,
        port=(0, 0),
        direction="EAST",
    ):
        tk.Component.__init__(self, "MMI2x2", locals())

        self.portlist = {}

        self.wgt = wgt
        self.length = length
        self.width = width
        if angle > np.pi / 2.0 or angle < 0:
            raise ValueError(
                "Warning! Improper angle specified ("
                + str(angle)
                + ").  Must be between 0 and pi/2.0."
            )
        self.angle = angle
        self.taper_width = wgt.wg_width if taper_width == None else taper_width
        self.wg_sep = width / 3.0 if wg_sep == None else wg_sep

        self.port = port
        self.direction = direction
        self.resist = wgt.resist
        self.wg_spec = {"layer": wgt.wg_layer, "datatype": wgt.wg_datatype}
        self.clad_spec = {"layer": wgt.clad_layer, "datatype": wgt.clad_datatype}

        self.type_check_values()
        self.__build_cell()
        self.__build_ports()

        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def type_check_values(self):
        # Check that the values for the MMI1x2 are all valid

        if self.wg_sep > (self.width - self.taper_width):
            raise ValueError(
                "Warning! Waveguide separation is larger than the "
                "max value (width - taper_width)"
            )
        if self.wg_sep < self.taper_width:
            raise ValueError(
                "Warning! Waveguide separation is smaller than the "
                "minimum value (taper_width)"
            )

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # then add it to the Cell

        angle_x_dist = 2 * self.wgt.bend_radius * np.sin(self.angle)
        angle_y_dist = 2 * self.wgt.bend_radius * (1 - np.cos(self.angle))

        """ Waveguide paths """
        # Top input
        path1 = gdspy.Path(self.wgt.wg_width, (0, 0))
        path1.turn(
            self.wgt.bend_radius,
            -self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            **self.wg_spec
        )
        path1.turn(
            self.wgt.bend_radius,
            self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            final_width=self.taper_width,
            **self.wg_spec
        )
        # Bottom input
        path2 = gdspy.Path(self.wgt.wg_width, (0, -self.wg_sep - 2 * angle_y_dist))
        path2.turn(
            self.wgt.bend_radius,
            self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            **self.wg_spec
        )
        path2.turn(
            self.wgt.bend_radius,
            -self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            final_width=self.taper_width,
            **self.wg_spec
        )
        # MMI body
        path3 = gdspy.Path(
            self.width, (angle_x_dist, -self.wg_sep / 2.0 - angle_y_dist)
        )
        path3.segment(self.length, direction="+x", **self.wg_spec)
        # Top output
        path4 = gdspy.Path(self.taper_width, (path1.x + self.length, path1.y))
        path4.turn(
            self.wgt.bend_radius,
            self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            final_width=self.wgt.wg_width,
            **self.wg_spec
        )
        path4.turn(
            self.wgt.bend_radius,
            -self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            **self.wg_spec
        )
        # Bottom output
        path5 = gdspy.Path(self.taper_width, (path2.x + self.length, path2.y))
        path5.turn(
            self.wgt.bend_radius,
            -self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            final_width=self.wgt.wg_width,
            **self.wg_spec
        )
        path5.turn(
            self.wgt.bend_radius,
            self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            **self.wg_spec
        )

        """ Now, generate the cladding paths """
        # Top input
        clad_path1 = gdspy.Path(self.wgt.wg_width + 2 * self.wgt.clad_width, (0, 0))
        clad_path1.turn(
            self.wgt.bend_radius,
            -self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            **self.clad_spec
        )
        clad_path1.turn(
            self.wgt.bend_radius,
            self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            final_width=self.taper_width + 2 * self.wgt.clad_width,
            **self.clad_spec
        )
        # Bottom input
        clad_path2 = gdspy.Path(
            self.wgt.wg_width + 2 * self.wgt.clad_width,
            (0, -self.wg_sep - 2 * angle_y_dist),
        )
        clad_path2.turn(
            self.wgt.bend_radius,
            self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            **self.clad_spec
        )
        clad_path2.turn(
            self.wgt.bend_radius,
            -self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            final_width=self.taper_width + 2 * self.wgt.clad_width,
            **self.clad_spec
        )
        # MMI body
        c_start_width = 2 * self.wgt.clad_width + 2 * self.taper_width + self.wg_sep
        clad_path3 = gdspy.Path(
            c_start_width,
            (angle_x_dist - self.wgt.clad_width, -self.wg_sep / 2.0 - angle_y_dist),
        )
        clad_path3.segment(
            self.wgt.clad_width,
            final_width=self.width + 2 * self.wgt.clad_width,
            direction="+x",
            **self.clad_spec
        )
        clad_path3.segment(self.length, direction="+x", **self.clad_spec)
        clad_path3.segment(
            self.wgt.clad_width,
            final_width=c_start_width,
            direction="+x",
            **self.clad_spec
        )
        # Top output
        clad_path4 = gdspy.Path(
            self.taper_width + 2 * self.wgt.clad_width,
            (clad_path1.x + self.length, clad_path1.y),
        )
        clad_path4.turn(
            self.wgt.bend_radius,
            self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            final_width=self.wgt.wg_width + 2 * self.wgt.clad_width,
            **self.clad_spec
        )
        clad_path4.turn(
            self.wgt.bend_radius,
            -self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            **self.clad_spec
        )
        # Bottom output
        clad_path5 = gdspy.Path(
            self.taper_width + 2 * self.wgt.clad_width,
            (clad_path2.x + self.length, clad_path2.y),
        )
        clad_path5.turn(
            self.wgt.bend_radius,
            -self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            final_width=self.wgt.wg_width + 2 * self.wgt.clad_width,
            **self.clad_spec
        )
        clad_path5.turn(
            self.wgt.bend_radius,
            self.angle,
            number_of_points=self.wgt.get_num_points_wg(self.angle),
            **self.clad_spec
        )

        self.input_port_top = (0.0, 0.0)
        self.input_port_bot = (0.0, -self.wg_sep - 2 * angle_y_dist)
        self.output_port_top = (2 * angle_x_dist + self.length, 0.0)
        self.output_port_bot = (
            2 * angle_x_dist + self.length,
            -self.wg_sep - 2 * angle_y_dist,
        )

        self.add(path1)
        self.add(path2)
        self.add(path3)
        self.add(path4)
        self.add(path5)
        self.add(clad_path1)
        self.add(clad_path2)
        self.add(clad_path3)
        self.add(clad_path4)
        self.add(clad_path5)

    def __build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input_top"] = {"port": self.input_port_top, "direction": "WEST"}
        self.portlist["input_bot"] = {"port": self.input_port_bot, "direction": "WEST"}
        self.portlist["output_top"] = {
            "port": self.output_port_top,
            "direction": "EAST",
        }
        self.portlist["output_bot"] = {
            "port": self.output_port_bot,
            "direction": "EAST",
        }


if __name__ == "__main__":
    from . import *

    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist="+")

    wg1 = Waveguide([(0, 0), (0, -100)], wgt)
    tk.add(top, wg1)

    mmi1 = MMI2x2(
        wgt, length=50, width=10, taper_width=2.0, wg_sep=3.0, **wg1.portlist["output"]
    )
    mmi2 = MMI2x2(
        wgt,
        length=50,
        width=10,
        taper_width=2.0,
        wg_sep=3.0,
        **mmi1.portlist["output_top"]
    )
    tk.add(top, mmi1)
    tk.add(top, mmi2)

    gdspy.LayoutViewer()
#    # gdspy.write_gds('mmi2x2.gds', unit=1.0e-6, precision=1.0e-9)

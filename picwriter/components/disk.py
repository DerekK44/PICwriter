# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk


class Disk(tk.Component):
    """Disk Resonator Cell class.

    Args:
       * **wgt** (WaveguideTemplate):  WaveguideTemplate object
       * **radius** (float): Radius of the disk resonator
       * **coupling_gap** (float): Distance between the bus waveguide and resonator

    Keyword Args:
       * **wrap_angle** (float): Angle in *radians* between 0 and pi (defaults to 0) that determines how much the bus waveguide wraps along the resonator.  0 corresponds to a straight bus waveguide, and pi corresponds to a bus waveguide wrapped around half of the resonator.
       * **parity** (1 or -1): If 1, resonator to left of bus waveguide, if -1 resonator to the right
       * **port** (tuple): Cartesian coordinate of the input port (x1, y1)
       * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)

    Members:
       * **portlist** (dict): Dictionary with the relevant port information

    Portlist format:
       * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
       * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

    Where in the above (x1,y1) is the same as the 'port' input, (x2, y2) is the end of the component, and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
    'Direction' points *towards* the waveguide that will connect to it.

    """

    def __init__(
        self,
        wgt,
        radius,
        coupling_gap,
        wrap_angle=0,
        parity=1,
        port=(0, 0),
        direction="EAST",
    ):
        tk.Component.__init__(self, "Disk", locals())

        self.portlist = {}

        self.port = port
        # self.trace=[port, tk.translate_point(port, 2*radius, direction)]
        self.direction = direction

        self.radius = radius
        self.coupling_gap = coupling_gap
        self.wrap_angle = wrap_angle
        if (wrap_angle > np.pi) or (wrap_angle < 0):
            raise ValueError(
                "Warning! Wrap_angle is nor a valid angle between 0 and pi."
            )
        self.parity = parity
        self.resist = wgt.resist
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

        if self.wrap_angle == 0:
            bus_length = 2 * self.radius
            # Add bus waveguide with cladding
            path = gdspy.Path(self.wgt.wg_width, (0, 0))
            path.segment(2 * self.radius, direction="+x", **self.wg_spec)
            clad = gdspy.Path(2 * self.wgt.clad_width + self.wgt.wg_width, (0, 0))
            clad.segment(2 * self.radius, direction="+x", **self.clad_spec)

            # Disk resonator
            if self.parity == 1:
                ring = gdspy.Round(
                    (
                        self.radius,
                        self.radius + self.wgt.wg_width / 2.0 + self.coupling_gap,
                    ),
                    self.radius,
                    number_of_points=self.wgt.get_num_points_curve(
                        2 * np.pi, self.radius
                    ),
                    **self.wg_spec
                )
                clad_ring = gdspy.Round(
                    (
                        self.radius,
                        self.radius + self.wgt.wg_width / 2.0 + self.coupling_gap,
                    ),
                    self.radius + self.wgt.clad_width,
                    number_of_points=self.wgt.get_num_points_curve(
                        2 * np.pi, self.radius + self.wgt.clad_width
                    ),
                    **self.clad_spec
                )
            elif self.parity == -1:
                ring = gdspy.Round(
                    (
                        self.radius,
                        -self.radius - self.wgt.wg_width / 2.0 - self.coupling_gap,
                    ),
                    self.radius,
                    number_of_points=self.wgt.get_num_points_curve(
                        2 * np.pi, self.radius
                    ),
                    **self.wg_spec
                )
                clad_ring = gdspy.Round(
                    (
                        self.radius,
                        -self.radius - self.wgt.wg_width / 2.0 - self.coupling_gap,
                    ),
                    self.radius + self.wgt.clad_width,
                    number_of_points=self.wgt.get_num_points_curve(
                        2 * np.pi, self.radius + self.wgt.clad_width
                    ),
                    **self.clad_spec
                )
            else:
                raise ValueError(
                    "Warning!  Parity value is not an acceptable value (must be +1 or -1)."
                )
        elif self.wrap_angle > 0:
            theta = self.wrap_angle / 2.0
            rp = self.radius + self.wgt.wg_width / 2.0 + self.coupling_gap
            dx, dy = rp * np.sin(theta), rp - rp * np.cos(theta)
            bus_length = 2 * self.radius if (4 * dx < 2 * self.radius) else 4 * dx

            # Add bus waveguide with cladding that wraps
            path = gdspy.Path(self.wgt.wg_width, (0, 0))
            clad = gdspy.Path(2 * self.wgt.clad_width + self.wgt.wg_width, (0, 0))
            if 4 * dx < bus_length:
                path.segment(
                    (bus_length - 4 * dx) / 2.0, direction="+x", **self.wg_spec
                )
                clad.segment(
                    (bus_length - 4 * dx) / 2.0, direction="+x", **self.clad_spec
                )
                xcenter = self.radius
            else:
                xcenter = 2 * dx

            if self.parity == 1:
                path.arc(
                    rp,
                    np.pi / 2.0,
                    np.pi / 2.0 - theta,
                    number_of_points=2 * self.wgt.get_num_points_curve(theta, rp),
                    **self.wg_spec
                )
                path.arc(
                    rp,
                    -np.pi / 2.0 - theta,
                    -np.pi / 2.0 + theta,
                    number_of_points=2 * self.wgt.get_num_points_curve(2 * theta, rp),
                    **self.wg_spec
                )
                path.arc(
                    rp,
                    np.pi / 2.0 + theta,
                    np.pi / 2.0,
                    number_of_points=2 * self.wgt.get_num_points_curve(theta, rp),
                    **self.wg_spec
                )
                clad.arc(
                    rp,
                    np.pi / 2.0,
                    np.pi / 2.0 - theta,
                    number_of_points=2 * self.wgt.get_num_points_curve(theta, rp),
                    **self.clad_spec
                )
                clad.arc(
                    rp,
                    -np.pi / 2.0 - theta,
                    -np.pi / 2.0 + theta,
                    number_of_points=2 * self.wgt.get_num_points_curve(2 * theta, rp),
                    **self.clad_spec
                )
                clad.arc(
                    rp,
                    np.pi / 2.0 + theta,
                    np.pi / 2.0,
                    number_of_points=2 * self.wgt.get_num_points_curve(theta, rp),
                    **self.clad_spec
                )

                # Make the disk resonator
                ring = gdspy.Round(
                    (
                        xcenter,
                        self.radius
                        + self.wgt.wg_width / 2.0
                        + self.coupling_gap
                        - 2 * dy,
                    ),
                    self.radius,
                    number_of_points=self.wgt.get_num_points_curve(
                        2 * np.pi, self.radius
                    ),
                    **self.wg_spec
                )
                clad_ring = gdspy.Round(
                    (
                        xcenter,
                        self.radius
                        + self.wgt.wg_width / 2.0
                        + self.coupling_gap
                        - 2 * dy,
                    ),
                    self.radius + self.wgt.clad_width,
                    number_of_points=self.wgt.get_num_points_curve(
                        2 * np.pi, self.radius + self.wgt.clad_width
                    ),
                    **self.clad_spec
                )

            elif self.parity == -1:
                path.arc(
                    rp,
                    -np.pi / 2.0,
                    -np.pi / 2.0 + theta,
                    number_of_points=2 * self.wgt.get_num_points_curve(theta, rp),
                    **self.wg_spec
                )
                path.arc(
                    rp,
                    np.pi / 2.0 + theta,
                    np.pi / 2.0 - theta,
                    number_of_points=2 * self.wgt.get_num_points_curve(2 * theta, rp),
                    **self.wg_spec
                )
                path.arc(
                    rp,
                    -np.pi / 2.0 - theta,
                    -np.pi / 2.0,
                    number_of_points=2 * self.wgt.get_num_points_curve(theta, rp),
                    **self.wg_spec
                )
                clad.arc(
                    rp,
                    -np.pi / 2.0,
                    -np.pi / 2.0 + theta,
                    number_of_points=2 * self.wgt.get_num_points_curve(theta, rp),
                    **self.clad_spec
                )
                clad.arc(
                    rp,
                    np.pi / 2.0 + theta,
                    np.pi / 2.0 - theta,
                    number_of_points=2 * self.wgt.get_num_points_curve(2 * theta, rp),
                    **self.clad_spec
                )
                clad.arc(
                    rp,
                    -np.pi / 2.0 - theta,
                    -np.pi / 2.0,
                    number_of_points=2 * self.wgt.get_num_points_curve(theta, rp),
                    **self.clad_spec
                )

                # Make the disk resonator
                ring = gdspy.Round(
                    (
                        xcenter,
                        -self.radius
                        - self.wgt.wg_width / 2.0
                        - self.coupling_gap
                        + 2 * dy,
                    ),
                    self.radius,
                    number_of_points=self.wgt.get_num_points_curve(
                        2 * np.pi, self.radius
                    ),
                    **self.wg_spec
                )
                clad_ring = gdspy.Round(
                    (
                        xcenter,
                        -self.radius
                        - self.wgt.wg_width / 2.0
                        - self.coupling_gap
                        + 2 * dy,
                    ),
                    self.radius + self.wgt.clad_width,
                    number_of_points=self.wgt.get_num_points_curve(
                        2 * np.pi, self.radius + self.wgt.clad_width
                    ),
                    **self.clad_spec
                )

            if 4 * dx < bus_length:
                path.segment((bus_length - 4 * dx) / 2.0, **self.wg_spec)
                clad.segment((bus_length - 4 * dx) / 2.0, **self.clad_spec)

        self.port_input = (0, 0)
        self.port_output = (bus_length, 0)

        self.add(ring)
        self.add(clad_ring)
        self.add(path)
        self.add(clad)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {"port": self.port_input, "direction": "WEST"}
        self.portlist["output"] = {"port": self.port_output, "direction": "EAST"}


if __name__ == "__main__":
    from . import *

    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, resist="+")

    wg1 = Waveguide([(0, 0), (100, 0)], wgt)
    tk.add(top, wg1)

    r1 = Disk(
        wgt, 60.0, 1.0, wrap_angle=np.pi / 2.0, parity=1, **wg1.portlist["output"]
    )

    wg2 = Waveguide(
        [
            r1.portlist["output"]["port"],
            (r1.portlist["output"]["port"][0] + 100, r1.portlist["output"]["port"][1]),
        ],
        wgt,
    )
    tk.add(top, wg2)

    r2 = Disk(wgt, 50.0, 0.8, wrap_angle=np.pi, parity=-1, **wg2.portlist["output"])

    wg3 = Waveguide(
        [
            r2.portlist["output"]["port"],
            (r2.portlist["output"]["port"][0] + 100, r2.portlist["output"]["port"][1]),
        ],
        wgt,
    )
    tk.add(top, wg3)

    r3 = Disk(wgt, 40.0, 0.6, parity=1, **wg3.portlist["output"])

    wg4 = Waveguide(
        [
            r3.portlist["output"]["port"],
            (r3.portlist["output"]["port"][0] + 100, r3.portlist["output"]["port"][1]),
        ],
        wgt,
    )
    tk.add(top, wg4)

    tk.add(top, r1)
    tk.add(top, r2)
    tk.add(top, r3)

#    gdspy.LayoutViewer()
#    gdspy.write_gds('disk.gds', unit=1.0e-6, precision=1.0e-9)

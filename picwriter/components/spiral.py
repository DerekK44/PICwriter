# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk
from picwriter.components.waveguide import Waveguide
from picwriter.components.sbend import SBend


class Spiral(tk.Component):
    """Spiral Waveguide Cell class.  The desired length of the spiral is first set, along with the spacing between input and output (the 'width' paramter).  Then, the corresponding height of the spiral is automatically set.

    Args:
       * **wgt** (WaveguideTemplate):  WaveguideTemplate object
       * **width** (float): width of the spiral (i.e. distance between input/output ports)
       * **length** (float): desired length of the waveguide

    Keyword Args:
       * **spacing** (float): distance between parallel waveguides
       * **parity** (int): If 1 spiral on right side, if -1 spiral on left side (mirror flip)
       * **port** (tuple): Cartesian coordinate of the input port
       * **direction** (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians)

    Members:
       * **portlist** (dict): Dictionary with the relevant port information

    Portlist format:
       * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
       * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

    Where in the above (x1,y1) are the first elements of the spiral trace, (x2, y2) are the last elements of the spiral trace, and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*.
    'Direction' points *towards* the waveguide that will connect to it.

    """

    def __init__(
        self, wgt, width, length, spacing=None, parity=1, port=(0, 0), direction="NORTH"
    ):
        tk.Component.__init__(self, "Spiral", locals())

        self.portlist = {}

        self.width = width
        self.length = length
        self.parity = parity
        self.port = port
        self.spacing = 3 * wgt.clad_width if spacing == None else spacing

        self.wgt = wgt
        if self.wgt.euler == True:
            self.bend_radius = wgt.effective_bend_radius
            self.corner_dl = 2 * wgt.effective_bend_radius - wgt.bend_length_90
        else:
            self.bend_radius = wgt.bend_radius
            self.corner_dl = 2 * wgt.bend_radius - (0.5 * np.pi * wgt.bend_radius)

        self.direction = direction

        if width < self.spacing + 5 * self.bend_radius:
            print("width = " + str(width))
            print("spacing = " + str(self.spacing))
            print("bend_radius = " + str(self.bend_radius))
            raise ValueError(
                "Warning!  Given the WaveguideTemplate 'bend radius' and 'spacing' specified, no spiral can be fit within the requested 'width'.  Please increase the 'width'."
            )

        self.nmax = int(
            (self.width - self.spacing - 5 * self.bend_radius) / (2 * self.spacing)
        )

        self.__build_cell()
        self.__build_ports()

        """ Translate & rotate the ports corresponding to this specific component object
        """
        self._auto_transform_()

    def __fixed_len(self, h):
        w = self.width
        s = self.spacing
        br = self.bend_radius
        wcent = (w - s - br) / 2.0
        return 2 * wcent + (h - s) + wcent + br + h + (w - br) + (h - s) + wcent

    def __spiral_len(self, h, n):
        if n == 0:
            return 0
        else:
            w = self.width
            s = self.spacing
            br = self.bend_radius
            wcent = (w - s - br) / 2.0
            return 2 * ((2 * (wcent - n * s)) + (h - s - 2 * n * s))

    def __middle_len(self, h, n):
        return (h - 2 * self.spacing) - 2 * n * self.spacing

    def get_length(self, h, n):
        # Return the length of the spiral given the height and number of wraps, "n"
        num_points = 10 + 4 * n

        length = self.__fixed_len(h)
        length += sum([self.__spiral_len(h, i + 1) for i in range(n)])
        length += self.__middle_len(h, n)
        length -= (num_points - 2) * self.corner_dl
        return length

    def __get_hmin(self, n):
        # Determine the minimum height corresponding to the spiral parameters and # of spiral turns, 'n'
        br = self.bend_radius
        s = self.spacing
        return 2 * br + 2 * s + 2 * n * s

    def get_spiral_length(self):
        # Returns the true length of the spiral, including length from the turns
        return self.actual_length

    def __get_number_of_spirals(self):
        # Find the ideal number of loops required to make the spiral such that the
        # spiral is wound as tightly as possible.  This means that the required height
        # of the spiral should be minimized appropriately.
        length_goal = self.length

        n = 0
        hmin = self.__get_hmin(n)
        length_min = self.get_length(hmin, n)
        while (length_min < length_goal) and n < self.nmax:
            n += 1
            hmin = self.__get_hmin(n)
            length_min = self.get_length(hmin, n)

        if n == 0:
            if length_min > length_goal:
                return None
            else:
                return n
        else:
            return n - 1

    def __get_spiral_height(self, n):
        # n is the number of spirals
        # Returns the appropriate height ( > hmin) such that
        num_wg_segments = 4 + 2 * n

        hmin = self.__get_hmin(n)
        delta_length = self.length - self.get_length(hmin, n)
        hnew = hmin + (delta_length / num_wg_segments)

        return hnew

    def __build_cell(self):
        # Determine the correct set of waypoints, then feed this over to a
        # Waveguide() class.
        # This is just one way of doing it... ¯\_(ツ)_/¯

        # Determine the number of spiral wraps
        skip_length_check = False
        n = self.__get_number_of_spirals()

        if n != None:
            """Determine the corresponding spiral height"""
            h = self.__get_spiral_height(n)

            w = self.width
            length = self.length
            br = self.bend_radius
            s = self.spacing

            """ Double check all parameters
            """
            if abs(length - self.get_length(h, n)) > 1e-6:
                raise ValueError(
                    "Warning! The computed length and desired length are not equal!"
                )

            """ Now that the parameters are all determined, build the corresponding
            waypoints """
            wcent = (w - s - br) / 2.0

            p = self.parity
            x0, y0 = 0, 0

            """ Start/end points corresponding to 'fixed_len' unit """
            start_points = [
                (x0, y0),
                (x0 + 2 * wcent, y0),
                (x0 + 2 * wcent, y0 - p * (h - s)),
            ]
            end_points = [
                (x0, y0 - p * s),
                (x0, y0 - p * h),
                (x0 + w - br, y0 - p * h),
                (x0 + w - br, y0),
                (x0 + w, y0),
            ]

            """ Generate the spiral going inwards """
            spiral_in_pts = []

            x_left_start, x_right_start = x0 + s, x0 + 2 * wcent - 2 * s
            y_top_start, y_bot_start = y0 - p * 2 * s, y0 - p * (h - s)

            for j in range(n):
                i = j + 1
                if i % 2 == 1:  # ODD, so add a segment on the LEFT
                    left_segment_index = (i - 1) / 2
                    spiral_in_pts.append(
                        (
                            x_left_start + 2 * s * left_segment_index,
                            y_bot_start + p * (2 * s * left_segment_index),
                        )
                    )
                    spiral_in_pts.append(
                        (
                            x_left_start + 2 * s * left_segment_index,
                            y_top_start - p * (2 * s * left_segment_index),
                        )
                    )
                    if j + 1 == n:  # This is the last one! Add the middle point now
                        spiral_in_pts.append(
                            (x0 + wcent, y_top_start - p * (2 * s * left_segment_index))
                        )
                if i % 2 == 0:  # EVEN, so add a segment on the RIGHT
                    right_segment_index = (i - 2) / 2
                    spiral_in_pts.append(
                        (
                            x_right_start - (2 * s * right_segment_index),
                            y_top_start - p * (2 * s * right_segment_index),
                        )
                    )
                    spiral_in_pts.append(
                        (
                            x_right_start - (2 * s * right_segment_index),
                            y_bot_start + p * (2 * s * right_segment_index + 2 * s),
                        )
                    )
                    if j + 1 == n:  # This is the last one! Add the middle point now
                        spiral_in_pts.append(
                            (
                                x0 + wcent,
                                y_bot_start + p * (2 * s * right_segment_index + 2 * s),
                            )
                        )

            if n == 0:
                spiral_in_pts.append((x0 + wcent, y_bot_start))

            """ Generate the spiral going outwards """
            spiral_out_pts = []

            x_left_start, x_right_start = x0 + 2 * s, x0 + 2 * wcent - s
            y_top_start, y_bot_start = y0 - p * s, y0 - p * (h - 2 * s)

            for j in range(n):
                i = j + 1
                if i % 2 == 1:  # ODD, so add a segment on the RIGHT
                    right_segment_index = (i - 1) / 2
                    spiral_out_pts.append(
                        (
                            x_right_start - 2 * s * right_segment_index,
                            y_top_start - p * 2 * s * right_segment_index,
                        )
                    )
                    spiral_out_pts.append(
                        (
                            x_right_start - 2 * s * right_segment_index,
                            y_bot_start + p * (2 * s * right_segment_index),
                        )
                    )
                    if j + 1 == n:  # This is the last one! Add the middle point now
                        spiral_out_pts.append(
                            (x0 + wcent, y_bot_start + p * 2 * s * right_segment_index)
                        )

                elif i % 2 == 0:  # EVEN, add a segment on the LEFT
                    left_segment_index = (i - 2) / 2
                    spiral_out_pts.append(
                        (
                            x_left_start + 2 * s * left_segment_index,
                            y_bot_start + p * 2 * s * left_segment_index,
                        )
                    )
                    spiral_out_pts.append(
                        (
                            x_left_start + 2 * s * left_segment_index,
                            y_top_start - p * (2 * s * left_segment_index + 2 * s),
                        )
                    )
                    if j + 1 == n:  # This is the last one! Add the middle point now
                        spiral_out_pts.append(
                            (
                                x0 + wcent,
                                y_top_start - p * (2 * s * left_segment_index + 2 * s),
                            )
                        )

            if n == 0:
                spiral_out_pts.append((x0 + wcent, y_top_start))

            spiral_out_pts.reverse()  # reverse order

            waypoints = start_points + spiral_in_pts + spiral_out_pts + end_points

        else:
            """ Make the waveguide waypoints just a U-bend, since the waveguide length is not long enough to spiral in on itself """

            length = self.length
            w = self.width
            br = self.bend_radius
            dl = self.corner_dl

            if length < w + 4 * br - 4 * dl:
                """ Route a sinusoidal s-bend waveguide with the desired length """
                # Goal:  Find the height of the s-bend

                from scipy.optimize import fsolve
                from scipy.special import ellipeinc

                # The equation below is the arc length of a sine curve, for a given height and width
                func = lambda s_height: length - ellipeinc(
                    2 * np.pi, 1 - 1 / (1 + (s_height ** 2 * np.pi ** 2 / w ** 2))
                ) / (
                    (2 * np.pi / w) / np.sqrt(1 + (s_height ** 2 * np.pi ** 2 / w ** 2))
                )

                h_guess = np.sqrt((length / 2.0) ** 2 - (w / 2) ** 2)

                h_solution = fsolve(func, h_guess)
                h = -self.parity * h_solution[0]

                sbend1 = SBend(self.wgt, w / 2.0, h, port=(0, 0), direction="EAST")
                self.add(sbend1)

                sbend2 = SBend(
                    self.wgt, w / 2.0, -h, port=(w / 2.0, h), direction="EAST"
                )
                self.add(sbend2)

                #                print("Added an SBend")
                #                print("h = "+str(h))
                #                print("w = "+str(w))
                #                print("length = "+str(length))

                self.actual_length = ellipeinc(
                    2 * np.pi, 1 - 1 / (1 + (h ** 2 * np.pi ** 2 / w ** 2))
                ) / ((2 * np.pi / w) / np.sqrt(1 + (h ** 2 * np.pi ** 2 / w ** 2)))

                skip_length_check = True

            else:
                p = self.parity
                x0, y0 = 0, 0

                extra_height = (length - (w + 4 * br - 4 * dl)) / 2.0

                max_turns = (w - 4 * br) // (
                    4 * br
                )  # one 'turn' is a turn segment added to the waveguide "U" (to get the length required without making the bend very tall)
                extra_length_per_turn = (
                    8 * br - 4 * dl - 4 * br
                )  # Extra length incurred by adding a turn (compared to a straight section)

                waypoints = [(x0, y0), (x0 + br, y0)]

                number_of_turns = (
                    extra_height // extra_length_per_turn
                )  # Max number of turns that could be formed from the extra_height

                if number_of_turns > max_turns:
                    """ Add *all* of the turns, plus some extra for the height, else add only the smaller number of turns. """
                    number_of_turns = max_turns

                dh = (
                    length
                    - (w + 4 * br - 4 * dl)
                    - number_of_turns * extra_length_per_turn
                ) / (number_of_turns * 2 + 2)

                waypoints.append((x0 + br, y0 - p * (2 * br + dh)))
                for i in range(int(number_of_turns)):
                    waypoints.append((x0 + 3 * br + i * br * 4, y0 - p * (2 * br + dh)))
                    waypoints.append((x0 + 3 * br + i * br * 4, y0))
                    waypoints.append((x0 + 5 * br + i * br * 4, y0))
                    waypoints.append((x0 + 5 * br + i * br * 4, y0 - p * (2 * br + dh)))

                waypoints.append((x0 + w - br, y0 - p * (2 * br + dh)))
                waypoints.append((x0 + w - br, y0))
                waypoints.append((x0 + w, y0))

        """ Independently verify that the length of the spiral structure generated is correct
        """
        if not skip_length_check:
            l = 0
            for i in range(len(waypoints) - 1):
                dx, dy = (
                    waypoints[i + 1][0] - waypoints[i][0],
                    waypoints[i + 1][1] - waypoints[i][1],
                )
                l += np.sqrt(dx ** 2 + dy ** 2)
            num_corners = len(waypoints) - 2
            l -= num_corners * self.corner_dl

            self.actual_length = l

            if abs(l - self.length) > 1e-6:
                print("Actual computed length = " + str(l))
                print("Expected length = " + str(self.length))
                raise ValueError(
                    "Warning! Spiral generated is significantly different from what is expected."
                )

            """ Generate the waveguide """
            wg = Waveguide(waypoints, self.wgt)

            self.add(wg)

        self.portlist_input = (0, 0)
        self.portlist_output = (self.width, 0)

    def __build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}

        self.portlist["input"] = {"port": self.portlist_input, "direction": "WEST"}
        self.portlist["output"] = {"port": self.portlist_output, "direction": "EAST"}


if __name__ == "__main__":
    from picwriter.components.waveguide import WaveguideTemplate

    gdspy.current_library = gdspy.GdsLibrary()
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(
        bend_radius=50, wg_width=1.0, clad_width=10.0, euler_bend=True
    )

    sp1 = Spiral(
        wgt,
        width=2700.0,
        length=2900.0,
        spacing=20.0,
        parity=1,
        port=(0, 0),
        direction="EAST",
    )
    tk.add(top, sp1)

    print("length is " + str(sp1.get_spiral_length()))
    print("portlist = " + str(sp1.portlist))

    gdspy.LayoutViewer(cells="top")
    # gdspy.write_gds('spiral.gds', unit=1.0e-6, precision=1.0e-9)

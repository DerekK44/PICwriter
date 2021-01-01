# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import picwriter.toolkit as tk
from picwriter.components.ebend import EBend


class WaveguideTemplate:
    """Template for waveguides that contains standard information about the geometry and fabrication.  Supported waveguide types are **strip** (also known as 'channel' waveguides), **slot**, and **SWG** ('sub-wavelength grating', or 1D photonic crystal waveguides).

    Keyword Args:
       * **wg_type** (string): Type of waveguide used.  Options are 'strip', 'slot', and 'swg'.  Defaults to 'strip'.
       * **bend_radius** (float): Radius of curvature for waveguide bends (circular).  Defaults to 50.
       * **waveguide_stack** (list): List of layers and path widths to be drawn when waveguides are routed & placed.  Format is '[[width1, (layer1, datatype1)], [width2, (layer2, datatype2)], ...]'.  The first element defines the main waveguide width & layer for slot and subwavelength gratings.  If using waveguide_stack, the following keyword arguments are ignored: wg_width, clad_width, wg_layer, wg_datatype, clad_layer, clad_datatype.  Defaults to [[2.0, (1,0)], [10.0, (2,0)]].
       * **wg_width** (float): Width of the waveguide as shown on the mask.  Defaults to 2.
       * **euler_bend** (boolean): If `True`, uses Euler bends to route waveguides.  Defaults to `False`.  Currently only works with slot and strip waveguides.  The given `bend_radius` value determines the **smallest** bend radius along the entire Euler curve.
       * **slot** (float): Size of the waveguide slot region.  This is only used if `wg_type`=`'slot'`.  Defaults to 0.1.
       * **period** (float): Period of the SWG. This is only used if `wg_type`=`'swg'`. Defaults to 0.1.
       * **duty_cycle** (float): Duty cycle of the SWG. This is only used if `wg_type`=`'swg'`. Defaults to 0.5.
       * **clad_width** (float): Width of the cladding (region next to waveguide, mainly used for positive-type photoresists + etching, or negative-type and liftoff).  Defaults to 10.
       * **grid** (float): Defines the grid spacing in units of microns, so that the number of points per bend can be automatically calculated.  Defaults to 0.001 (1 nm).
       * **resist** (string): Must be either '+' or '-'.  Specifies the type of photoresist used.  Defaults to '+'
       * **fab** (string): If 'ETCH', then keeps resist as is, otherwise changes it from '+' to '-' (or vice versa).  This is mainly used to reverse the type of mask used if the fabrication type is 'LIFTOFF'.   Defaults to 'ETCH'.
       * **wg_layer** (int): Layer type used for waveguides.  Defaults to 1.
       * **wg_datatype** (int): Data type used for waveguides.  Defaults to 0.
       * **clad_layer** (int): Layer type used for cladding.  Defaults to 2.
       * **clad_datatype** (int): Data type used for cladding.  Defaults to 0.

    """

    def __init__(
        self,
        wg_type="strip",
        bend_radius=50.0,
        waveguide_stack=None,
        wg_width=2.0,
        clad_width=10.0,
        grid=0.001,
        resist="+",
        fab="ETCH",
        slot=0.1,
        period=0.1,
        duty_cycle=0.5,
        wg_layer=1,
        wg_datatype=0,
        clad_layer=2,
        clad_datatype=0,
        euler_bend=False,
    ):
        self.name = tk.getCellName(
            "WaveguideTemplate"
        )  # Each WaveguideTemplate is given a unique name

        if waveguide_stack == None:
            self.waveguide_stack = [
                [wg_width, (wg_layer, wg_datatype)],
                [2 * clad_width + wg_width, (clad_layer, clad_datatype)],
            ]
            self.wg_width = wg_width
            self.wg_layer = wg_layer
            self.wg_datatype = wg_datatype
            self.clad_width = clad_width
            self.clad_layer = clad_layer
            self.clad_datatype = clad_datatype
        else:
            if len(waveguide_stack) <= 1:
                raise ValueError(
                    "Warning, waveguide_stack must be a list with more than 1 element"
                )
            self.waveguide_stack = waveguide_stack
            self.wg_width = waveguide_stack[0][0]
            self.wg_layer, self.wg_datatype = waveguide_stack[0][1]
            self.clad_width = waveguide_stack[1][0]
            self.clad_layer, self.clad_datatype = waveguide_stack[1][1]

        if wg_type in ["strip", "slot", "swg"]:
            self.wg_type = wg_type
        else:
            raise ValueError("Warning, invalid input for kwarg wg_type.")
        if self.wg_type == "slot":
            self.slot = slot
            self.rail = (self.wg_width - self.slot) / 2.0
            self.rail_dist = self.wg_width - self.rail
        elif self.wg_type == "swg":
            self.period = period
            self.duty_cycle = duty_cycle

        self.bend_radius = bend_radius

        if resist != "+" and resist != "-":
            raise ValueError(
                "Warning, invalid input for kwarg resist in " "WaveguideTemplate"
            )
        if fab == "ETCH":
            self.resist = resist  # default state assumes 'etching'
        else:  # reverse waveguide type if liftoff or something else
            self.resist = "+" if resist == "-" else "-"

        self.grid = grid
        self.euler = euler_bend
        if self.euler:
            self.scale_factor = (
                self.bend_radius / 0.45015815807855303
            )  # Computed from the radius of curvature when the fresnel integrals are at 1/np.sqrt(2.0)
            self.bend_length_90 = 2 * (1.0 / np.sqrt(2.0)) * self.scale_factor
            self.effective_bend_radius = 0.8418389017566366 * self.scale_factor

        if self.wg_type == "swg":
            self.straight_period_cell = gdspy.Cell(
                "swg_seg_"
                + str(self.wg_width)
                + "_"
                + str(self.period)
                + "_"
                + str(self.duty_cycle)
                + "_"
                + str(self.wg_layer)
                + "_"
                + str(self.clad_layer)
            )
            straight_path = gdspy.Path(self.wg_width, initial_point=(0, 0))
            straight_path.segment(
                self.period * self.duty_cycle,
                direction="+x",
                layer=self.wg_layer,
                datatype=self.wg_datatype,
            )
            self.straight_period_cell.add(straight_path)
            self.bend_period_cell = gdspy.Cell(
                "swg_bend_"
                + str(self.wg_width)
                + "_"
                + str(self.period)
                + "_"
                + str(self.duty_cycle)
                + "_"
                + str(self.wg_layer)
                + "_"
                + str(self.clad_layer)
            )
            bend_path = gdspy.Path(self.wg_width, initial_point=(self.bend_radius, 0))
            bend_path.arc(
                self.bend_radius,
                0,
                self.period * self.duty_cycle / self.bend_radius,
                layer=self.wg_layer,
                datatype=self.wg_datatype,
            )
            self.bend_period_cell.add(bend_path)

    def __copy__(self):
        new_wgt = type(self)()
        new_wgt.__dict__.update(self.__dict__)
        new_wgt.name = tk.getCellName("WaveguideTemplate")
        return new_wgt

    def get_num_points_wg(self, angle):
        # This is determined from Eq 1 and 2 in "Design and simulation of silicon photonic schematics and layouts" by Chrostowski et al.
        # Factor of 2 because there are 2 sides of the path
        return 2 * int(
            np.ceil(
                abs(
                    angle
                    * 1.0
                    / np.arccos(2 * (1 - (0.5 * self.grid / self.bend_radius)) ** 2 - 1)
                )
            )
        )

    def get_num_points_curve(self, angle, radius):
        # This is determined from Eq 1 and 2 in "Design and simulation of silicon photonic schematics and layouts" by Chrostowski et al.
        return int(
            np.ceil(
                abs(
                    angle
                    * 1.0
                    / np.arccos(2 * (1 - (0.5 * self.grid / radius)) ** 2 - 1)
                )
            )
        )


class Waveguide(tk.Component):
    """Waveguide Cell class.

    Args:
       * **trace** (list):  List of coordinates used to generate the waveguide (such as '[(x1,y1), (x2,y2), ...]').
       * **wgt** (WaveguideTemplate):  WaveguideTemplate object

    Members:
       * **portlist** (dict): Dictionary with the relevant port information

    Portlist format:
       * portlist['input'] = {'port': (x1,y1), 'direction': 'dir1'}
       * portlist['output'] = {'port': (x2, y2), 'direction': 'dir2'}

    Where in the above (x1,y1) are the first elements of 'trace', (x2, y2) are the last elements of 'trace', and 'dir1', 'dir2' are of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, *or* an angle in *radians*. 'Direction' points *towards* the component that the waveguide will connect to.

    """

    def __init__(self, trace, wgt):
        tk.Component.__init__(self, "Waveguide", locals())

        self.portlist = {}

        self.trace = trace
        self.wgt = wgt
        self.resist = wgt.resist
        self.wg_spec = {"layer": wgt.wg_layer, "datatype": wgt.wg_datatype}
        self.clad_spec = {
            "layer": wgt.clad_layer,
            "datatype": wgt.clad_datatype,
        }  # Used for 'xor' operation

        self.__type_check_trace()

        self.__build_cell()
        self.__build_ports()

    def __normalize_trace(self):
        """Rotates and translates the input trace so the following two constraints are satisfied:
        1. The input point (first point) lies at the origin (0,0)
        2. The second point lies in the +x direction (rot angle = 0.0)

        This allows the trace to be properly hashed, so duplicate traces can be referenced
        rather than have new cells for identical waveguides.
        """
        return NotImplemented

    def __type_check_trace(self):
        trace = []
        """ Round each trace (x,y) point to the nearest 1e-6.
        Prevents some typechecking errors
        """
        for t in self.trace:
            trace.append((round(t[0], 6), round(t[1], 6)))
        self.trace = trace

        """ Type-check trace ¯\_(ツ)_/¯
        """
        prev_dx, prev_dy = 1, 1  # initialize to arbitrary value
        for i in range(len(self.trace) - 1):
            dx = abs(self.trace[i + 1][0] - self.trace[i][0]) + 1e-10
            dy = abs(self.trace[i + 1][1] - self.trace[i][1]) + 1e-10
            if (prev_dx <= 1e-6 and dx <= 1e-6) or (prev_dy <= 1e-6 and dy <= 1e-6):
                raise ValueError(
                    "Warning! Unnecessary waypoint specified.  All"
                    " waypoints must specify a valid bend"
                )
            prev_dx, prev_dy = dx, dy

    def __build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        br = self.wgt.bend_radius

        # add waveguide
        if self.wgt.wg_type == "swg":
            # SWG waveguides consist of both straight segments and bends that are built individually
            segments = [
                [None, None] for i in range(len(self.trace) - 1)
            ]  # list of endpoints for all straight segments
            bends = [
                [None, None, None] for i in range(len(self.trace) - 2)
            ]  # list of arc-centers, start angular positions, and end angular positions for all bends
            prev_dl = 0.0
            for i in range(len(self.trace)):
                if i == 0:
                    segments[i][0] = self.trace[
                        i
                    ]  # if first point in trace, just add as start point of first segment
                elif i == len(self.trace) - 1:
                    segments[i - 1][1] = self.trace[
                        i
                    ]  # if last point in trace, just add as end point of last segment
                else:
                    start_angle = tk.get_exact_angle(self.trace[i - 1], self.trace[i])
                    next_angle = tk.get_exact_angle(self.trace[i], self.trace[i + 1])
                    angle_change = tk.normalize_angle(next_angle - start_angle)

                    # dl is the amount of distance that is taken *off* the waveguide from the curved section
                    dl = abs(br * np.tan(angle_change / 2.0))
                    if (dl + prev_dl) > tk.dist(
                        self.trace[i - 1], self.trace[i]
                    ) + 1e-6:
                        raise ValueError(
                            "Warning! The waypoints "
                            + str(self.trace[i - 1])
                            + " and "
                            + str(self.trace[i])
                            + " are too close to accommodate "
                            " the necessary bend-radius of "
                            + str(br)
                            + ", the points were closer than "
                            + str(dl + prev_dl)
                        )

                    # assign start and end points for segments around this trace point
                    segments[i - 1][1] = tk.translate_point(
                        self.trace[i], dl, start_angle + np.pi
                    )
                    segments[i][0] = tk.translate_point(self.trace[i], dl, next_angle)

                    # calculate arc-center for the bend
                    chord_angle = tk.get_exact_angle(segments[i - 1][1], segments[i][0])
                    bisect_len = abs(br / np.cos(angle_change / 2.0))
                    if angle_change > 0:
                        bends[i - 1][0] = tk.translate_point(
                            self.trace[i], bisect_len, chord_angle + np.pi / 2
                        )
                    else:
                        bends[i - 1][0] = tk.translate_point(
                            self.trace[i], bisect_len, chord_angle - np.pi / 2
                        )

                    # calculate start and end angular positions for the bend
                    if angle_change > 0:
                        bends[i - 1][1] = tk.normalize_angle(start_angle - np.pi / 2)
                        bends[i - 1][2] = tk.normalize_angle(next_angle - np.pi / 2)
                    else:
                        bends[i - 1][1] = tk.normalize_angle(start_angle + np.pi / 2)
                        bends[i - 1][2] = tk.normalize_angle(next_angle + np.pi / 2)

                    prev_dl = dl

            # need to account for partial periods in the following segment and bend building
            # so need to do them interleaving
            remaining_period = 0.0
            for i in range(len(segments)):
                # add straight segment
                segment = segments[i]
                direction = tk.get_exact_angle(segment[0], segment[1])
                direction_deg = direction / np.pi * 180
                total_dist = tk.dist(segment[0], segment[1])
                curr_point = segment[0]
                if (
                    total_dist > remaining_period
                ):  # if the total distance will complete the remaining period from before
                    # finish any partial period leftover from previous segment/bend
                    if remaining_period > self.wgt.period * (1 - self.wgt.duty_cycle):
                        first_path = gdspy.Path(
                            self.wgt.wg_width, initial_point=curr_point
                        )
                        first_path.segment(
                            remaining_period
                            - self.wgt.period * (1 - self.wgt.duty_cycle),
                            direction=direction,
                            **self.wg_spec
                        )
                        self.add(first_path)
                    # add in all whole periods in remaining length
                    curr_point = tk.translate_point(
                        curr_point, remaining_period, direction
                    )
                    remaining_length = total_dist - remaining_period
                    num_periods = int(remaining_length // self.wgt.period)
                    for j in range(num_periods):
                        self.add(
                            gdspy.CellReference(
                                self.wgt.straight_period_cell,
                                origin=curr_point,
                                rotation=direction_deg,
                            )
                        )
                        curr_point = tk.translate_point(
                            curr_point, self.wgt.period, direction
                        )
                    # finish any partial period at end of this segment
                    if (
                        tk.dist(curr_point, segment[1])
                        < self.wgt.period * self.wgt.duty_cycle
                    ):
                        last_path = gdspy.Path(
                            self.wgt.wg_width, initial_point=curr_point
                        )
                        last_path.segment(
                            tk.dist(curr_point, segment[1]),
                            direction=direction,
                            **self.wg_spec
                        )
                        self.add(last_path)
                    else:
                        self.add(
                            gdspy.CellReference(
                                self.wgt.straight_period_cell,
                                origin=curr_point,
                                rotation=direction_deg,
                            )
                        )
                    remaining_period = self.wgt.period - tk.dist(curr_point, segment[1])
                else:  # if total distance did not complete the remaining period from before
                    if remaining_period > self.wgt.period * (1 - self.wgt.duty_cycle):
                        if total_dist > remaining_period - self.wgt.period * (
                            1 - self.wgt.duty_cycle
                        ):
                            first_path = gdspy.Path(
                                self.wgt.wg_width, initial_point=curr_point
                            )
                            first_path.segment(
                                remaining_period
                                - self.wgt.period * (1 - self.wgt.duty_cycle),
                                direction=direction,
                                **self.wg_spec
                            )
                            self.add(first_path)
                        elif total_dist > 0:
                            first_path = gdspy.Path(
                                self.wgt.wg_width, initial_point=curr_point
                            )
                            first_path.segment(
                                total_dist, direction=direction, **self.wg_spec
                            )
                            self.add(first_path)
                    remaining_period = remaining_period - total_dist

                # add bend
                if i != len(bends):
                    bend = bends[i]
                    angle_change = tk.normalize_angle(bend[2] - bend[1])
                    angular_period = self.wgt.period / br
                    curr_angle = bend[1]
                    remaining_angle = remaining_period / br
                    if (
                        abs(angle_change) > remaining_angle
                    ):  # if the angle change will complete the remaining period from before
                        # finish any partial period leftover from previous segment/bend
                        if angle_change > 0:
                            if remaining_angle > angular_period * (
                                1 - self.wgt.duty_cycle
                            ):
                                first_path = gdspy.Path(
                                    self.wgt.wg_width,
                                    initial_point=tk.translate_point(
                                        bend[0], br, curr_angle
                                    ),
                                )
                                first_path.arc(
                                    br,
                                    curr_angle,
                                    curr_angle
                                    + remaining_angle
                                    - angular_period * (1 - self.wgt.duty_cycle),
                                    **self.wg_spec
                                )
                                self.add(first_path)
                            curr_angle += remaining_angle
                        else:
                            if remaining_angle > angular_period * (
                                1 - self.wgt.duty_cycle
                            ):
                                first_path = gdspy.Path(
                                    self.wgt.wg_width,
                                    initial_point=tk.translate_point(
                                        bend[0], br, curr_angle
                                    ),
                                )
                                first_path.arc(
                                    br,
                                    curr_angle,
                                    curr_angle
                                    - (
                                        remaining_angle
                                        - angular_period * (1 - self.wgt.duty_cycle)
                                    ),
                                    **self.wg_spec
                                )
                                self.add(first_path)
                            curr_angle -= remaining_angle
                        # add in all whole periods in remaining angle
                        num_periods = int(
                            br
                            * (abs(angle_change) - remaining_angle)
                            // self.wgt.period
                        )
                        if angle_change > 0:
                            for j in range(num_periods):
                                self.add(
                                    gdspy.CellReference(
                                        self.wgt.bend_period_cell,
                                        origin=bend[0],
                                        rotation=curr_angle / np.pi * 180,
                                    )
                                )
                                curr_angle += angular_period
                            # finish any partial period at end of this bend
                            if (
                                abs(tk.normalize_angle(bend[2] - curr_angle))
                                < angular_period * self.wgt.duty_cycle
                            ):
                                last_path = gdspy.Path(
                                    self.wgt.wg_width,
                                    initial_point=tk.translate_point(
                                        bend[0], br, curr_angle
                                    ),
                                )
                                last_path.arc(br, curr_angle, bend[2], **self.wg_spec)
                                self.add(last_path)
                            else:
                                self.add(
                                    gdspy.CellReference(
                                        self.wgt.bend_period_cell,
                                        origin=bend[0],
                                        rotation=curr_angle / np.pi * 180,
                                    )
                                )
                        else:
                            for j in range(num_periods):
                                self.add(
                                    gdspy.CellReference(
                                        self.wgt.bend_period_cell,
                                        origin=bend[0],
                                        rotation=curr_angle / np.pi * 180,
                                        x_reflection=True,
                                    )
                                )
                                curr_angle -= angular_period
                            # finish any partial period at end of this bend
                            if (
                                abs(tk.normalize_angle(bend[2] - curr_angle))
                                < angular_period * self.wgt.duty_cycle
                            ):
                                last_path = gdspy.Path(
                                    self.wgt.wg_width,
                                    initial_point=tk.translate_point(
                                        bend[0], br, bend[2]
                                    ),
                                )
                                last_path.arc(
                                    br,
                                    bend[2],
                                    bend[2]
                                    + abs(tk.normalize_angle(bend[2] - curr_angle)),
                                    **self.wg_spec
                                )
                                self.add(last_path)
                            else:
                                self.add(
                                    gdspy.CellReference(
                                        self.wgt.bend_period_cell,
                                        origin=bend[0],
                                        rotation=curr_angle / np.pi * 180,
                                        x_reflection=True,
                                    )
                                )
                        remaining_period = self.wgt.period - br * abs(
                            tk.normalize_angle(bend[2] - curr_angle)
                        )
                    else:  # if the angle change did not complete the remaining period from before
                        if remaining_angle > angular_period * (1 - self.wgt.duty_cycle):
                            if abs(angle_change) > remaining_angle - angular_period * (
                                1 - self.wgt.duty_cycle
                            ):
                                if angle_change > 0:
                                    first_path = gdspy.Path(
                                        self.wgt.wg_width,
                                        initial_point=tk.translate_point(
                                            bend[0], br, curr_angle
                                        ),
                                    )
                                    first_path.arc(
                                        br,
                                        curr_angle,
                                        curr_angle
                                        + remaining_angle
                                        - angular_period * (1 - self.wgt.duty_cycle),
                                        **self.wg_spec
                                    )
                                    self.add(first_path)
                                else:
                                    first_path = gdspy.Path(
                                        self.wgt.wg_width,
                                        initial_point=tk.translate_point(
                                            bend[0], br, curr_angle
                                        ),
                                    )
                                    first_path.arc(
                                        br,
                                        curr_angle,
                                        curr_angle
                                        - (
                                            remaining_angle
                                            - angular_period * (1 - self.wgt.duty_cycle)
                                        ),
                                        **self.wg_spec
                                    )
                                    self.add(first_path)
                            else:
                                if angle_change > 0:
                                    first_path = gdspy.Path(
                                        self.wgt.wg_width,
                                        initial_point=tk.translate_point(
                                            bend[0], br, curr_angle
                                        ),
                                    )
                                    first_path.arc(
                                        br,
                                        curr_angle,
                                        curr_angle + angle_change,
                                        **self.wg_spec
                                    )
                                    self.add(first_path)
                                else:
                                    first_path = gdspy.Path(
                                        self.wgt.wg_width,
                                        initial_point=tk.translate_point(
                                            bend[0], br, curr_angle + angle_change
                                        ),
                                    )
                                    first_path.arc(
                                        br,
                                        curr_angle + angle_change,
                                        curr_angle,
                                        **self.wg_spec
                                    )
                                    self.add(first_path)
                        remaining_period = remaining_period - br * abs(angle_change)

            # add cladding
            for i in range(len(self.wgt.waveguide_stack) - 1):
                cur_width = self.wgt.waveguide_stack[i + 1][0]
                cur_spec = {
                    "layer": self.wgt.waveguide_stack[i + 1][1][0],
                    "datatype": self.wgt.waveguide_stack[i + 1][1][1],
                }
                if len(self.trace) == 2:
                    path2 = gdspy.Path(cur_width, self.trace[0])
                    path2.segment(
                        tk.dist(self.trace[0], self.trace[1]),
                        direction=tk.get_exact_angle(self.trace[0], self.trace[1]),
                        **cur_spec
                    )
                else:
                    path2 = gdspy.Path(cur_width, self.trace[0])
                    prev_dl = 0.0
                    for i in range(len(self.trace) - 2):
                        start_angle = tk.get_exact_angle(
                            self.trace[i], self.trace[i + 1]
                        )
                        next_angle = tk.get_exact_angle(
                            self.trace[i + 1], self.trace[i + 2]
                        )

                        # dl is the amount of distance that is taken *off* the waveguide from the curved section
                        dl = abs(br * np.tan((next_angle - start_angle) / 2.0))
                        if (dl + prev_dl) > tk.dist(
                            self.trace[i], self.trace[i + 1]
                        ) + 1e-6:
                            raise ValueError(
                                "Warning! The waypoints "
                                + str(self.trace[i])
                                + " and "
                                + str(self.trace[i + 1])
                                + " are too close to accommodate "
                                " the necessary bend-radius of "
                                + str(br)
                                + ", the points were closer than "
                                + str(dl + prev_dl)
                            )

                        path2.segment(
                            tk.dist(self.trace[i], self.trace[i + 1]) - dl - prev_dl,
                            direction=start_angle,
                            **cur_spec
                        )

                        turnby = tk.normalize_angle(next_angle - start_angle)

                        path2.turn(
                            br,
                            turnby,
                            number_of_points=self.wgt.get_num_points_wg(turnby),
                            **cur_spec
                        )
                        prev_dl = dl

                    path2.segment(
                        tk.dist(self.trace[-2], self.trace[-1]) - prev_dl,
                        direction=next_angle,
                        **cur_spec
                    )
                self.add(path2)

        else:
            """Strip and slot waveguide generation below"""
            self.length = 0.0
            if len(self.trace) == 2:
                if self.wgt.wg_type == "strip":
                    path = gdspy.Path(self.wgt.wg_width, self.trace[0])
                    path.segment(
                        tk.dist(self.trace[0], self.trace[1]),
                        direction=tk.get_exact_angle(self.trace[0], self.trace[1]),
                        **self.wg_spec
                    )
                    self.length += tk.dist(self.trace[0], self.trace[1])
                    print("Initial length: {}".format(tk.dist(self.trace[0], self.trace[1])))
                elif self.wgt.wg_type == "slot":
                    path = gdspy.Path(
                        self.wgt.rail,
                        self.trace[0],
                        number_of_paths=2,
                        distance=self.wgt.rail_dist,
                    )
                    path.segment(
                        tk.dist(self.trace[0], self.trace[1]),
                        direction=tk.get_exact_angle(self.trace[0], self.trace[1]),
                        **self.wg_spec
                    )
                    self.length += tk.dist(self.trace[0], self.trace[1])
                    print("Initial length: {}".format(tk.dist(self.trace[0], self.trace[1])))

                clad_path_list = []
                for c in range(len(self.wgt.waveguide_stack) - 1):
                    cur_width = self.wgt.waveguide_stack[c + 1][0]
                    cur_spec = {
                        "layer": self.wgt.waveguide_stack[c + 1][1][0],
                        "datatype": self.wgt.waveguide_stack[c + 1][1][1],
                    }
                    cp = gdspy.Path(cur_width, self.trace[0])
                    cp.segment(
                        tk.dist(self.trace[0], self.trace[1]),
                        direction=tk.get_exact_angle(self.trace[0], self.trace[1]),
                        **cur_spec
                    )
                    clad_path_list.append(cp)

            else:
                if self.wgt.wg_type == "strip":
                    path = gdspy.Path(self.wgt.wg_width, self.trace[0])
                elif self.wgt.wg_type == "slot":
                    path = gdspy.Path(
                        self.wgt.rail,
                        self.trace[0],
                        number_of_paths=2,
                        distance=self.wgt.rail_dist,
                    )

                clad_path_list = []
                for c in range(len(self.wgt.waveguide_stack) - 1):
                    clad_path_list.append(
                        gdspy.Path(self.wgt.waveguide_stack[c + 1][0], self.trace[0])
                    )

                prev_dl = 0.0
                for i in range(len(self.trace) - 2):
                    start_angle = tk.get_exact_angle(self.trace[i], self.trace[i + 1])
                    next_angle = tk.get_exact_angle(
                        self.trace[i + 1], self.trace[i + 2]
                    )
                    # The following makes sure the turn-by angle is *always* between -pi and +pi
                    turnby = tk.normalize_angle(next_angle - start_angle)

                    # dl is the amount of distance that is taken *off* the waveguide from the curved section
                    if self.wgt.euler == False:
                        dl = abs(br * np.tan((next_angle - start_angle) / 2.0))
                    else:
                        # Generate next Euler bend ahead of time
                        ebend = EBend(
                            self.wgt,
                            turnby,
                            direction=start_angle,
                            vertex=self.trace[i + 1],
                        )
                        dl = ebend.dist_to_vertex
                        self.add(ebend)
                        self.length += ebend.get_bend_length()
                        print("EBend length: {}".format(ebend.get_bend_length()))

                    if (dl + prev_dl) > tk.dist(
                        self.trace[i], self.trace[i + 1]
                    ) + 1e-6:
                        raise ValueError(
                            "Warning! The waypoints "
                            + str(self.trace[i])
                            + " and "
                            + str(self.trace[i + 1])
                            + " are too close to accommodate "
                            " the necessary bend-radius of "
                            + str(br)
                            + ", the points were closer than "
                            + str(dl + prev_dl)
                        )

                    path.segment(
                        tk.dist(self.trace[i], self.trace[i + 1]) - dl - prev_dl,
                        direction=start_angle,
                        **self.wg_spec
                    )
                    self.length += tk.dist(self.trace[i], self.trace[i + 1]) - dl - prev_dl
                    print("Segment length: {}".format(tk.dist(self.trace[i], self.trace[i + 1]) - dl - prev_dl))

                    for c in range(len(self.wgt.waveguide_stack) - 1):
                        cur_spec = {
                            "layer": self.wgt.waveguide_stack[c + 1][1][0],
                            "datatype": self.wgt.waveguide_stack[c + 1][1][1],
                        }
                        clad_path_list[c].segment(
                            tk.dist(self.trace[i], self.trace[i + 1]) - dl - prev_dl,
                            direction=start_angle,
                            **cur_spec
                        )

                    if self.wgt.euler == False:
                        path.turn(
                            br,
                            turnby,
                            number_of_points=self.wgt.get_num_points_wg(turnby),
                            **self.wg_spec
                        )
                        self.length += abs(br * turnby)
                        print("Bend length: {}".format(abs(br * turnby)))

                        for c in range(len(self.wgt.waveguide_stack) - 1):
                            cur_spec = {
                                "layer": self.wgt.waveguide_stack[c + 1][1][0],
                                "datatype": self.wgt.waveguide_stack[c + 1][1][1],
                            }
                            clad_path_list[c].turn(
                                br,
                                turnby,
                                number_of_points=self.wgt.get_num_points_wg(turnby),
                                **cur_spec
                            )
                    else:
                        # Create a new gdspy Path object, since bends are separate objects from straight waveguides
                        self.add(path)
                        for cpath in clad_path_list:
                            self.add(cpath)

                        if self.wgt.wg_type == "strip":
                            path = gdspy.Path(
                                self.wgt.wg_width, ebend.portlist["output"]["port"]
                            )
                        elif self.wgt.wg_type == "slot":
                            path = gdspy.Path(
                                self.wgt.rail,
                                ebend.portlist["output"]["port"],
                                number_of_paths=2,
                                distance=self.wgt.rail_dist,
                            )

                        for c in range(len(self.wgt.waveguide_stack) - 1):
                            clad_path_list[c] = gdspy.Path(
                                self.wgt.waveguide_stack[c + 1][0],
                                ebend.portlist["output"]["port"],
                            )

                    prev_dl = dl

                # Add on the final segment
                path.segment(
                    tk.dist(self.trace[-2], self.trace[-1]) - prev_dl,
                    direction=next_angle,
                    **self.wg_spec
                )
                self.length += tk.dist(self.trace[-2], self.trace[-1]) - prev_dl
                print("Final length: {}".format(tk.dist(self.trace[-2], self.trace[-1]) - prev_dl))
                for c in range(len(self.wgt.waveguide_stack) - 1):
                    cur_spec = {
                        "layer": self.wgt.waveguide_stack[c + 1][1][0],
                        "datatype": self.wgt.waveguide_stack[c + 1][1][1],
                    }
                    clad_path_list[c].segment(
                        tk.dist(self.trace[-2], self.trace[-1]) - prev_dl,
                        direction=next_angle,
                        **cur_spec
                    )

            self.add(path)
            for cpath in clad_path_list:
                self.add(cpath)

    def __build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {
            "port": (self.trace[0][0], self.trace[0][1]),
            "direction": tk.get_exact_angle(self.trace[1], self.trace[0]),
        }
        self.portlist["output"] = {
            "port": (self.trace[-1][0], self.trace[-1][1]),
            "direction": tk.get_exact_angle(self.trace[-2], self.trace[-1]),
        }


if __name__ == "__main__":
    gdspy.current_library = gdspy.GdsLibrary()
    top = gdspy.Cell("top")
    #    wgt1= WaveguideTemplate(wg_type='strip', wg_width=1.0, bend_radius=25, resist='+', euler_bend=True)
    wgt2 = WaveguideTemplate(
        wg_type="slot", wg_width=1.0, bend_radius=25, slot=0.3, resist="+", fab="ETCH"
    )
    wgt3 = WaveguideTemplate(
        wg_type="swg",
        wg_width=1.0,
        bend_radius=25,
        duty_cycle=0.50,
        period=1.0,
        resist="+",
        fab="ETCH",
    )
    wg_stack = [[0.5, (1, 0)], [2.0, (2, 0)], [10, (4, 0)]]
    wgt1 = WaveguideTemplate(
        wg_type="slot",
        wg_width=1.0,
        bend_radius=25,
        slot=0.3,
        waveguide_stack=wg_stack,
        resist="+",
        euler_bend=False,
    )

    space = 10.0
    wg1 = Waveguide(
        [
            (0, 0),
            (140.0 - space, 0),
            (160.0 - space, 100.0),
            (300.0, 100.0),
            (400, 150.0),
            (200, -300),
            (-500, 100),
            (-500, -200),
            # (0, 0), # These are Manhattan grid waypoints
            # (300, 0),
            # (300.0, 100.0),
            # (900.0, 100.0),
            # (900.0, -400.0),
            # (-1900.0, -400.0),
            # (-1900, 800),
            # (-600, 800)
        ],
        wgt1,
    )
    print("wg1 length = {}".format(wg1.length))
    print("wg1 length (other way) = {}".format(tk.get_trace_length(wg1.trace, wgt1)))
    tk.add(top, wg1)
    wg2 = Waveguide(
        [(0, -space), (140.0, -space), (160.0, 50.0 - space), (300.0, 50.0 - space)],
        wgt2,
    )
    tk.add(top, wg2)
    wg3 = Waveguide(
        [
            (0, -2 * space),
            (140.0 + space, -2 * space),
            (160.0 + space, 50.0 - 2 * space),
            (300.0, 50.0 - 2 * space),
        ],
        wgt3,
    )
    tk.add(top, wg3)

    gdspy.LayoutViewer()
#    gdspy.write_gds('waveguide.gds', unit=1.0e-6, precision=1.0e-9)

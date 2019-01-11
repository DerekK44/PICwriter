# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk

class WaveguideTemplate:
    """ Template for waveguides that contains standard information about the geometry and fabrication.  Supported waveguide types are **strip** (also known as "channel" waveguides), **slot**, and **SWG** ("sub-wavelength grating", or 1D photonic crystal waveguides).

        Keyword Args:
           * **wg_type** (string): Type of waveguide used.  Options are "strip", "slot", and "swg".  Defaults to "strip".
           * **bend_radius** (float): Radius of curvature for waveguide bends (circular).  Defaults to 50.
           * **wg_width** (float): Width of the waveguide as shown on the mask.  Defaults to 2.
           * **slot** (float): Size of the waveguide slot region.  This is only used if `wg_type`=`'slot'`.  Defaults to 0.1.
           * **period** (float): Period of the SWG. This is only used if `wg_type`=`'swg'`. Defaults to 0.1.
           * **duty_cycle** (float): Duty cycle of the SWG. This is only used if `wg_type`=`'swg'`. Defaults to 0.5.
           * **clad_width** (float): Width of the cladding (region next to waveguide, mainly used for positive-type photoresists + etching, or negative-type and liftoff).  Defaults to 10.
           * **resist** (string): Must be either '+' or '-'.  Specifies the type of photoresist used.  Defaults to '+'
           * **fab** (string): If 'ETCH', then keeps resist as is, otherwise changes it from '+' to '-' (or vice versa).  This is mainly used to reverse the type of mask used if the fabrication type is 'LIFTOFF'.   Defaults to 'ETCH'.
           * **wg_layer** (int): Layer type used for waveguides.  Defaults to 1.
           * **wg_datatype** (int): Data type used for waveguides.  Defaults to 0.
           * **clad_layer** (int): Layer type used for cladding.  Defaults to 2.
           * **clad_datatype** (int): Data type used for cladding.  Defaults to 0.

    """
    def __init__(self, wg_type='strip', bend_radius=50.0, wg_width=2.0, clad_width=10.0,
                 resist='+', fab='ETCH', slot=0.1, period=0.1, duty_cycle=0.5,
                 wg_layer=1, wg_datatype=0, clad_layer=2, clad_datatype=0):
        self.wg_width = wg_width
        if wg_type in ['strip', 'slot', 'swg']:
            self.wg_type = wg_type
        else:
            raise ValueError("Warning, invalid input for kwarg wg_type.")
        if self.wg_type =='slot':
            self.slot = slot
            self.rail = (self.wg_width - self.slot)/2.0
            self.rail_dist = self.wg_width -self.rail
        elif self.wg_type =='swg':
            self.period = period
            self.duty_cycle = duty_cycle

        self.bend_radius = bend_radius
        self.clad_width = clad_width
        if resist != '+' and resist != '-':
            raise ValueError("Warning, invalid input for kwarg resist in "
                             "WaveguideTemplate")
        if fab=='ETCH':
            self.resist = resist #default state assumes 'etching'
        else: #reverse waveguide type if liftoff or something else
            self.resist = '+' if resist=='-' else '-'

        self.wg_layer = wg_layer
        self.wg_datatype = wg_datatype
        self.clad_layer = clad_layer
        self.clad_datatype = clad_datatype

        if self.wg_type =='swg':
            self.straight_period_cell = gdspy.Cell("swg_seg_"+str(self.wg_width)+"_"+str(self.period)+"_"+str(self.duty_cycle)+"_"+str(self.wg_layer)+"_"+str(self.clad_layer))
            straight_path = gdspy.Path(self.wg_width, initial_point=(0,0))
            straight_path.segment(self.period*self.duty_cycle, direction='+x', layer=self.wg_layer, datatype=self.wg_datatype)
            self.straight_period_cell.add(straight_path)
            self.bend_period_cell = gdspy.Cell("swg_bend_"+str(self.wg_width)+"_"+str(self.period)+"_"+str(self.duty_cycle)+"_"+str(self.wg_layer)+"_"+str(self.clad_layer))
            bend_path = gdspy.Path(self.wg_width, initial_point=(self.bend_radius,0))
            bend_path.arc(self.bend_radius, 0, self.period*self.duty_cycle/self.bend_radius, layer=self.wg_layer, datatype=self.wg_datatype)
            self.bend_period_cell.add(bend_path)

class Waveguide(gdspy.Cell):
    """ Waveguide Cell class (subclass of gdspy.Cell).

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
        gdspy.Cell.__init__(self,"Waveguide--"+str(uuid.uuid4()))

        self.portlist = {}

        self.trace = trace
        self.wgt = wgt
        self.resist = wgt.resist
        self.wg_spec = {'layer': wgt.wg_layer, 'datatype': wgt.wg_datatype}
        self.clad_spec = {'layer': wgt.clad_layer, 'datatype': wgt.clad_datatype} #Used for 'xor' operation

        self.type_check_trace()
        self.build_cell()
        self.build_ports()

    def type_check_trace(self):
        trace = []
        """ Round each trace (x,y) point to the nearest 1e-6.
        Prevents some typechecking errors
        """
        for t in self.trace:
            trace.append((round(t[0], 6), round(t[1], 6)))
        self.trace = trace

        """ Type-check trace ¯\_(ツ)_/¯
        """
        prev_dx, prev_dy = 1,1 #initialize to arbitrary value
        for i in range(len(self.trace)-1):
            dx = abs(self.trace[i+1][0]-self.trace[i][0])+1E-10
            dy = abs(self.trace[i+1][1]-self.trace[i][1])+1E-10
            if ((prev_dx <= 1e-6 and dx<=1e-6) or (prev_dy <= 1e-6 and dy<=1e-6)):
                raise ValueError("Warning! Unnecessary waypoint specified.  All"
                                 " waypoints must specify a valid bend")
            prev_dx, prev_dy = dx, dy

    def build_cell(self):
        # Sequentially build all the geometric shapes using gdspy path functions
        # for waveguide, then add it to the Cell
        br = self.wgt.bend_radius

        # add waveguide
        if self.wgt.wg_type=='swg':
            # SWG waveguides consist of both straight segments and bends that are built individually
            segments = [[None,None] for i in range(len(self.trace)-1)] # list of endpoints for all straight segments
            bends = [[None,None,None] for i in range(len(self.trace)-2)] # list of arc-centers, start angular positions, and end angular positions for all bends
            prev_dl = 0.0
            for i in range(len(self.trace)):
                if i == 0:
                    segments[i][0] = self.trace[i] # if first point in trace, just add as start point of first segment
                elif i == len(self.trace)-1:
                    segments[i-1][1] = self.trace[i] # if last point in trace, just add as end point of last segment
                else:
                    start_angle = tk.get_exact_angle(self.trace[i-1], self.trace[i])
                    next_angle = tk.get_exact_angle(self.trace[i], self.trace[i+1])
                    angle_change = tk.normalize_angle(next_angle-start_angle)

                    #dl is the amount of distance that is taken *off* the waveguide from the curved section
                    dl = abs(br*np.tan(angle_change/2.0))
                    if (dl+prev_dl) > tk.dist(self.trace[i-1], self.trace[i])+1E-6:
                        raise ValueError("Warning! The waypoints "+str(self.trace[i-1])+" and "+str(self.trace[i])+" are too close to accommodate "
                                         " the necessary bend-radius of "+str(br)+", the points were closer than "+str(dl+prev_dl))

                    # assign start and end points for segments around this trace point
                    segments[i-1][1] = tk.translate_point(self.trace[i], dl, start_angle+np.pi)
                    segments[i][0] = tk.translate_point(self.trace[i], dl, next_angle)

                    # calculate arc-center for the bend
                    chord_angle = tk.get_exact_angle(segments[i-1][1], segments[i][0])
                    bisect_len = abs(br/np.cos(angle_change/2.0))
                    if angle_change > 0:
                        bends[i-1][0] = tk.translate_point(self.trace[i], bisect_len, chord_angle+np.pi/2)
                    else:
                        bends[i-1][0] = tk.translate_point(self.trace[i], bisect_len, chord_angle-np.pi/2)

                    # calculate start and end angular positions for the bend
                    if angle_change > 0:
                        bends[i-1][1] = tk.normalize_angle(start_angle - np.pi/2)
                        bends[i-1][2] = tk.normalize_angle(next_angle - np.pi/2)
                    else:
                        bends[i-1][1] = tk.normalize_angle(start_angle + np.pi/2)
                        bends[i-1][2] = tk.normalize_angle(next_angle + np.pi/2)

                    prev_dl = dl

            # need to account for partial periods in the following segment and bend building
            # so need to do them interleaving
            remaining_period = 0.0
            for i in range(len(segments)):
                # add straight segment
                segment = segments[i]
                direction = tk.get_exact_angle(segment[0], segment[1])
                direction_deg = direction/np.pi*180
                total_dist = tk.dist(segment[0], segment[1])
                curr_point = segment[0]
                if total_dist > remaining_period: # if the total distance will complete the remaining period from before
                    # finish any partial period leftover from previous segment/bend
                    if remaining_period > self.wgt.period*(1-self.wgt.duty_cycle):
                        first_path = gdspy.Path(self.wgt.wg_width, initial_point=curr_point)
                        first_path.segment(remaining_period-self.wgt.period*(1-self.wgt.duty_cycle), direction=direction, **self.wg_spec)
                        self.add(first_path)
                    # add in all whole periods in remaining length
                    curr_point = tk.translate_point(curr_point, remaining_period, direction)
                    remaining_length = total_dist - remaining_period
                    num_periods = int(remaining_length//self.wgt.period)
                    for j in range(num_periods):
                        self.add(gdspy.CellReference(self.wgt.straight_period_cell, origin=curr_point, rotation=direction_deg))
                        curr_point = tk.translate_point(curr_point, self.wgt.period, direction)
                    # finish any partial period at end of this segment
                    if tk.dist(curr_point, segment[1]) < self.wgt.period*self.wgt.duty_cycle:
                        last_path = gdspy.Path(self.wgt.wg_width, initial_point=curr_point)
                        last_path.segment(tk.dist(curr_point, segment[1]), direction=direction, **self.wg_spec)
                        self.add(last_path)
                    else:
                        self.add(gdspy.CellReference(self.wgt.straight_period_cell, origin=curr_point, rotation=direction_deg))
                    remaining_period = self.wgt.period - tk.dist(curr_point, segment[1])
                else: # if total distance did not complete the remaining period from before
                    if remaining_period > self.wgt.period*(1-self.wgt.duty_cycle):
                        if total_dist > remaining_period-self.wgt.period*(1-self.wgt.duty_cycle):
                            first_path = gdspy.Path(self.wgt.wg_width, initial_point=curr_point)
                            first_path.segment(remaining_period-self.wgt.period*(1-self.wgt.duty_cycle), direction=direction, **self.wg_spec)
                            self.add(first_path)
                        elif total_dist > 0:
                            first_path = gdspy.Path(self.wgt.wg_width, initial_point=curr_point)
                            first_path.segment(total_dist, direction=direction, **self.wg_spec)
                            self.add(first_path)
                    remaining_period = remaining_period-total_dist


                # add bend
                if i != len(bends):
                    bend = bends[i]
                    angle_change = tk.normalize_angle(bend[2]-bend[1])
                    angular_period = self.wgt.period/br
                    curr_angle = bend[1]
                    remaining_angle = remaining_period/br
                    if abs(angle_change) > remaining_angle: # if the angle change will complete the remaining period from before
                        # finish any partial period leftover from previous segment/bend
                        if angle_change > 0:
                            if remaining_angle > angular_period*(1-self.wgt.duty_cycle):
                                first_path = gdspy.Path(self.wgt.wg_width, initial_point=tk.translate_point(bend[0], br, curr_angle))
                                first_path.arc(br, curr_angle, curr_angle+remaining_angle-angular_period*(1-self.wgt.duty_cycle), **self.wg_spec)
                                self.add(first_path)
                            curr_angle += remaining_angle
                        else:
                            if remaining_angle > angular_period*(1-self.wgt.duty_cycle):
                                first_path = gdspy.Path(self.wgt.wg_width, initial_point=tk.translate_point(bend[0], br, curr_angle))
                                first_path.arc(br, curr_angle, curr_angle-(remaining_angle-angular_period*(1-self.wgt.duty_cycle)), **self.wg_spec)
                                self.add(first_path)
                            curr_angle -= remaining_angle
                        # add in all whole periods in remaining angle
                        num_periods = int(br*(abs(angle_change)-remaining_angle)//self.wgt.period)
                        if angle_change > 0:
                            for j in range(num_periods):
                                self.add(gdspy.CellReference(self.wgt.bend_period_cell, origin=bend[0], rotation=curr_angle/np.pi*180))
                                curr_angle += angular_period
                            # finish any partial period at end of this bend
                            if abs(tk.normalize_angle(bend[2]-curr_angle)) < angular_period*self.wgt.duty_cycle:
                                last_path = gdspy.Path(self.wgt.wg_width, initial_point=tk.translate_point(bend[0], br, curr_angle))
                                last_path.arc(br, curr_angle, bend[2], **self.wg_spec)
                                self.add(last_path)
                            else:
                                self.add(gdspy.CellReference(self.wgt.bend_period_cell, origin=bend[0], rotation=curr_angle/np.pi*180))
                        else:
                            for j in range(num_periods):
                                self.add(gdspy.CellReference(self.wgt.bend_period_cell, origin=bend[0], rotation=curr_angle/np.pi*180, x_reflection=True))
                                curr_angle -= angular_period
                            # finish any partial period at end of this bend
                            if abs(tk.normalize_angle(bend[2]-curr_angle)) < angular_period*self.wgt.duty_cycle:
                                last_path = gdspy.Path(self.wgt.wg_width, initial_point=tk.translate_point(bend[0], br, bend[2]))
                                last_path.arc(br, bend[2], bend[2]+abs(tk.normalize_angle(bend[2]-curr_angle)), **self.wg_spec)
                                self.add(last_path)
                            else:
                                self.add(gdspy.CellReference(self.wgt.bend_period_cell, origin=bend[0], rotation=curr_angle/np.pi*180, x_reflection=True))
                        remaining_period = self.wgt.period - br*abs(tk.normalize_angle(bend[2]-curr_angle))
                    else: # if the angle change did not complete the remaining period from before
                        if remaining_angle > angular_period*(1-self.wgt.duty_cycle):
                            if abs(angle_change) > remaining_angle-angular_period*(1-self.wgt.duty_cycle):
                                if angle_change > 0:
                                    first_path = gdspy.Path(self.wgt.wg_width, initial_point=tk.translate_point(bend[0], br, curr_angle))
                                    first_path.arc(br, curr_angle, curr_angle+remaining_angle-angular_period*(1-self.wgt.duty_cycle), **self.wg_spec)
                                    self.add(first_path)
                                else:
                                    first_path = gdspy.Path(self.wgt.wg_width, initial_point=tk.translate_point(bend[0], br, curr_angle))
                                    first_path.arc(br, curr_angle, curr_angle-(remaining_angle-angular_period*(1-self.wgt.duty_cycle)), **self.wg_spec)
                                    self.add(first_path)
                            else:
                                if angle_change > 0:
                                    first_path = gdspy.Path(self.wgt.wg_width, initial_point=tk.translate_point(bend[0], br, curr_angle))
                                    first_path.arc(br, curr_angle, curr_angle+angle_change, **self.wg_spec)
                                    self.add(first_path)
                                else:
                                    first_path = gdspy.Path(self.wgt.wg_width, initial_point=tk.translate_point(bend[0], br, curr_angle+angle_change))
                                    first_path.arc(br, curr_angle+angle_change, curr_angle, **self.wg_spec)
                                    self.add(first_path)
                        remaining_period = remaining_period - br*abs(angle_change)

        else:
            # Strip and slot waveguide generation below
            if len(self.trace)==2:
                if self.wgt.wg_type=='strip':
                    path = gdspy.Path(self.wgt.wg_width, self.trace[0])
                    path.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_exact_angle(self.trace[0], self.trace[1]), **self.wg_spec)
                elif self.wgt.wg_type=='slot':
                    path = gdspy.Path(self.wgt.rail, self.trace[0], number_of_paths=2, distance=self.wgt.rail_dist)
                    path.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_exact_angle(self.trace[0], self.trace[1]), **self.wg_spec)
            else:
                if self.wgt.wg_type=='strip':
                    path = gdspy.Path(self.wgt.wg_width, self.trace[0])
                elif self.wgt.wg_type=='slot':
                    path = gdspy.Path(self.wgt.rail, self.trace[0], number_of_paths=2, distance=self.wgt.rail_dist)

                prev_dl = 0.0
                for i in range(len(self.trace)-2):
                    start_angle = tk.get_exact_angle(self.trace[i], self.trace[i+1])
                    next_angle = tk.get_exact_angle(self.trace[i+1], self.trace[i+2])

                    #dl is the amount of distance that is taken *off* the waveguide from the curved section
                    dl = abs(br*np.tan((next_angle-start_angle)/2.0))
                    if (dl+prev_dl) > tk.dist(self.trace[i], self.trace[i+1])+1E-6:
                        raise ValueError("Warning! The waypoints "+str(self.trace[i])+" and "+str(self.trace[i+1])+" are too close to accommodate "
                                         " the necessary bend-radius of "+str(br)+", the points were closer than "+str(dl+prev_dl))

                    path.segment(tk.dist(self.trace[i], self.trace[i+1])-dl-prev_dl,
                                 direction=start_angle, **self.wg_spec)

                    # The following makes sure the turn-by angle is *always* between -pi and +pi
                    turnby = tk.normalize_angle(next_angle - start_angle)

                    path.turn(br, turnby, number_of_points=0.1, **self.wg_spec)
                    prev_dl = dl

                path.segment(tk.dist(self.trace[-2], self.trace[-1])-prev_dl,
                             direction=next_angle, **self.wg_spec)

            self.add(path)

        # add cladding
        if len(self.trace)==2:
            path2 = gdspy.Path(self.wgt.wg_width+2*self.wgt.clad_width, self.trace[0])
            path2.segment(tk.dist(self.trace[0], self.trace[1]), direction=tk.get_exact_angle(self.trace[0], self.trace[1]), **self.clad_spec)
        else:
            path2 = gdspy.Path(self.wgt.wg_width+2*self.wgt.clad_width, self.trace[0])
            prev_dl = 0.0
            for i in range(len(self.trace)-2):
                start_angle = tk.get_exact_angle(self.trace[i], self.trace[i+1])
                next_angle = tk.get_exact_angle(self.trace[i+1], self.trace[i+2])

                #dl is the amount of distance that is taken *off* the waveguide from the curved section
                dl = abs(br*np.tan((next_angle-start_angle)/2.0))
                if (dl+prev_dl) > tk.dist(self.trace[i], self.trace[i+1])+1E-6:
                    raise ValueError("Warning! The waypoints "+str(self.trace[i])+" and "+str(self.trace[i+1])+" are too close to accommodate "
                                     " the necessary bend-radius of "+str(br)+", the points were closer than "+str(dl+prev_dl))

                path2.segment(tk.dist(self.trace[i], self.trace[i+1])-dl-prev_dl,
                              direction=start_angle, **self.clad_spec)

                turnby = tk.normalize_angle(next_angle - start_angle)

                path2.turn(br, turnby, number_of_points=0.1, **self.clad_spec)
                prev_dl = dl

            path2.segment(tk.dist(self.trace[-2], self.trace[-1])-prev_dl,
                          direction=next_angle, **self.clad_spec)
        self.add(path2)


    def build_ports(self):
        # Portlist format:
        # example: example:  {'port':(x_position, y_position), 'direction': 'NORTH'}
        self.portlist["input"] = {'port':(self.trace[0][0], self.trace[0][1]),
                                  'direction': tk.get_exact_angle(self.trace[1], self.trace[0])}
        self.portlist["output"] = {'port':(self.trace[-1][0], self.trace[-1][1]),
                                   'direction':tk.get_exact_angle(self.trace[-2], self.trace[-1])}

if __name__ == "__main__":
    gdspy.current_library = gdspy.GdsLibrary()
    top = gdspy.Cell("top")
    wgt1= WaveguideTemplate(wg_type='strip', wg_width=1.0, bend_radius=25, resist='+', fab="ETCH")
    wgt2= WaveguideTemplate(wg_type='slot', wg_width=1.0, bend_radius=25, slot=0.3, resist='+', fab="ETCH")
    wgt3= WaveguideTemplate(wg_type='swg', wg_width=1.0, bend_radius=25, duty_cycle=0.50, period=1.0, resist='+', fab="ETCH")

    space = 10.0
    wg1=Waveguide([(0, 0), (140.0-space, 0), (160.0-space, 50.0), (300.0, 50.0)], wgt1)
    tk.add(top, wg1)
    wg2=Waveguide([(0, -space), (140.0, -space), (160.0, 50.0-space), (300.0, 50.0-space)], wgt2)
    tk.add(top, wg2)
    wg3=Waveguide([(0, -2*space), (140.0+space, -2*space), (160.0+space, 50.0-2*space), (300.0, 50.0-2*space)], wgt3)
    tk.add(top, wg3)

    gdspy.LayoutViewer()
    gdspy.write_gds('waveguide.gds', unit=1.0e-6, precision=1.0e-9)

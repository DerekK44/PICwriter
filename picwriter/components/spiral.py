# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import gdspy
import uuid
import picwriter.toolkit as tk
from picwriter.components.waveguide import Waveguide

class Spiral(gdspy.Cell):
    """ Spiral Waveguide Cell class (subclass of gdspy.Cell).  The desired length of the spiral is first set, along with the spacing between input and output (the 'width' paramter).  Then, the corresponding height of the spiral is automatically set.

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
    def __init__(self, wgt, width, length, spacing=None, parity=1, port=(0,0), direction="NORTH"):
        gdspy.Cell.__init__(self, "Spiral--"+str(uuid.uuid4()))

        self.portlist = {}

        self.width = width
        self.length = length
        self.parity = parity
        self.port = port
        self.spacing=3*wgt.clad_width if spacing==None else spacing


        self.wgt = wgt
        self.bend_radius = wgt.bend_radius
        self.direction = direction

        self.corner_dl = 2*wgt.bend_radius - (0.5*np.pi*wgt.bend_radius)

        if width < self.spacing + 5*self.bend_radius:
            raise ValueError("Warning!  Given the WaveguideTemplate 'bend radius' and 'spacing' specified, no spiral can be fit within the requested 'width'.  Please increase the 'width'.")

        self.nmax = int((self.width - self.spacing - 5*self.bend_radius)/(2*self.spacing))

        self.build_cell()
        self.build_ports()

    def fixed_len(self, h):
        w = self.width
        s = self.spacing
        br = self.bend_radius
        wcent = (w-s-br)/2.0
        return 2*wcent + (h - s) + wcent + br + h + (w-br) + (h-s) + wcent

    def spiral_len(self, h, n):
        if n==0:
            return 0
        else:
            w = self.width
            s = self.spacing
            br = self.bend_radius
            wcent = (w-s-br)/2.0
            return 2*((2*(wcent - n*s)) + (h-s-2*n*s))

    def middle_len(self, h, n):
        return (h - 2*self.spacing) - 2*n*self.spacing

    def get_length(self, h, n):
        # Return the length of the spiral given the height and number of wraps, "n"
        num_points = 10 + 4*n


        length = self.fixed_len(h)
        length += sum([self.spiral_len(h, i+1) for i in range(n)])
        length += self.middle_len(h, n)
        length -= (num_points - 2)*self.corner_dl
        return length

    def get_hmin(self, n):
        # Determine the minimum height corresponding to the spiral parameters and # of spiral turns, 'n'
        br = self.bend_radius
        s = self.spacing
        return 2*br + 2*s + 2*n*s

    def get_spiral_length(self):
		#Returns the true length of the spiral, including length from the turns
        return self.actual_length

    def get_number_of_spirals(self):
        # Find the ideal number of loops required to make the spiral such that the
        # spiral is wound as tightly as possible.  This means that the required height
        # of the spiral should be minimized appropriately.
        length_goal = self.length

        n = 0
        hmin = self.get_hmin(n)
        length_min = self.get_length(hmin, n)
        while (length_min < length_goal) and n < self.nmax:
            n += 1
            hmin = self.get_hmin(n)
            length_min = self.get_length(hmin, n)

        if n==0:
            if length_min > length_goal:
                raise ValueError("Warning! No value of 'n' (number of spirals) could be determined, since the minimum spiral length ("+str(length_min)+") is already larger than the goal ("+str(length_goal)+").  Please decrease the spiral width.")
            else:
                return n
        else:
            return n-1

    def get_spiral_height(self, n):
        # n is the number of spirals
        # Returns the appropriate height ( > hmin) such that
        num_wg_segments = 4 + 2*n

        hmin = self.get_hmin(n)
        delta_length = self.length - self.get_length(hmin, n)
        hnew = hmin + (delta_length/num_wg_segments)

        return hnew

    def build_cell(self):
        # Determine the correct set of waypoints, then feed this over to a
        # Waveguide() class.
        # This is just one way of doing it... ¯\_(ツ)_/¯

        # Determine the number of spiral wraps
        n = self.get_number_of_spirals()

        """ Determine the corresponding spiral height
        """
        h = self.get_spiral_height(n)

        w = self.width
        length = self.length
        br = self.wgt.bend_radius
        s = self.spacing

        """ Double check all parameters
        """
        if abs(length - self.get_length(h, n)) > 1E-6:
            raise ValueError("Warning! The computed length and desired length are not equal!")

        """ Now that the parameters are all determined, build the corresponding
        waypoints """
        wcent = (w-s-br)/2.0

        p = self.parity
        x0, y0 = 0,0

        """ Start/end points corresponding to 'fixed_len' unit """
        start_points = [(x0, y0),
                        (x0 + 2*wcent, y0),
                        (x0 + 2*wcent, y0 - p*(h - s))]
        end_points = [(x0, y0 - p*s),
                      (x0, y0 - p*h),
                      (x0 + w - br, y0 - p*h),
                      (x0 + w - br, y0),
                      (x0 + w, y0)]

        """ Generate the spiral going inwards """
        spiral_in_pts = []

        x_left_start, x_right_start = x0 + s, x0+2*wcent-2*s
        y_top_start, y_bot_start = y0 - p*2*s, y0 - p*(h-s)

        for j in range(n):
            i = j+1
            if i%2==1: #ODD, so add a segment on the LEFT
                left_segment_index = (i-1)/2
                spiral_in_pts.append((x_left_start + 2*s*left_segment_index, y_bot_start + p*(2*s*left_segment_index)))
                spiral_in_pts.append((x_left_start + 2*s*left_segment_index, y_top_start - p*(2*s*left_segment_index)))
                if j+1==n: #This is the last one! Add the middle point now
                    spiral_in_pts.append((x0+wcent, y_top_start - p*(2*s*left_segment_index)))
            if i%2==0: #EVEN, so add a segment on the RIGHT
                right_segment_index = (i-2)/2
                spiral_in_pts.append((x_right_start - (2*s*right_segment_index), y_top_start - p*(2*s*right_segment_index)))
                spiral_in_pts.append((x_right_start - (2*s*right_segment_index), y_bot_start + p*(2*s*right_segment_index + 2*s)))
                if j+1==n: #This is the last one! Add the middle point now
                    spiral_in_pts.append((x0+wcent, y_bot_start + p*(2*s*right_segment_index + 2*s)))

        if n==0:
            spiral_in_pts.append((x0+wcent, y_bot_start))

        """ Generate the spiral going outwards """
        spiral_out_pts = []

        x_left_start, x_right_start = x0 + 2*s, x0+2*wcent - s
        y_top_start, y_bot_start = y0 - p*s, y0 - p*(h-2*s)

        for j in range(n):
            i = j+1
            if i%2==1: #ODD, so add a segment on the RIGHT
                right_segment_index = (i-1)/2
                spiral_out_pts.append((x_right_start - 2*s*right_segment_index, y_top_start - p*2*s*right_segment_index))
                spiral_out_pts.append((x_right_start - 2*s*right_segment_index, y_bot_start + p*(2*s*right_segment_index)))
                if j+1==n: #This is the last one! Add the middle point now
                    spiral_out_pts.append((x0+wcent, y_bot_start + p*2*s*right_segment_index))

            elif i%2==0: #EVEN, add a segment on the LEFT
                left_segment_index = (i-2)/2
                spiral_out_pts.append((x_left_start + 2*s*left_segment_index, y_bot_start + p*2*s*left_segment_index))
                spiral_out_pts.append((x_left_start + 2*s*left_segment_index, y_top_start - p*(2*s*left_segment_index + 2*s)))
                if j+1==n: #This is the last one! Add the middle point now
                    spiral_out_pts.append((x0+wcent, y_top_start - p*(2*s*left_segment_index + 2*s)))

        if n==0:
            spiral_out_pts.append((x0+wcent, y_top_start))

        spiral_out_pts.reverse() #reverse order

        waypoints = start_points+spiral_in_pts+spiral_out_pts+end_points

        """ Independently verify that the length of the spiral structure generated is correct
        """
        l=0
        for i in range(len(waypoints)-1):
            dx, dy = waypoints[i+1][0]-waypoints[i][0], waypoints[i+1][1]-waypoints[i][1]
            l += np.sqrt(dx**2 + dy**2)
        num_corners = len(waypoints)-2
        l -= num_corners*self.corner_dl

        self.actual_length = l

        if abs(l - self.length) > 1E-6:
            print("Actual computed length = "+str(l))
            print("Expected length = "+str(self.length))
            raise ValueError("Warning! Spiral generated is significantly different from what is expected.")

        """ Generate the waveguide """
        wg = Waveguide(waypoints, self.wgt)

        dist = self.width
        if self.direction=="WEST":
            wgr = gdspy.CellReference(wg, rotation=180)
            self.portlist_output = (self.port[0]-dist, self.port[1])
        elif self.direction=="SOUTH":
            wgr = gdspy.CellReference(wg, rotation=-90)
            self.portlist_output = (self.port[0], self.port[1]-dist)
        elif self.direction=="EAST":
            wgr = gdspy.CellReference(wg, rotation=0.0)
            self.portlist_output = (self.port[0]+dist, self.port[1])
        elif self.direction=="NORTH":
            wgr = gdspy.CellReference(wg, rotation=90)
            self.portlist_output = (self.port[0], self.port[1]+dist)
        elif isinstance(self.direction, float) or isinstance(self.direction, int):
            wgr = gdspy.CellReference(wg, rotation=(float(self.direction)*180/np.pi))
            self.portlist_output = (self.port[0]+dist*np.cos(float(self.direction)), self.port[1]+dist*np.sin(float(self.direction)))

        wgr.translate(self.port[0], self.port[1])
        self.add(wgr)

    def build_ports(self):
        # Portlist format:
        #    example:  {'port':(x_position, y_position), 'direction': 'NORTH'}

        self.portlist["input"] = {'port':self.port,
                                    'direction':tk.flip_direction(self.direction)}
        self.portlist["output"] = {'port':self.portlist_output,
                                    'direction':self.direction}

if __name__ == "__main__":
    from picwriter.components.waveguide import WaveguideTemplate
    gdspy.current_library = gdspy.GdsLibrary()
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50,
                            wg_width=1.0,
                            clad_width=10.0)

    sp1 = Spiral(wgt,
                 width=300.0,
                 length=20000.0,
                 spacing=50.0,
                 parity=1,
                 port=(0,0),
                 direction='WEST')
    tk.add(top, sp1)

    print("length is "+str(sp1.get_spiral_length()))
    print("portlist = "+str(sp1.portlist))

    gdspy.LayoutViewer()
    # gdspy.write_gds('spiral.gds', unit=1.0e-6, precision=1.0e-9)

# -*- coding: utf-8 -*-
"""
Set of useful functions for converting PICwriter objects from polygons to hdf5 epsilon files that
can be easily imported to MEEP or MPB for quick simulations.  Functions for launching siulations using
MEEP/MPB are also included.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import gdspy
import h5py

class MaterialStack:
    """ Standard template for generating a material stack

        Args:
           * **vsize** (float): Vertical size of the material stack in microns (um)
           * **default_layer** (list): Default VStack with the following format: [(eps1, t1), (eps2, t2), (eps3, t3), ...] where eps1, eps2, .. are the permittivity (float), and t1, t2, .. are the thicknesses (float) from bottom to top. Note: t1+t2+... *must* add up to vsize.

        Members:
           * **stacklist** (dictionary): Each entry of the stacklist dictionary contains a VStack list.

        Keyword Args:
           * **name** (string): Identifier (optional) for the material stack

    """
    def __init__(self, vsize, default_stack, name="mstack"):
        self.name = name
        self.vsize = vsize
        self.default_stack = default_stack

        """ self.stack below contains a DICT of all the VStack lists """
        self.stacklist = {}

        self.addVStack(-1, -1, default_stack)

    def addVStack(self, layer, datatype, stack):
        """ Adds a vertical layer to the material stack LIST

        Args:
           * **layer** (int): Layer of the VStack
           * **datatype** (int): Datatype of the VStack
           * **stack** (list): Vstack list with the following format: [(eps1, t1), (eps2, t2), (eps3, t3), ...] where eps1, eps2, .. are the permittivity (float), and t1, t2, .. are the thicknesses (float) from bottom to top. Note: if t1+t2+... must add up to vsize.

        """
        #First, typecheck the stack
        t = 0
        for s in stack:
            t += s[1]
        if abs(t-self.vsize) >= 1E-6:
            raise ValueError("Warning! Stack thicknesses ("+str(t)+") do not add up to vsize ("+str(self.vsize)+").")

        self.stacklist[(layer, datatype)] = stack

    def interpolate_points(self, key, num_points):
        layer_ranges = []
        curz = 0.0 # "Current z"
        for layer in self.stacklist[key]:
            layer_ranges.append([layer[0], curz, curz+layer[1]])
            curz = curz+layer[1]

        points = []
        for i in np.linspace(1E-8, self.vsize, num_points):
            for layer in layer_ranges:
                if i > layer[1] and i <= layer[2]:
                    points.append(layer[0])

        if len(points) is not num_points:
            raise ValueError("Point interpolation did not work.  Repeat points added.")

        return np.array(points)

    def get_eps(self, key, height):
        """ Returns the dielectric constant (epsilon) corresponding to the `height` and VStack specified by `key`, where the height range is zero centered (-vsize/2.0, +vsize/2.0).

        Args:
            * **key** (layer,datatype): Key value of the VStack being used
            * **height** (float): Vertical position of the desired epsilon value (must be between -vsize/2.0, vsize/2.0)

        """
        cur_vmax = -self.vsize/2.0
        for layer in self.stacklist[key]:
            cur_vmax += layer[1]
            if height <= cur_vmax:
                return layer[0]
        return self.stacklist[key][-1][0]

def point_inside_polygon(x,y,poly):
    n = len(poly)
    inside =False
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside

def convert_to_hdf5(filename, component, mstack, x_size, z_size, res):
    """ Outputs the scalar dielectric field corresponding to the desired component and MaterialStack.  Format is compatible for importing with MEEP/MPB via `epsilon_input_file`.

    **Note**: that the top-down view of the device is the 'X-Z' plane.  The 'Y' direction specifies the vertical height.

    Args:
       * **filename** (string): Filename to save (must end with '.h5')
       * **component** (gdspy.Cell): Cell object (component of the PICwriter library)
       * **mstack** (MaterialStack): MaterialStack object that maps the gds layers to a physical stack
       * **x_size** (float): Size of the output field (in the x-direction).  Centered at the middle of the device.
       * **z_size** (float): Size of the output field (in the z-direction).  Centered at the middle of the device.
       * **res** (float):

    """
    import time
    start = time.time()

    flatcell = component.flatten()
    polygon_dict = flatcell.get_polygons(by_spec=True)
    bb = flatcell.get_bounding_box()
    xmin, xmax, zmin, zmax = bb[0][0], bb[1][0], bb[0][1], bb[1][1]
    center = ((xmax+xmin)/2.0, (zmax+zmin)/2.0)
    numx, numy, numz = int(x_size*res+1), int(mstack.vsize*res+1), int(z_size*res+1),
    x_list = np.linspace(center[0]-x_size/2.0, center[0]+x_size/2.0, int(x_size*res+1))
    z_list = np.linspace(center[1]-z_size/2.0, center[1]+z_size/2.0, int(z_size*res+1))

    # Initialize matrix for HDF5 output
    f = h5py.File(filename,'w')
    eps_matrix = f.create_dataset("epsilon", (numx, numy, numz))

    default_stacklist_pts = mstack.interpolate_points((-1,-1), num_points=numy)

    x_indices, z_indices = range(numx), range(numz)
    for x in x_indices:
        for z in z_indices:
            eps_matrix[x,:,z] = default_stacklist_pts

    cur_progress, prev_progress = 0, 0
    for key in list(polygon_dict.keys()):
        # Check if the polygon layer/datatype is in the MaterialStack
        if key in list(mstack.stacklist.keys()):
            # This *found* layer should be specified in the epsilon-input file
            stacklist_pts =mstack.interpolate_points(key, num_points=numy)
            # Look through all the xy points for values inside the polygons, then add vertical stacklist to the file.
            # Note the run-time is O(x*y*stacks*polygons*points_per_polygon)
            for x in x_indices:
                cur_progress = 100*(x/numx)
                if cur_progress%10 < prev_progress%10:
                    print("Saving PICwriter component dielectric to hdf5... "+str(100*(x/numx))+"% done.")
                prev_progress=cur_progress
                for z in z_indices:
                    xval, zval = x_list[x], z_list[z]
                    for polygon in polygon_dict[key]:
                        if point_inside_polygon(xval,zval,polygon):
                            eps_matrix[x,:,z] = stacklist_pts

    f.close()
    print("Time to write file = "+str(time.time()-start)+" seconds")
    return None

def export_timestep_fields_to_png(directory):
    from subprocess import call
    filename = 'mcts'

    """ Export the epsilon slices to images """
    call("h5topng -S3 -m1 -M4 "+str(directory)+"/topview-"+str(filename)+"-eps-000000.00.h5", shell=True)
    call("h5topng -S3 -m1 -M4 "+str(directory)+"/sideview-"+str(filename)+"-eps-000000.00.h5", shell=True)

    """ Export the slice of data with epsilon overlayed """
    simulation_time = np.array(h5py.File(str(directory)+"/"+str(filename)+"-ez-topview.h5", 'r')['ez']).shape[2]
    simulation_time = simulation_time-1 #since time starts at t=0

    """ Convert h5 slices to png with dielectric overlayed """
    exec_str = "h5topng -t 0:"+str(simulation_time)+" -R -Zc dkbluered -a yarg -A "+str(directory)+"/topview-"+str(filename)+"-eps-000000.00.h5 "+str(directory)+"/"+str(filename)+"-ez-topview.h5"
    call(exec_str, shell=True)
    exec_str = "h5topng -t 0:"+str(simulation_time)+" -R -Zc dkbluered -a yarg -A "+str(directory)+"/sideview-"+str(filename)+"-eps-000000.00.h5 "+str(directory)+"/"+str(filename)+"-ez-sideview.h5"
    call(exec_str, shell=True)


def compute_transmission_spectra(pic_component, mstack, ports, port_vcenter, port_height, port_width, res, wl_center, wl_span,
                                 norm=False, wgt=None, nfreq=100, dpml=0.5, fields=False, source_offset=0.1, symmetry=None,
                                 convert_component_to_hdf5=True, skip_sim=False, output_directory='meep-sim', parallel=False, n_p=2):

    """ Launches a MEEP simulation to compute the transmission/reflection spectra from each of the component's ports when light enters at the input `port`.

    How this function maps the GDSII layers to the material stack is something that will be improved in the future.  Currently works well for 1 or 2 layer devices.
    **Currently only supports components with port-directions that are `EAST` (0) or `WEST` (pi)**

    Args:
       * **pic_component** (gdspy.Cell): Cell object (component of the PICwriter library)
       * **mstack** (MaterialStack): MaterialStack object that maps the gds layers to a physical stack
       * **ports** (list of `Port` dicts): These are the ports to track the Poynting flux through.  **IMPORTANT** The first element of this list is where the Eigenmode source will be input.
       * **port_vcenter** (float): Vertical center of the waveguide
       * **port_height** (float): Height of the port cross-section (flux plane)
       * **port_width** (float): Width of the port cross-section (flux plane)
       * **res** (int): Resolution of the MEEP simulation
       * **wl_center** (float): Center wavelength (in microns)
       * **wl_span** (float): Wavelength span (determines the pulse width)

    Keyword Args:
       * **norm** (boolean):  If True, first computes a normalization run (transmission through a straight waveguide defined by `wgt` above.  Defaults to `False`.  If `True`, a WaveguideTemplate must be specified.
       * **wgt** (WaveguideTemplate): Waveguide template, used for normalization run.  Defaults to None.
       * **nfreq** (int): Number of frequencies (wavelengths) to compute the spectrum over.  Defaults to 100.
       * **dpml** (float): Length (in microns) of the perfectly-matched layer (PML) at simulation boundaries.  Defaults to 0.5 um.
       * **fields** (boolean): If true, outputs the epsilon and cross-sectional fields.  Defaults to false.
       * **source_offset** (float): Offset (in x-direction) between reflection monitor and source.  Defaults to 0.1 um.
       * **convert_component_to_hdf5** (boolean): Defaults to True.  If True, converts the `pic_component` to an hdf5 file (warning, this may take some time!).  If `False` (since it was already computed in a previous run), will not output to hdf5.  **NOTE** this will output the structure with resolution 50% higher than the meep `res` specified above (to reduce discretization errors).
       * **skip_sim** (boolean): Defaults to False.  If True, skips the simulation (and hdf5 export).  Useful if you forgot to perform a normalization and don't want to redo the whole MEEP simulation.
       * **output_directory** (string): Output directory for files generated.  Defaults to 'meep-sim'.
       * **parallel** (boolean): If `True`, will run simulation on `np` cores (`np` must be specified below, and MEEP/MPB must be built from source with parallel-libraries).  Defaults to False.
       * **n_p** (int): Number of processors to run meep simulation on.  Defaults to `2`.

    """
    from subprocess import call
    import os
    import time

    """ For each port determine input_direction (useful for computing the sign of the power flux) """
    input_directions = []
    for port in ports:
        if isinstance(port["direction"], float):
            if abs(port["direction"])<1E-6:
                input_directions.append(-1)
            elif abs(port["direction"]-np.pi)<1E-6:
                input_directions.append(1)
            else:
                raise ValueError("Warning! An invalid float port direction ("+str(port["direction"])+") was provided.  Must be 0 or pi.")
        elif isinstance(port["direction"], unicode) or isinstance(port["direction"], str):
            if port["direction"]=='EAST':
                input_directions.append(-1)
            elif port["direction"]=='WEST':
                input_directions.append(1)
            else:
                raise ValueError("Warning! An invalid string port direction ("+str(port["direction"])+") was provided.  Must be `EAST` or `WEST`.")
        else:
            raise ValueError("Warning! A port was given in `ports` that is not a valid type!")

    if norm and wgt==None:
        raise ValueError("Warning! A normalization run was called, but no WaveguideTemplate (wgt) was provided.")

    """ If a normalization run is specified, create short waveguide component, then simulate
    """
    if norm:
        import picwriter.toolkit as tk
        import picwriter.components as pc
        norm_component = gdspy.Cell('norm_straightwg')
        wg1 = pc.Waveguide([(0,0), (1,0)], wgt)
        wg2 = pc.Waveguide([(1,0), (2,0)], wgt)
        wg3 = pc.Waveguide([(2,0), (3,0)], wgt)
        tk.add(norm_component, wg1)
        tk.add(norm_component, wg2)
        tk.add(norm_component, wg3)

        flatcell = norm_component.flatten()
        bb = flatcell.get_bounding_box()
        sx, sy, sz = bb[1][0]-bb[0][0], mstack.vsize, bb[1][1]-bb[0][1]
        center = ((bb[1][0]+bb[0][0])/2.0, 0, (bb[1][1]+bb[0][1])/2.0)

        norm_ports = [wg2.portlist["input"], wg2.portlist["output"]]

        eps_norm_input_file = str('epsilon-norm.h5')
        convert_to_hdf5(eps_norm_input_file, norm_component, mstack, sx, sz, 1.5*res)

        # Launch MEEP simulation using correct inputs
        port_string = ""
        for port in norm_ports:
            port_string += str(port["port"][0])+" "+str(port["port"][1])+" "
        port_string = str(port_string[:-1])

        if parallel:
            exec_str = ("mpirun -np %d"
                        " python mcts.py"
                        " -fields %r"
                        " -output_directory '%s/%s'"
                        " -eps_input_file '%s/%s'"
                        " -res %d"
                        " -nfreq %d"
                        " -input_direction %d"
                        " -dpml %0.3f"
                        " -wl_center %0.3f"
                        " -wl_span %0.3f"
                        " -port_vcenter %0.3f"
                        " -port_height %0.3f"
                        " -port_width %0.3f"
                        " -source_offset %0.3f"
                        " -center_x %0.3f"
                        " -center_y %0.3f"
                        " -center_z %0.3f"
                        " -sx %0.3f"
                        " -sy %0.3f"
                        " -sz %0.3f"
                        " -port_coords %r"
                        " > '%s/%s-norm-res%d.out'") % (int(n_p), False, str(os.getcwd()), str(output_directory), str(os.getcwd()),
                        eps_norm_input_file, res, nfreq, input_directions[0], float(dpml), float(wl_center),
                        float(wl_span), float(port_vcenter), float(port_height), float(port_width),
                        float(source_offset), float(center[0]), float(center[1]), float(center[2]),
                        float(sx), float(sy), float(sz), port_string, str(os.getcwd()), str(output_directory), res)
        else:
            exec_str = ("python mcts.py"
                        " -fields %r"
                        " -output_directory '%s/%s'"
                        " -eps_input_file '%s/%s'"
                        " -res %d"
                        " -nfreq %d"
                        " -input_direction %d"
                        " -dpml %0.3f"
                        " -wl_center %0.3f"
                        " -wl_span %0.3f"
                        " -port_vcenter %0.3f"
                        " -port_height %0.3f"
                        " -port_width %0.3f"
                        " -source_offset %0.3f"
                        " -center_x %0.3f"
                        " -center_y %0.3f"
                        " -center_z %0.3f"
                        " -sx %0.3f"
                        " -sy %0.3f"
                        " -sz %0.3f"
                        " -port_coords %r"
                        " > '%s/%s-norm-res%d.out'") % (False, str(os.getcwd()), str(output_directory), str(os.getcwd()),
                        eps_norm_input_file, res, nfreq, input_directions[0], float(dpml), float(wl_center),
                        float(wl_span), float(port_vcenter), float(port_height), float(port_width),
                        float(source_offset), float(center[0]), float(center[1]), float(center[2]),
                        float(sx), float(sy), float(sz), port_string, str(os.getcwd()), str(output_directory), res)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        print("Running MEEP normalization... (straight waveguide)")
        start = time.time()
        call(exec_str, shell=True, cwd=dir_path)
        print("Time to run MEEP normalization = "+str(time.time()-start)+" seconds")

        grep_str = "grep flux1: '%s/%s-norm-res%d.out' > '%s/%s-norm-res%d.dat'"%(str(os.getcwd()), str(output_directory), res,
                                                                                  str(os.getcwd()), str(output_directory), res)
        call(grep_str, shell="True")

    # Convert the structure to an hdf5 file
    flatcell = pic_component.flatten()
    bb = flatcell.get_bounding_box()
    sx, sy, sz = bb[1][0]-bb[0][0], mstack.vsize, bb[1][1]-bb[0][1]
    center = ((bb[1][0]+bb[0][0])/2.0, 0, (bb[1][1]+bb[0][1])/2.0)

    eps_input_file = str('epsilon-component.h5')
    if convert_component_to_hdf5 and skip_sim==False:
        convert_to_hdf5(eps_input_file, pic_component, mstack, sx, sz, 1.5*res)

    # Launch MEEP simulation using correct inputs
    port_string = ""
    for port in ports:
        port_string += str(port["port"][0])+" "+str(port["port"][1])+" "
    port_string = str(port_string[:-1])

    if parallel:
        exec_str = ("mpirun -np %d"
                    " python mcts.py"
                    " -fields %r"
                    " -output_directory '%s/%s'"
                    " -eps_input_file '%s/%s'"
                    " -res %d"
                    " -nfreq %d"
                    " -input_direction %d"
                    " -dpml %0.3f"
                    " -wl_center %0.3f"
                    " -wl_span %0.3f"
                    " -port_vcenter %0.3f"
                    " -port_height %0.3f"
                    " -port_width %0.3f"
                    " -source_offset %0.3f"
                    " -center_x %0.3f"
                    " -center_y %0.3f"
                    " -center_z %0.3f"
                    " -sx %0.3f"
                    " -sy %0.3f"
                    " -sz %0.3f"
                    " -port_coords %r"
                    " > '%s/%s-res%d.out'") % (int(n_p), fields, str(os.getcwd()), str(output_directory), str(os.getcwd()),
                    eps_input_file, res, nfreq, input_directions[0], float(dpml), float(wl_center),
                    float(wl_span), float(port_vcenter), float(port_height), float(port_width),
                    float(source_offset), float(center[0]), float(center[1]), float(center[2]),
                    float(sx), float(sy), float(sz), port_string, str(os.getcwd()), str(output_directory), res)
    else:
        exec_str = ("python mcts.py"
                    " -fields %r"
                    " -output_directory '%s/%s'"
                    " -eps_input_file '%s/%s'"
                    " -res %d"
                    " -nfreq %d"
                    " -input_direction %d"
                    " -dpml %0.3f"
                    " -wl_center %0.3f"
                    " -wl_span %0.3f"
                    " -port_vcenter %0.3f"
                    " -port_height %0.3f"
                    " -port_width %0.3f"
                    " -source_offset %0.3f"
                    " -center_x %0.3f"
                    " -center_y %0.3f"
                    " -center_z %0.3f"
                    " -sx %0.3f"
                    " -sy %0.3f"
                    " -sz %0.3f"
                    " -port_coords %r"
                    " > '%s/%s-res%d.out'") % (fields, str(os.getcwd()), str(output_directory), str(os.getcwd()),
                    eps_input_file, res, nfreq, input_directions[0], float(dpml), float(wl_center),
                    float(wl_span), float(port_vcenter), float(port_height), float(port_width),
                    float(source_offset), float(center[0]), float(center[1]), float(center[2]),
                    float(sx), float(sy), float(sz), port_string, str(os.getcwd()), str(output_directory), res)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    if skip_sim==False:
        print("Running MEEP simulation... (check .out file for current status)")
        start = time.time()
        call(exec_str, shell=True, cwd=dir_path)
        print("Time to run MEEP simulation = "+str(time.time()-start)+" seconds")

    grep_str = "grep flux1: '%s/%s-res%d.out' > '%s/%s-res%d.dat'"%(str(os.getcwd()), str(output_directory), res,
                                                                    str(os.getcwd()), str(output_directory), res)
    call(grep_str, shell="True")

    """ Grab data and plot transmission/reflection spectra
    """
    norm_data = np.genfromtxt("%s/%s-norm-res%d.dat"%(str(os.getcwd()), str(output_directory), res), delimiter=",")
    freq, refl0, trans0 = norm_data[:,1], -norm_data[:,2], norm_data[:,3]# refl0 = -norm_data[:,2]
    comp_data = np.genfromtxt("%s/%s-res%d.dat"%(str(os.getcwd()), str(output_directory), res), delimiter=",")

    flux_data = []
    for i in range(len(ports)): #Get the power flux-data from the component simulation for each flux-plane
        flux_data.append((-1)*input_directions[i]*comp_data[:,i+2])

    wavelength = [1.0/f for f in freq]
    from matplotlib import pyplot as plt

    # Plot a spectrum corresponding to each port (sign is calculated from the port "direction")
    colorlist = ['r-', 'b-', 'g-', 'c-', 'm-', 'y-']
    plt.plot(wavelength, (flux_data[0]-refl0)/trans0, colorlist[0], label='port 0')
    for i in range(len(flux_data)-1):
        plt.plot(wavelength, flux_data[i+1]/trans0, colorlist[(i+1)%len(colorlist)], label='port '+str(i+1))

    plt.xlabel("Wavelength [um]")
    plt.ylabel("Transmission")
    plt.xlim([min(wavelength),max(wavelength)])
    plt.legend(loc='best')
    plt.savefig("%s/%s-res%d.png"%(str(os.getcwd()), str(output_directory), res))
    plt.close()

    if fields:
        print("Outputting fields images to "+str(output_directory))
        export_timestep_fields_to_png(str(output_directory))

    return None


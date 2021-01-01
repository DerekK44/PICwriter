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
    """Standard template for generating a material stack

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
        """Adds a vertical layer to the material stack LIST

        Args:
           * **layer** (int): Layer of the VStack
           * **datatype** (int): Datatype of the VStack
           * **stack** (list): Vstack list with the following format: [(eps1, t1), (eps2, t2), (eps3, t3), ...] where eps1, eps2, .. are the permittivity (float), and t1, t2, .. are the thicknesses (float) from bottom to top. Note: if t1+t2+... must add up to vsize.

        """
        # First, typecheck the stack
        t = 0
        for s in stack:
            t += s[1]
        if abs(t - self.vsize) >= 1e-6:
            raise ValueError(
                "Warning! Stack thicknesses ("
                + str(t)
                + ") do not add up to vsize ("
                + str(self.vsize)
                + ")."
            )

        self.stacklist[(layer, datatype)] = stack

    def interpolate_points(self, key, num_points):
        layer_ranges = []
        curz = 0.0  # "Current z"
        for layer in self.stacklist[key]:
            layer_ranges.append([layer[0], curz, curz + layer[1]])
            curz = curz + layer[1]

        points = []
        for i in np.linspace(1e-8, self.vsize, num_points):
            for layer in layer_ranges:
                if i > layer[1] and i <= layer[2]:
                    points.append(layer[0])

        if len(points) is not num_points:
            raise ValueError("Point interpolation did not work.  Repeat points added.")

        return np.array(points)

    def get_eps(self, key, height):
        """Returns the dielectric constant (epsilon) corresponding to the `height` and VStack specified by `key`, where the height range is zero centered (-vsize/2.0, +vsize/2.0).

        Args:
            * **key** (layer,datatype): Key value of the VStack being used
            * **height** (float): Vertical position of the desired epsilon value (must be between -vsize/2.0, vsize/2.0)

        """
        cur_vmax = -self.vsize / 2.0
        for layer in self.stacklist[key]:
            cur_vmax += layer[1]
            if height <= cur_vmax:
                return layer[0]
        return self.stacklist[key][-1][0]


def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def export_component_to_hdf5(filename, component, mstack, boolean_operations):
    """Outputs the polygons corresponding to the desired component and MaterialStack.
    Format is compatible for generating prism geometries in MEEP/MPB.

    **Note**: that the top-down view of the device is the 'X-Z' plane.  The 'Y' direction specifies the vertical height.

    Args:
       * **filename** (string): Filename to save (must end with '.h5')
       * **component** (gdspy.Cell): Cell object (component of the PICwriter library)
       * **mstack** (MaterialStack): MaterialStack object that maps the gds layers to a physical stack
       * **boolean_operations** (list): A list of specified boolean operations to be performed on the layers (order matters, see below).

    The boolean_operations argument must be specified in the following format::

       boolean_opeartions = [((layer1/datatype1), (layer2/datatype2), operation), ...]

    where 'operation' can be 'xor', 'or', 'and', or 'not' and the resulting polygons are placed on (layer1, datatype1). For example, the boolean_operation below::

       boolean_operations = [((-1,-1), (2,0), 'and'), ((2,0), (1,0), 'xor')]

    will:

       (1) do an 'xor' of the default layerset (-1,-1) with the cladding (2,0) and then make this the new default
       (2) do an 'xor' of the cladding (2,0) and waveguide (1,0) and make this the new cladding

    Write format:
       * LL = layer
       * DD = datatype
       * NN = polygon index
       * VV = vertex index
       * XX = x-position
       * ZZ = z-position
       * height = height of the prism
       * eps = epsilon of the prism
       * y-center = center (y-direction) of the prism [note: (x,y) center defaults to (0,0)]

    """

    flatcell = component.flatten()
    polygon_dict = flatcell.get_polygons(by_spec=True)

    bb = flatcell.get_bounding_box()
    sx, sy, sz = bb[1][0] - bb[0][0], mstack.vsize, bb[1][1] - bb[0][1]
    center_x, center_y, center_z = (
        (bb[1][0] + bb[0][0]) / 2.0,
        0.0,
        (bb[1][1] + bb[0][1]) / 2.0,
    )

    ll_list, dd_list, nn_list, vv_list, xx_list, zz_list = [], [], [], [], [], []
    height_list, eps_list, ycenter_list = [], [], []

    """ Add the default layer set """
    polygon_dict[(-1, -1)] = [
        np.array(
            [
                [bb[0][0], bb[0][1]],
                [bb[1][0], bb[0][1]],
                [bb[1][0], bb[1][1]],
                [bb[0][0], bb[1][1]],
            ]
        )
    ]

    #    print("boolean operations: ")
    #    print(boolean_operations)
    #
    #    print('key (default): (-1,-1)')
    #    print(polygon_dict[(-1,-1)])

    for key in polygon_dict.keys():
        """Merge the polygons
        This prevents weird edge effects in MEEP with subpixel averaging between adjacent objects
        """
        polygons = polygon_dict[key]
        polygons_union = gdspy.fast_boolean(
            polygons, polygons, "or", max_points=99999, layer=key[0], datatype=key[1]
        )
        polygon_dict[key] = polygons_union.polygons

    for bo in boolean_operations:
        polygons_bool = gdspy.fast_boolean(
            polygon_dict[bo[0]],
            polygon_dict[bo[1]],
            bo[2],
            layer=bo[0][0],
            datatype=bo[0][1],
        )
        if polygons_bool == None:
            del polygon_dict[bo[0]]
        else:
            polygon_dict[bo[0]] = polygons_bool.polygons

    #    for key in polygon_dict.keys():
    #        print('key: '+str(key))
    #        print(polygon_dict[key])

    for key in polygon_dict.keys():
        ll, dd, = (
            key[0],
            key[1],
        )
        if key in list(mstack.stacklist.keys()):
            stacklist = np.array(mstack.stacklist[key])

            # Put together a list of the centers of each layer
            zlength = sum(stacklist[:, 1])
            z0 = -zlength / 2.0
            centers = [z0 + stacklist[0][1] / 2.0]
            for i in range(len(stacklist) - 1):
                prev_value = centers[-1]
                centers.append(
                    prev_value + stacklist[i][1] / 2.0 + stacklist[i + 1][1] / 2.0
                )

            for i in range(len(stacklist)):
                for nn in range(len(polygon_dict[key])):
                    #                    print("Polygon: ")
                    #                    print("layer=("+str(ll)+"/"+str(dd)+"), height="+str(stacklist[i][1])+" eps="+str(stacklist[i][0])+" ycent="+str(centers[i]))
                    for vv in range(len(polygon_dict[key][nn])):
                        xx, zz = polygon_dict[key][nn][vv]
                        ll_list.append(ll)
                        dd_list.append(dd)
                        nn_list.append(nn)
                        vv_list.append(vv)
                        xx_list.append(xx - center_x)
                        zz_list.append(zz - center_z)
                        height_list.append(stacklist[i][1])
                        eps_list.append(stacklist[i][0])
                        ycenter_list.append(centers[i])

    with h5py.File(filename, "w") as hf:
        hf.create_dataset("LL", data=np.array(ll_list))
        hf.create_dataset("DD", data=np.array(dd_list))
        hf.create_dataset("NN", data=np.array(nn_list))
        hf.create_dataset("VV", data=np.array(vv_list))
        hf.create_dataset("XX", data=np.array(xx_list))
        hf.create_dataset("ZZ", data=np.array(zz_list))
        hf.create_dataset("height", data=np.array(height_list))
        hf.create_dataset("eps", data=np.array(eps_list))
        hf.create_dataset("ycenter", data=np.array(ycenter_list))


def export_wgt_to_hdf5(filename, wgt, mstack, sx):
    """Outputs the polygons corresponding to the desired waveguide template and MaterialStack.
    Format is compatible for generating prism geometries in MEEP/MPB.

    **Note**: that the top-down view of the device is the 'X-Z' plane.  The 'Y' direction specifies the vertical height.

    Args:
       * **filename** (string): Filename to save (must end with '.h5')
       * **wgt** (WaveguideTemplate): WaveguideTemplate object from the PICwriter library
       * **mstack** (MaterialStack): MaterialStack object that maps the gds layers to a physical stack
       * **sx** (float): Size of the simulation region in the x-direction

    Write-format for all blocks:
       * CX = center-x
       * CY = center-y
       * width = width (x-direction) of block
       * height = height (y-direction) of block
       * eps = dielectric constant

    """
    CX, CY, width_list, height_list, eps_list = [], [], [], [], []
    if wgt.wg_type == "strip":
        """
        check wg (layer/datatype) and clad (layer/datatype)
        check if these are in the mstack.  If so, create the blocks that would correspond to each
        save all 'block' info to hdf5 file (center, x-size, y-size, epsilon)
        still need to add support for full material functions (i.e. built-in silicon, SiN, etc...)
        """
        for key in mstack.stacklist.keys():
            if key == (wgt.wg_layer, wgt.wg_datatype):
                width = wgt.wg_width
                center_x = 0.0
                total_y = sum([layer[1] for layer in mstack.stacklist[key]])
                cur_y = -total_y / 2.0
                for layer in mstack.stacklist[key]:
                    center_y = cur_y + layer[1] / 2.0
                    cur_y = cur_y + layer[1]
                    CX.append(center_x)
                    CY.append(center_y)
                    width_list.append(width)
                    height_list.append(layer[1])
                    eps_list.append(layer[0])
            if key == (wgt.clad_layer, wgt.clad_datatype):
                width = wgt.clad_width
                center_x = (wgt.wg_width + wgt.clad_width) / 2.0
                total_y = sum([layer[1] for layer in mstack.stacklist[key]])
                cur_y = -total_y / 2.0
                for layer in mstack.stacklist[key]:
                    center_y = cur_y + layer[1] / 2.0
                    cur_y = cur_y + layer[1]
                    # Add cladding on +x side
                    CX.append(center_x)
                    CY.append(center_y)
                    width_list.append(width)
                    height_list.append(layer[1])
                    eps_list.append(layer[0])
                    # Add cladding on -x side
                    CX.append(-center_x)
                    CY.append(center_y)
                    width_list.append(width)
                    height_list.append(layer[1])
                    eps_list.append(layer[0])

    elif wgt.wg_type == "slot":
        """Same thing as above but for slot waveguides"""
        slot = wgt.slot
        for key in mstack.stacklist.keys():
            if key == (wgt.wg_layer, wgt.wg_datatype):
                """ Add waveguide blocks """
                rail_width = (wgt.wg_width - slot) / 2.0
                center_x = (slot + rail_width) / 2.0
                total_y = sum([layer[1] for layer in mstack.stacklist[key]])
                cur_y = -total_y / 2.0
                for layer in mstack.stacklist[key]:
                    center_y = cur_y + layer[1] / 2.0
                    cur_y = cur_y + layer[1]
                    # Add left waveguide component
                    CX.append(center_x)
                    CY.append(center_y)
                    width_list.append(rail_width)
                    height_list.append(layer[1])
                    eps_list.append(layer[0])
                    # Add right waveguide component
                    CX.append(-center_x)
                    CY.append(center_y)
                    width_list.append(rail_width)
                    height_list.append(layer[1])
                    eps_list.append(layer[0])
            if key == (wgt.clad_layer, wgt.clad_datatype):
                """ Add cladding blocks """
                width = wgt.clad_width
                center_x = (wgt.wg_width + wgt.clad_width) / 2.0
                total_y = sum([layer[1] for layer in mstack.stacklist[key]])
                cur_y = -total_y / 2.0
                for layer in mstack.stacklist[key]:
                    center_y = cur_y + layer[1] / 2.0
                    cur_y = cur_y + layer[1]
                    # Add cladding on +x side
                    CX.append(center_x)
                    CY.append(center_y)
                    width_list.append(width)
                    height_list.append(layer[1])
                    eps_list.append(layer[0])
                    # Add cladding on -x side
                    CX.append(-center_x)
                    CY.append(center_y)
                    width_list.append(width)
                    height_list.append(layer[1])
                    eps_list.append(layer[0])
                    # Add slot region
                    CX.append(0.0)
                    CY.append(center_y)
                    width_list.append(slot)
                    height_list.append(layer[1])
                    eps_list.append(layer[0])

    if (wgt.wg_width + 2 * wgt.clad_width) < sx:
        """ If True, need to add additional region next to cladding (default material) """
        default_key = (-1, -1)
        center_x = sx / 2.0
        width = sx - (wgt.wg_width + 2 * wgt.clad_width)
        total_y = sum([layer[1] for layer in mstack.stacklist[default_key]])
        cur_y = -total_y / 2.0
        for layer in mstack.stacklist[default_key]:
            center_y = cur_y + layer[1] / 2.0
            cur_y = cur_y + layer[1]
            # Add default material blocks on +x side
            CX.append(center_x)
            CY.append(center_y)
            width_list.append(width)
            height_list.append(layer[1])
            eps_list.append(layer[0])
            # Add default material blocks on -x side
            CX.append(-center_x)
            CY.append(center_y)
            width_list.append(width)
            height_list.append(layer[1])
            eps_list.append(layer[0])

    with h5py.File(filename, "w") as hf:
        hf.create_dataset("CX", data=np.array(CX))
        hf.create_dataset("CY", data=np.array(CY))
        hf.create_dataset("width_list", data=np.array(width_list))
        hf.create_dataset("height_list", data=np.array(height_list))
        hf.create_dataset("eps_list", data=np.array(eps_list))


def export_timestep_fields_to_png(directory):
    from subprocess import call

    filename = "mcts"

    """ Export the epsilon slices to images """
    call(
        "h5topng -S3 -m1 -M4 "
        + str(directory)
        + "/topview-"
        + str(filename)
        + "-eps-000000.00.h5",
        shell=True,
    )
    call(
        "h5topng -S3 -m1 -M4 "
        + str(directory)
        + "/sideview-"
        + str(filename)
        + "-eps-000000.00.h5",
        shell=True,
    )

    """ Export the slice of data with epsilon overlayed """
    simulation_time = np.array(
        h5py.File(str(directory) + "/" + str(filename) + "-ez-topview.h5", "r")["ez"]
    ).shape[2]
    simulation_time = simulation_time - 1  # since time starts at t=0

    """ Convert h5 slices to png with dielectric overlayed """
    exec_str = (
        "h5topng -t 0:"
        + str(simulation_time)
        + " -R -Zc dkbluered -a yarg -A "
        + str(directory)
        + "/topview-"
        + str(filename)
        + "-eps-000000.00.h5 "
        + str(directory)
        + "/"
        + str(filename)
        + "-ez-topview.h5"
    )
    call(exec_str, shell=True)
    exec_str = (
        "h5topng -t 0:"
        + str(simulation_time)
        + " -R -Zc dkbluered -a yarg -A "
        + str(directory)
        + "/sideview-"
        + str(filename)
        + "-eps-000000.00.h5 "
        + str(directory)
        + "/"
        + str(filename)
        + "-ez-sideview.h5"
    )
    call(exec_str, shell=True)


def compute_mode(
    wgt,
    mstack,
    res,
    wavelength,
    sx,
    sy,
    plot_mode_number=1,
    polarization="TE",
    output_directory="mpb-sim",
    save_mode_data=True,
    suppress_window=False,
):

    """Launches a MPB simulation to quickly compute and visualize a waveguide's electromagnetic eigenmodes

    Args:
       * **wgt** (WaveguideTemplate): WaveguideTemplate object used to specify the waveguide geometry (mask-level)
       * **mstack** (MaterialStack): MaterialStack object that maps the gds layers to a physical stack
       * **res** (int): Resolution of the MPB simulation (number of pixels per micron).
       * **wavelength** (float): Wavelength in microns.
       * **sx** (float): Size of the simulation region in the x-direction.
       * **sy** (float): Size of the simulation region in the y-direction.
       * **plot_mode_number** (int): Which mode to plot (only plots one mode at a time).  Must be a number equal to or less than num_modes.  Defaults to 1.
       * **polarization** (string): Mode polarization.  Must be either "TE", "TM", or "None" (corresponding to MPB parities of ODD-X, EVEN-X, or NO-PARITY).
       * **output_directory** (string): Output directory for files generated.  Defaults to 'mpb-sim'.
       * **save_mode_data** (Boolean): Save the mode image and data to a separate file.  Defaults to True.
       * **suppress_window** (Boolean): Suppress the matplotlib window.  Defaults to false.

    Returns:
       List of values for the modes: [[:math:`n_{eff,1}, n_{g,1}`], [:math:`n_{eff,2}, n_{g,2}`], ...]

    """
    from subprocess import call
    import os
    import time

    eps_input_file = str("epsilon.h5")
    export_wgt_to_hdf5(eps_input_file, wgt, mstack, sx)

    exec_str = (
        "python mcm.py"
        " -res %d"
        " -wavelength %0.3f"
        " -sx %0.3f"
        " -sy %0.3f"
        " -plot_mode_number %d"
        " -polarization %s"
        " -epsilon_file '%s/%s'"
        " -output_directory '%s/%s'"
        " -save_mode_data %r"
        " -suppress_window %r"
        " > '%s/%s-res%d.out'"
    ) % (
        res,
        wavelength,
        sx,
        sy,
        plot_mode_number,
        polarization,
        str(os.getcwd()),
        str(eps_input_file),
        str(os.getcwd()),
        str(output_directory),
        save_mode_data,
        suppress_window,
        str(os.getcwd()),
        str(output_directory),
        res,
    )

    dir_path = os.path.dirname(os.path.realpath(__file__))
    print("dir_path = " + str(dir_path))

    print("Running MPB simulation... (check .out file for current status)")
    start = time.time()
    call(exec_str, shell=True, cwd=dir_path)
    print("Time to run MPB simulation = " + str(time.time() - start) + " seconds")
    return None


def compute_transmission_spectra(
    pic_component,
    mstack,
    wgt,
    ports,
    port_vcenter,
    port_height,
    port_width,
    res,
    wl_center,
    wl_span,
    boolean_operations=None,
    norm=False,
    input_pol="TE",
    nfreq=100,
    dpml=0.5,
    fields=False,
    plot_window=False,
    source_offset=0.1,
    symmetry=None,
    skip_sim=False,
    output_directory="meep-sim",
    parallel=False,
    n_p=2,
):

    """Launches a MEEP simulation to compute the transmission/reflection spectra from each of the component's ports when light enters at the input `port`.

    How this function maps the GDSII layers to the material stack is something that will be improved in the future.  Currently works well for 1 or 2 layer devices.
    **Currently only supports components with port-directions that are `EAST` (0) or `WEST` (pi)**

    Args:
       * **pic_component** (gdspy.Cell): Cell object (component of the PICwriter library)
       * **mstack** (MaterialStack): MaterialStack object that maps the gds layers to a physical stack
       * **wgt** (WaveguideTemplate): Waveguide template
       * **ports** (list of `Port` dicts): These are the ports to track the Poynting flux through.  **IMPORTANT** The first element of this list is where the Eigenmode source will be input.
       * **port_vcenter** (float): Vertical center of the waveguide
       * **port_height** (float): Height of the port cross-section (flux plane)
       * **port_width** (float): Width of the port cross-section (flux plane)
       * **res** (int): Resolution of the MEEP simulation
       * **wl_center** (float): Center wavelength (in microns)
       * **wl_span** (float): Wavelength span (determines the pulse width)

    Keyword Args:
       * **boolean_operations** (list): A list of specified boolean operations to be performed on the layers (ORDER MATTERS).  In the following format:
           [((layer1/datatype1), (layer2/datatype2), operation), ...] where 'operation' can be 'xor', 'or', 'and', or 'not' and the resulting polygons are placed on (layer1, datatype1).  See below for example.
       * **norm** (boolean):  If True, first computes a normalization run (transmission through a straight waveguide defined by `wgt` above.  Defaults to `False`.  If `True`, a WaveguideTemplate must be specified.
       * **input_pol** (String): Input polarization of the waveguide mode.  Must be either "TE" or "TM".  Defaults to "TE" (z-antisymmetric).
       * **nfreq** (int): Number of frequencies (wavelengths) to compute the spectrum over.  Defaults to 100.
       * **dpml** (float): Length (in microns) of the perfectly-matched layer (PML) at simulation boundaries.  Defaults to 0.5 um.
       * **fields** (boolean): If true, outputs the epsilon and cross-sectional fields.  Defaults to false.
       * **plot_window** (boolean): If true, outputs the spectrum plot in a matplotlib window (in addition to saving).  Defaults to False.
       * **source_offset** (float): Offset (in x-direction) between reflection monitor and source.  Defaults to 0.1 um.
       * **skip_sim** (boolean): Defaults to False.  If True, skips the simulation (and hdf5 export).  Useful if you forgot to perform a normalization and don't want to redo the whole MEEP simulation.
       * **output_directory** (string): Output directory for files generated.  Defaults to 'meep-sim'.
       * **parallel** (boolean): If `True`, will run simulation on `np` cores (`np` must be specified below, and MEEP/MPB must be built from source with parallel-libraries).  Defaults to False.
       * **n_p** (int): Number of processors to run meep simulation on.  Defaults to `2`.


    Example of **boolean_operations** (using the default):
           The following default boolean_operation will:
               (1) do an 'xor' of the default layerset (-1,-1) with a cladding (2,0) and then make this the new default layerset
               (2) do an 'xor' of the cladding (2,0) and waveguide (1,0) and make this the new cladding

            boolean_operations = [((-1,-1), (2,0), 'and'), ((2,0), (1,0), 'xor')]

    """
    from subprocess import call
    import os
    import time

    if boolean_operations == None:
        boolean_operations = [
            ((-1, -1), (wgt.clad_layer, wgt.clad_datatype), "xor"),
            (
                (wgt.clad_layer, wgt.clad_datatype),
                (wgt.wg_layer, wgt.wg_datatype),
                "xor",
            ),
        ]

    """ For each port determine input_direction (useful for computing the sign of the power flux) """
    input_directions = []
    for port in ports:
        if isinstance(port["direction"], float):
            if abs(port["direction"]) < 1e-6:
                input_directions.append(-1)
            elif abs(port["direction"] - np.pi) < 1e-6:
                input_directions.append(1)
            else:
                raise ValueError(
                    "Warning! An invalid float port direction ("
                    + str(port["direction"])
                    + ") was provided.  Must be 0 or pi."
                )
        elif isinstance(port["direction"], (str, bytes)):
            if port["direction"] == "EAST":
                input_directions.append(-1)
            elif port["direction"] == "WEST":
                input_directions.append(1)
            else:
                raise ValueError(
                    "Warning! An invalid string port direction ("
                    + str(port["direction"])
                    + ") was provided.  Must be `EAST` or `WEST`."
                )
        else:
            raise ValueError(
                "Warning! A port was given in `ports` that is not a valid type!"
            )

    if norm and wgt == None:
        raise ValueError(
            "Warning! A normalization run was called, but no WaveguideTemplate (wgt) was provided."
        )

    """ If a normalization run is specified, create short waveguide component, then simulate
    """
    if norm:
        import picwriter.toolkit as tk
        import picwriter.components as pc

        norm_component = gdspy.Cell(tk.getCellName("norm_straightwg"))
        wg1 = pc.Waveguide([(0, 0), (1, 0)], wgt)
        wg2 = pc.Waveguide([(1, 0), (2, 0)], wgt)
        wg3 = pc.Waveguide([(2, 0), (3, 0)], wgt)
        tk.add(norm_component, wg1)
        tk.add(norm_component, wg2)
        tk.add(norm_component, wg3)

        flatcell = norm_component.flatten()
        bb = flatcell.get_bounding_box()
        sx, sy, sz = bb[1][0] - bb[0][0], mstack.vsize, bb[1][1] - bb[0][1]
        center = ((bb[1][0] + bb[0][0]) / 2.0, 0, (bb[1][1] + bb[0][1]) / 2.0)

        norm_ports = [wg2.portlist["input"], wg2.portlist["output"]]

        eps_norm_input_file = str("epsilon-norm.h5")
        export_component_to_hdf5(
            eps_norm_input_file, norm_component, mstack, boolean_operations
        )
        #        convert_to_hdf5(eps_norm_input_file, norm_component, mstack, sx, sz, 1.5*res)

        # Launch MEEP simulation using correct inputs
        port_string = ""
        for port in norm_ports:
            port_string += str(port["port"][0]) + " " + str(port["port"][1]) + " "
        port_string = str(port_string[:-1])

        if parallel:
            exec_str = (
                "mpirun -np %d"
                " python mcts.py"
                " -fields %r"
                " -input_pol %s"
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
                " > '%s/%s-norm-res%d.out'"
            ) % (
                int(n_p),
                False,
                input_pol,
                str(os.getcwd()),
                str(output_directory),
                str(os.getcwd()),
                eps_norm_input_file,
                res,
                nfreq,
                input_directions[0],
                float(dpml),
                float(wl_center),
                float(wl_span),
                float(port_vcenter),
                float(port_height),
                float(port_width),
                float(source_offset),
                float(center[0]),
                float(center[1]),
                float(center[2]),
                float(sx),
                float(sy),
                float(sz),
                port_string,
                str(os.getcwd()),
                str(output_directory),
                res,
            )
        else:
            exec_str = (
                "python mcts.py"
                " -fields %r"
                " -input_pol %s"
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
                " > '%s/%s-norm-res%d.out'"
            ) % (
                False,
                input_pol,
                str(os.getcwd()),
                str(output_directory),
                str(os.getcwd()),
                eps_norm_input_file,
                res,
                nfreq,
                input_directions[0],
                float(dpml),
                float(wl_center),
                float(wl_span),
                float(port_vcenter),
                float(port_height),
                float(port_width),
                float(source_offset),
                float(center[0]),
                float(center[1]),
                float(center[2]),
                float(sx),
                float(sy),
                float(sz),
                port_string,
                str(os.getcwd()),
                str(output_directory),
                res,
            )
        dir_path = os.path.dirname(os.path.realpath(__file__))
        print("Running MEEP normalization... (straight waveguide)")
        start = time.time()
        call(exec_str, shell=True, cwd=dir_path)
        print(
            "Time to run MEEP normalization = " + str(time.time() - start) + " seconds"
        )

        grep_str = "grep flux1: '%s/%s-norm-res%d.out' > '%s/%s-norm-res%d.dat'" % (
            str(os.getcwd()),
            str(output_directory),
            res,
            str(os.getcwd()),
            str(output_directory),
            res,
        )
        call(grep_str, shell="True")

    # Get size, center of simulation window
    flatcell = pic_component.flatten()
    bb = flatcell.get_bounding_box()
    sx, sy, sz = bb[1][0] - bb[0][0], mstack.vsize, bb[1][1] - bb[0][1]
    center = ((bb[1][0] + bb[0][0]) / 2.0, 0, (bb[1][1] + bb[0][1]) / 2.0)

    # Convert the structure to an hdf5 file
    eps_input_file = str("epsilon-component.h5")
    export_component_to_hdf5(eps_input_file, pic_component, mstack, boolean_operations)

    # Launch MEEP simulation using correct inputs
    port_string = ""
    for port in ports:
        port_string += str(port["port"][0]) + " " + str(port["port"][1]) + " "
    port_string = str(port_string[:-1])

    if parallel:
        exec_str = (
            "mpirun -np %d"
            " python mcts.py"
            " -fields %r"
            " -input_pol %s"
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
            " > '%s/%s-res%d.out'"
        ) % (
            int(n_p),
            fields,
            input_pol,
            str(os.getcwd()),
            str(output_directory),
            str(os.getcwd()),
            eps_input_file,
            res,
            nfreq,
            input_directions[0],
            float(dpml),
            float(wl_center),
            float(wl_span),
            float(port_vcenter),
            float(port_height),
            float(port_width),
            float(source_offset),
            float(center[0]),
            float(center[1]),
            float(center[2]),
            float(sx),
            float(sy),
            float(sz),
            port_string,
            str(os.getcwd()),
            str(output_directory),
            res,
        )
    else:
        exec_str = (
            "python mcts.py"
            " -fields %r"
            " -input_pol %s"
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
            " > '%s/%s-res%d.out'"
        ) % (
            fields,
            input_pol,
            str(os.getcwd()),
            str(output_directory),
            str(os.getcwd()),
            eps_input_file,
            res,
            nfreq,
            input_directions[0],
            float(dpml),
            float(wl_center),
            float(wl_span),
            float(port_vcenter),
            float(port_height),
            float(port_width),
            float(source_offset),
            float(center[0]),
            float(center[1]),
            float(center[2]),
            float(sx),
            float(sy),
            float(sz),
            port_string,
            str(os.getcwd()),
            str(output_directory),
            res,
        )

    dir_path = os.path.dirname(os.path.realpath(__file__))
    if skip_sim == False:
        print("Running MEEP simulation... (check .out file for current status)")
        start = time.time()
        call(exec_str, shell=True, cwd=dir_path)
        print("Time to run MEEP simulation = " + str(time.time() - start) + " seconds")

    grep_str = "grep flux1: '%s/%s-res%d.out' > '%s/%s-res%d.dat'" % (
        str(os.getcwd()),
        str(output_directory),
        res,
        str(os.getcwd()),
        str(output_directory),
        res,
    )
    call(grep_str, shell="True")

    """ Grab data and plot transmission/reflection spectra
    """
    norm_data = np.genfromtxt(
        "%s/%s-norm-res%d.dat" % (str(os.getcwd()), str(output_directory), res),
        delimiter=",",
    )
    freq, refl0, trans0 = (
        norm_data[:, 1],
        -norm_data[:, 2],
        norm_data[:, 3],
    )  # refl0 = -norm_data[:,2]
    comp_data = np.genfromtxt(
        "%s/%s-res%d.dat" % (str(os.getcwd()), str(output_directory), res),
        delimiter=",",
    )

    flux_data = []
    for i in range(
        len(ports)
    ):  # Get the power flux-data from the component simulation for each flux-plane
        flux_data.append((-1) * input_directions[i] * comp_data[:, i + 2])

    wavelength = [1.0 / f for f in freq]
    from matplotlib import pyplot as plt

    # Plot a spectrum corresponding to each port (sign is calculated from the port "direction")
    colorlist = ["r-", "b-", "g-", "c-", "m-", "y-"]
    plt.plot(wavelength, (flux_data[0] - refl0) / trans0, colorlist[0], label="port 0")
    for i in range(len(flux_data) - 1):
        plt.plot(
            wavelength,
            flux_data[i + 1] / trans0,
            colorlist[(i + 1) % len(colorlist)],
            label="port " + str(i + 1),
        )

    plt.xlabel("Wavelength [um]")
    plt.ylabel("Transmission")
    plt.xlim([min(wavelength), max(wavelength)])
    plt.legend(loc="best")
    plt.savefig("%s/%s-res%d.png" % (str(os.getcwd()), str(output_directory), res))
    if plot_window:
        plt.show()
    plt.close()

    if fields:
        print("Outputting fields images to " + str(output_directory))
        export_timestep_fields_to_png(str(output_directory))

    return None

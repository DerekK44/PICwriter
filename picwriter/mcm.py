#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Default MPB launch-file for computing electromagnetic modes of arbitrary PICwriter waveguides.

MCM = "MPB Compute Mode"

Launches a MPB simulation to compute the electromagnetic mode profile for a given waveguide template and
material stack.

@author: dkita
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import meep as mp
from meep import mpb
import h5py
import argparse
import matplotlib.pyplot as plt
import os

def str2bool(v):
    """ Allow proper argparse handling of boolean inputs """
    if v.lower() in ('yes', 'true', 'True', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'False', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main(args):
    """
    Args:
       * **res** (int): Resolution of the simulation [pixels/um] (default=10)
       * **wavelength** (float): Wavelength in microns (default=1.55)
       * **sx** (float): Size of the simulation region in the x-direction (default=4.0)
       * **sy** (float): Size of the simulation region in the y-direction (default=4.0)
       * **plot_mode_number** (int): Which mode to plot (only plots one mode at a time).  Must be a number equal to or less than num_mode (default=1)
       * **polarization** (string): If true, outputs the fields at the relevant waveguide cross-sections (top-down and side-view)
       * **epsilon_file** (string): Filename with the dielectric "block" objects (default=None)
       * **output_directory** (string): If true, outputs the fields at the relevant waveguide cross-sections (top-down and side-view)
       * **save_mode_data** (boolean): Save the mode image and data to a separate file (default=None)
       * **suppress_window** (boolean): Suppress the matplotlib window (default=False)
    """
    #Boolean inputs
    save_mode_data = args.save_mode_data
    suppress_window = args.suppress_window

    #String inputs
    polarization = args.polarization
    epsilon_file = args.epsilon_file
    output_directory = args.output_directory
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    #Int inputs
    res = args.res
#    num_modes = args.num_modes
    plot_mode_number = args.plot_mode_number

    #Float inputs
    wavelength = args.wavelength
    sx = args.sx
    sy = args.sy

    geometry_lattice = mp.Lattice(size=mp.Vector3(0,sy,sx))

    with h5py.File(epsilon_file,'r') as hf:
        data = np.array([np.array(hf.get("CX")),
                         np.array(hf.get("CY")),
                         np.array(hf.get("width_list")),
                         np.array(hf.get("height_list")),
                         np.array(hf.get("eps_list"))])
    geometry = []
    for i in range(len(data[0])):
        geometry.append(mp.Block(size=mp.Vector3(mp.inf, data[3][i], data[2][i]),
                                 center=mp.Vector3(0, data[1][i], data[0][i]),
                                 material=mp.Medium(epsilon=data[4][i])))

    ms = mpb.ModeSolver(geometry_lattice=geometry_lattice,
                        geometry=geometry,
                        resolution=res,
                        default_material=mp.Medium(epsilon=1.0),
                        num_bands=plot_mode_number)
    freq = 1/wavelength
    kdir = mp.Vector3(1,0,0)
    tol = 1e-6
    kmag_guess = freq*2.02
    kmag_min = freq*0.01
    kmag_max = freq*10.0

    if polarization=="TE":
        parity=mp.ODD_Z
    elif polarization=="TM":
        parity=mp.EVEN_Z
    elif polarization=="None":
        parity=mp.NO_PARITY

    k = ms.find_k(parity, freq, plot_mode_number, plot_mode_number, kdir, tol, kmag_guess, kmag_min, kmag_max)
    vg = ms.compute_group_velocities()
    print('k='+str(k))
    print('v_g='+str(vg))

    k=k[0]
    vg=vg[0][0]

    """ Plot modes """
    eps = ms.get_epsilon()
    ms.get_dfield(plot_mode_number)
    E = ms.get_efield(plot_mode_number)
    Eabs = np.sqrt(np.multiply(E[:,:,0,2],E[:,:,0,2]) + np.multiply(E[:,:,0,1],E[:,:,0,1]) + np.multiply(E[:,:,0,0],E[:,:,0,0]))
    H = ms.get_hfield(plot_mode_number)
    Habs = np.sqrt(np.multiply(H[:,:,0,2],H[:,:,0,2]) + np.multiply(H[:,:,0,1],H[:,:,0,1]) + np.multiply(H[:,:,0,0],H[:,:,0,0]))

    plt_extent = [-sy/2.0, +sy/2.0, -sx/2.0, +sx/2.0]

    cmap_fields = 'hot_r'
    cmap_geom = 'viridis'

    if not suppress_window:
        """
        First plot electric field
        """
        plt.figure(figsize=(14,8))

        plt.subplot(2, 3, 1)
        plt.imshow(abs(E[:,:,0,2]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|E_x|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 2)
        plt.imshow(abs(E[:,:,0,1]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|E_y|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 3)
        plt.imshow(abs(E[:,:,0,0]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|E_z|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 4)
        plt.imshow(abs(Eabs),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|E|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 5)
        plt.imshow(eps,cmap=cmap_geom,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide dielectric")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.tight_layout()
        plt.show()

        """
        Then plot magnetic field
        """
        plt.figure(figsize=(14,8))

        plt.subplot(2, 3, 1)
        plt.imshow(abs(H[:,:,0,2]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|H_x|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 2)
        plt.imshow(abs(H[:,:,0,1]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|H_y|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 3)
        plt.imshow(abs(H[:,:,0,0]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|H_z|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 4)
        plt.imshow(abs(Habs),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|H|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 5)
        plt.imshow(eps,cmap=cmap_geom,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide dielectric")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.tight_layout()
        plt.show()

    if save_mode_data:
        """
        First plot electric field
        """
        plt.figure(figsize=(14,8))

        plt.subplot(2, 3, 1)
        plt.imshow(abs(E[:,:,0,2]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|E_x|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 2)
        plt.imshow(abs(E[:,:,0,1]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|E_y|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 3)
        plt.imshow(abs(E[:,:,0,0]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|E_z|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 4)
        plt.imshow(abs(Eabs),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|E|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 5)
        plt.imshow(eps,cmap=cmap_geom,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide dielectric")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.tight_layout()
        if polarization=="TE":
            savetxt='%s/TE_mode%d_Efield.png' % (output_directory, plot_mode_number)
        elif polarization=="TM":
            savetxt='%s/TM_mode%d_Efield.png' % (output_directory, plot_mode_number)
        elif polarization=="None":
            savetxt='%s/mode%d_Efield.png' % (output_directory, plot_mode_number)
        plt.savefig(savetxt)

        """
        Then plot magnetic field
        """
        plt.figure(figsize=(14,8))

        plt.subplot(2, 3, 1)
        plt.imshow(abs(H[:,:,0,2]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|H_x|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 2)
        plt.imshow(abs(H[:,:,0,1]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|H_y|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 3)
        plt.imshow(abs(H[:,:,0,0]),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|H_z|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 4)
        plt.imshow(abs(Habs),cmap=cmap_fields,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide mode $|H|$")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.subplot(2, 3, 5)
        plt.imshow(eps,cmap=cmap_geom,origin='lower',aspect='auto', extent=plt_extent)
        plt.title("Waveguide dielectric")
        plt.ylabel("y-axis")
        plt.xlabel("x-axis")
        plt.colorbar()

        plt.tight_layout()
        if polarization=="TE":
            savetxt='%s/TE_mode%d_Hfield.png' % (output_directory, plot_mode_number)
        elif polarization=="TM":
            savetxt='%s/TM_mode%d_Hfield.png' % (output_directory, plot_mode_number)
        elif polarization=="None":
            savetxt='%s/mode%d_Hfield.png' % (output_directory, plot_mode_number)
        plt.savefig(savetxt)

        """
        Save the mode data to a .txt file
        """
        if polarization=="TE":
            datafilename='%s/TE_mode%d_data.txt' % (output_directory, plot_mode_number)
        elif polarization=="TM":
            datafilename='%s/TM_mode%d_data.txt' % (output_directory, plot_mode_number)
        elif polarization=="None":
            datafilename='%s/mode%d_data.txt' % (output_directory, plot_mode_number)
        f = open(datafilename, 'w')
        f.write('#################################################################\n')
        f.write('Mode %d with %s polarization \n'%(plot_mode_number, polarization))
        f.write('#################################################################\n')
        f.write('\n')
        f.write('k \t\t %0.6f \n'%(k))
        f.write('n_eff \t\t %0.6f \n'%(wavelength*k))
        f.write('vg \t\t %0.6f \n'%(vg))
        f.write('ng \t\t %0.6f \n'%(1/vg))

if __name__ == "__main__":
    """
    Args:
       * **res** (int): Resolution of the simulation [pixels/um] (default=10)
       * **wavelength** (float): Wavelength in microns (default=1.55)
       * **sx** (float): Size of the simulation region in the x-direction (default=4.0)
       * **sy** (float): Size of the simulation region in the y-direction (default=4.0)
       * **plot_mode_number** (int): Which mode to plot (only plots one mode at a time).  Must be a number equal to or less than num_mode (default=1)
       * **polarization** (string): If true, outputs the fields at the relevant waveguide cross-sections (top-down and side-view)
       * **epsilon_file** (string): Filename with the dielectric "block" objects (default=None)
       * **output_directory** (string): If true, outputs the fields at the relevant waveguide cross-sections (top-down and side-view)
       * **save_mode_data** (boolean): Save the mode image and data to a separate file (default=None)
       * **suppress_window** (boolean): Suppress the matplotlib window (default=False)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-res', type=int, default=10, help='Resolution of the simulation [pixels/um] (default=10)')
    parser.add_argument('-wavelength', type=float, default=1.55, help='Wavelength in microns (default=1.55)')
    parser.add_argument('-sx', type=float, default=4.0, help='Size of the simulation region in the x-direction (default=4.0)')
    parser.add_argument('-sy', type=float, default=4.0, help='Size of the simulation region in the y-direction (default=4.0)')
#    parser.add_argument('-num_modes', type=int, default=1, help='Number of modes to compute (defaults=1)')
    parser.add_argument('-plot_mode_number', type=int, default=1, help='Which mode to plot (only plots one mode at a time).  Must be a number equal to or less than num_mode (default=1)')
    parser.add_argument('-polarization', type=str, default=None, help='Name of the output directory (for storing the fields) (default=None)')
    parser.add_argument('-epsilon_file', type=str, default=None, help='Filename with the dielectric "block" objects (default=None)')
    parser.add_argument('-output_directory', type=str, default=None, help='Name of the output directory (for storing the fields) (default=None)')
    parser.add_argument('-save_mode_data', type=str2bool, nargs='?', const=True, default=True, help='Save the mode image and data to a separate file (default=True)')
    parser.add_argument('-suppress_window', type=str2bool, nargs='?', const=True, default=False, help='Suppress the matplotlib window (default=False)')

    args = parser.parse_args()
    main(args)
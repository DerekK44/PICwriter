#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""
import numpy as np
import gdspy
from picwriter import toolkit as tk
from picwriter.components import *

X_SIZE, Y_SIZE = 15000, 15000
exclusion_region = 2000.0 #region where no devices are to be fabricated
x0, y0 = X_SIZE/2.0, Y_SIZE/2.0 #define origin of the die
step = 100.0 #standard spacing between components

""" Top level Cell that contains everything """
top = gdspy.Cell("top")

wgt = WaveguideTemplate(wg_width=0.45, clad_width=10.0, bend_radius=100,
                        resist='+', fab='ETCH', layer=1, datatype=1)

""" Add a die outline, with exclusion, from gdspy geometries found at
    http://gdspy.readthedocs.io/en/latest/"""
top.add(gdspy.Rectangle((0,0), (X_SIZE, Y_SIZE), layer=6, datatype=0))
top.add(gdspy.Rectangle((0, Y_SIZE-exclusion_region), (X_SIZE, Y_SIZE), layer=7, datatype=0))
top.add(gdspy.Rectangle((0, 0), (X_SIZE, exclusion_region), layer=7, datatype=0))
top.add(gdspy.Rectangle((0, 0), (exclusion_region, Y_SIZE), layer=7, datatype=0))
top.add(gdspy.Rectangle((X_SIZE-exclusion_region, 0), (X_SIZE, Y_SIZE), layer=7, datatype=0))

""" Add some components from the PICwriter library """
spiral_unit = gdspy.Cell("spiral_unit")
sp1 = Spiral(wgt, 1000.0, 1000.0, 10000, parity=1, center=(500.0+exclusion_region+4*step,y0))
tk.add(spiral_unit, sp1)

wg1=Waveguide([sp1.portlist["input"]["port"], (sp1.portlist["input"]["port"][0], 4000.0)], wgt)
wg2=Waveguide([sp1.portlist["output"]["port"], (sp1.portlist["output"]["port"][0], Y_SIZE-4000.0)], wgt)
tk.add(spiral_unit, wg1)
tk.add(spiral_unit, wg2)

tp_bot = Taper(wgt, length=100.0, end_width=0.1, **wg1.portlist["output"])
tk.add(spiral_unit, tp_bot)

gc_top = GratingCouplerFocusing(wgt, focus_distance=20, width=20, length=40,
                                period=0.7, dutycycle=0.4, wavelength=1.55,
                                sin_theta=np.sin(np.pi*8/180), **wg2.portlist["output"])
tk.add(spiral_unit, gc_top)

for i in range(9):
    top.add(gdspy.CellReference(spiral_unit, (i*1100.0, 0)))

""" Visualize layout using gdspy's LayoutViewer"""
gdspy.LayoutViewer()
""" Or save the file to a .GDSII file """
print("Writing mask...")
print("dependencies="+str(top.get_dependencies()))
gdspy.write_gds('mask_template.gds', unit=1.0e-6, precision=1.0e-9)
print("EOF")

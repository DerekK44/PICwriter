# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""
import gdspy
from picwriter import toolkit as tk
from picwriter.components import *

top = gdspy.Cell('top')
wgt = WaveguideTemplate(wg_width=0.45, clad_width=10.0, bend_radius=100, resist='+', fab='ETCH', wg_layer=1, wg_datatype=0, clad_layer=2, clad_datatype=0)

wg1 = Waveguide([(0,0), (200,0)], wgt)
tk.add(top, wg1)

mmi1 = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, **wg1.portlist['output'])
tk.add(top, mmi1)

mmi2 = MMI1x2(wgt, length=50, width=10, taper_width=2.0, wg_sep=3, port=(1750, 0), direction='WEST')
tk.add(top, mmi2)

(xtop, ytop) = mmi1.portlist['output_top']['port']
wg2 = Waveguide([(xtop, ytop),
                 (xtop+100, ytop),
                 (xtop+100, ytop+200),
                 (xtop+200, ytop+200)], wgt)
tk.add(top, wg2)

sp = Spiral(wgt, 600.0, 1000.0, 8000.0, parity=-1, **wg2.portlist['output'])
tk.add(top, sp)

(xtop_out, ytop_out) = sp.portlist['output']['port']
(xmmi_top, ymmi_top) = mmi2.portlist['output_bot']['port']
wg_spiral_out = Waveguide([(xtop_out, ytop_out),
                            (xmmi_top-100, ytop_out),
                            (xmmi_top-100, ytop_out-200),
                            (xmmi_top, ytop_out-200)], wgt)
tk.add(top, wg_spiral_out)

(xbot, ybot) = mmi1.portlist['output_bot']['port']
wg3 = Waveguide([(xbot, ybot),
                 (xbot+100, ybot),
                 (xbot+100, ybot-200),
                 (xmmi_top-100, ybot-200),
                 (xmmi_top-100, ybot),
                 (xmmi_top, ybot)], wgt)
tk.add(top, wg3)

wg_out = Waveguide([mmi2.portlist['input']['port'],
                    (mmi2.portlist['input']['port'][0]+200, mmi2.portlist['input']['port'][1])], wgt)
tk.add(top, wg_out)


tk.build_mask(top, wgt, final_layer=3, final_datatype=0)

gdspy.LayoutViewer()
gdspy.write_gds('tutorial2.gds', unit=1.0e-6, precision=1.0e-9)

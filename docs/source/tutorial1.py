import gdspy
from picwriter import toolkit as tk
import picwriter.components as pc

top = gdspy.Cell("top")

top.add(gdspy.Rectangle((0,0), (1000, 1000), layer=100, datatype=0))

wgt = pc.WaveguideTemplate(wg_width=0.45, clad_width=10.0, bend_radius=100, resist='+', fab='ETCH',
                        	wg_layer=1, wg_datatype=0, clad_layer=2, clad_datatype=0)
wg = pc.Waveguide([(25, 25), (975, 25), (975,500), (25,500),(25,975),(975,975)], wgt)

tk.add(top, wg)

tk.build_mask(top, wgt, final_layer=3, final_datatype=0)

gdspy.LayoutViewer()
gdspy.write_gds('tutorial.gds', unit=1.0e-6, precision=1.0e-9)
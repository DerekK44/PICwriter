Mach-Zehnder Interferometer
++++++++++++++++++++++++++++++++++

.. automodule:: picwriter.components
   :members: MachZehnder
   
.. image:: imgs/mzi.png

The above image of an unbalanced Mach-Zehnder with heaters for thermo-optic phase modulation is easily generated from the following code::

    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(bend_radius=50, wg_width=1.0, resist='+')
    htr_mt = MetalTemplate(width=25, clad_width=25, bend_radius=wgt.bend_radius, resist='+', fab="ETCH", metal_layer=13, metal_datatype=0, clad_layer=14, clad_datatype=0)
    mt = MetalTemplate(width=25, clad_width=25, resist='+', fab="ETCH", metal_layer=11, metal_datatype=0, clad_layer=12, clad_datatype=0)

    wg_in = Waveguide([(0,0), (300,0)], wgt)
    tk.add(top, wg_in)
    mzi = MachZehnder(wgt, MMIlength=50, MMIwidth=10, MMItaper_width=2.0, MMIwg_sep=3, arm1=0, arm2=100, heater=True, heater_length=400, mt=htr_mt, **wg_in.portlist["output"])
    tk.add(top, mzi)
    wg_out = Waveguide([mzi.portlist["output"]["port"], (mzi.portlist["output"]["port"][0]+300, mzi.portlist["output"]["port"][1])], wgt)
    tk.add(top, wg_out)

    mt1=MetalRoute([mzi.portlist["heater_top_in"]["port"],
                    (mzi.portlist["heater_top_in"]["port"][0]-150, mzi.portlist["heater_top_in"]["port"][1]),
                    (mzi.portlist["heater_top_in"]["port"][0]-150, mzi.portlist["heater_top_in"]["port"][1]+200)], mt)
    mt2=MetalRoute([mzi.portlist["heater_top_out"]["port"],
                    (mzi.portlist["heater_top_out"]["port"][0]+150, mzi.portlist["heater_top_out"]["port"][1]),
                    (mzi.portlist["heater_top_out"]["port"][0]+150, mzi.portlist["heater_top_out"]["port"][1]+200)], mt)
    mt3=MetalRoute([mzi.portlist["heater_bot_in"]["port"],
                    (mzi.portlist["heater_bot_in"]["port"][0]-150, mzi.portlist["heater_bot_in"]["port"][1]),
                    (mzi.portlist["heater_bot_in"]["port"][0]-150, mzi.portlist["heater_bot_in"]["port"][1]-200)], mt)
    mt4=MetalRoute([mzi.portlist["heater_bot_out"]["port"],
                    (mzi.portlist["heater_bot_out"]["port"][0]+150, mzi.portlist["heater_bot_out"]["port"][1]),
                    (mzi.portlist["heater_bot_out"]["port"][0]+150, mzi.portlist["heater_bot_out"]["port"][1]-200)], mt)
    tk.add(top, mt1)
    tk.add(top, mt2)
    tk.add(top, mt3)
    tk.add(top, mt4)
    tk.add(top, Bondpad(mt, **mt1.portlist["output"]))
    tk.add(top, Bondpad(mt, **mt2.portlist["output"]))
    tk.add(top, Bondpad(mt, **mt3.portlist["output"]))
    tk.add(top, Bondpad(mt, **mt4.portlist["output"]))

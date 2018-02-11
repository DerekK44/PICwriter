Tutorial
********

Getting started with PICwriter is easy.  In the examples below, we'll walk you through quickly generating a couple lithography masks.


Basic code structure
====================

Every file should start with the following import statements::

    import gdspy
    from picwriter import toolkit as tk
    from picwriter.components import *
    
The first statement allows us to use the base commands from the gdspy library.  The second provides additional functionality for working with the picwriter components, which are imported with the third statement.  Next, we can create a top-level cell that we will add all of our PIC components to::

    top = gdspy.Cell("top")
                        	
Now, we can just add a simple geometric shape from the gdspy library, such as a square::

    top.add(gdspy.Rectangle((0,0), (1000, 1000), layer=100, datatype=0))
    
Let's add a simple waveguide with a bend.  To do this, we only need a reference to a WaveguideTemplate reference, and a set of waypoints (i.e. a list of (x,y) tuples).  The WaveguideTemplate class specifies all important parameters, such as resist type, waveguide width, cladding width, bending radius, then the layer and datatype::

    wgt = WaveguideTemplate(wg_width=0.45, clad_width=10.0, bend_radius=100, resist='+', fab='ETCH',
                        	wg_layer=1, wg_datatype=0, clad_layer=2, clad_datatype=0)
    wg = Waveguide([(25, 25), (975, 25), (975,500), (25,500),(25,975),(975,975)], wgt)

We then add this to the top cell using the toolkit "add" method::

    tk.add(top, wg)
    
This is simply a shortcut for the gdspy add method (which would look like `top.add(gdspy.CellReference(subcell))`.  Both are equivalent, though the first is slightly less typing.  To generate the mask according to the fab specifications (positive/negative resist, and fabrication type), we can call the `tk.build_mask()` function::

    tk.build_mask(top, wgt, final_layer=3, final_datatype=0)
    
This simply takes the waveguide layer and the cladding layer, then does the appropraite 'xor' operation (or just simply returns the waveguide layer).  Lastly, we can visualize everything by either visualizing with the built-in gdspy LayoutViewer, or exporting to a GDSII file in the working directory of your python script::

    gdspy.LayoutViewer()
    gdspy.write_gds('tutorial.gds', unit=1.0e-6, precision=1.0e-9)
    
The 'units' specifies we are using microns as the base unit, and 'precision' specifies 1 nm precision.

Putting it all together
+++++++++++++++++++++++

Below is the entire program, along with an image of the GDSII file it generates::

    import gdspy
    from picwriter import toolkit as tk
    from picwriter.components import *
    
    top = gdspy.Cell("top")
    wgt = WaveguideTemplate(wg_width=0.45, clad_width=10.0, bend_radius=100, resist='+', fab='ETCH',
                        	wg_layer=1, wg_datatype=0, clad_layer=2, clad_datatype=0)
                        	
    top.add(gdspy.Rectangle((0,0), (1000, 1000), layer=100, datatype=0))
    wg = Waveguide([(25, 25), (975, 25), (975,500), (25,500),(25,975),(975,975)], wgt)
    tk.add(top, wg)
    
    tk.build_mask(top, wgt, final_layer=3, final_datatype=0)
    
    gdspy.LayoutViewer()
    gdspy.write_gds('tutorial.gds', unit=1.0e-6, precision=1.0e-9)
    
The results should look like this, if we select only the final layer (3/0) and layer for the square (100/0):

.. image:: imgs/tutorial1.png

Putting components together
===========================

Here we show how to generate a slightly more complex mask using the set of supported components that come standard in the picwriter library.  Let's build up an interesting object, a Mach-Zehnder interferometer, which consists of two 1x2 MMI's, and one arm that is much longer than the other.  But to make it longer, we need to use a `spiral` type of waveguide (for compactness).

Unbalanced Mach-Zehnder Interferometer with Spiral Arm
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Each component is added individually, then placed on the `top` layer, as shown below::

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
    
The resulting GDSII file looks like this:

.. image:: imgs/tutorial2.png

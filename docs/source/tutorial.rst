Tutorial
********

Getting started with PICwriter is easy, assuming everything's been installed appropriately.  In the examples below, we'll walk you through generating a quick lithography mask.


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

    wgt = WaveguideTemplate(wg_width=0.45, clad_width=10.0, bend_radius=100, resist='+', fab='ETCH', layer=1, datatype=1)
    wg=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)

We then add this to the top cell using the toolkit "add" method::

    tk.add(top, wg)
    
This is simply a shortcut for the gdspy add method (which would look like `top.add(gdspy.CellReference(subcell))`.  Both are equivalent, though the first is slightly less typing.  Lastly, we can visualize everything by either visualizing with the built-in gdspy LayoutViewer, or exporting to a GDSII file in the working directory of your python script::

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
    wgt = WaveguideTemplate(wg_width=0.45, clad_width=10.0, bend_radius=100, resist='+', fab='ETCH', layer=1, datatype=1)
                        	
    top.add(gdspy.Rectangle((0,0), (1000, 1000), layer=100, datatype=0))
    wg=Waveguide([(50,0), (250,0), (250,500), (500,500)], wgt)
    tk.add(top, wg)
    gdspy.LayoutViewer()
    gdspy.write_gds('tutorial.gds', unit=1.0e-6, precision=1.0e-9)



Adding some simple components
=============================

Here we show how to generate a slightly more complex mask using the set of supported components that come standard in the picwriter library.

Waveguides & Waveguide Templates
++++++++++++++++++++++++++++++++

Stay tuned for more content, coming soon!

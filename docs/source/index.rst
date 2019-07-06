PICwriter Documentation
=======================

Picwriter (Photonic-Integrated-Circuit Writer) is a free Python module, built above the gdspy module, aimed at simplifying the process of designing complex GDSII masks for photonic integrated circuits through a prebuilt library of easy-to-implement PCells. Supported blocks include waveguides, straight grating couplers, focusing grating couplers, tapers, directional couplers, multi-mode interferometers (MMI's), resonators, spiral structures, and more that are coming soon!

Features
--------

The ultimate goal of this module is to reduce the time required to generate photonic integrated circuit mask designs, by extending the functionality of the gdspy library.

* High-level specification of common building blocks for photonic-integrated circuits
* Easily snap photonic components together using portlist syntax and waypoint routing of waveguides and metal traces
* PICwriter will automatically detect if you are adding a cell to the mask which is identical to one added before, so you don't have to worry about referencing existing cells.
* Waveguide bends and curves automatically compute the number of vertices per polygon to minimize grid errors.
* (coming soon!) simple templates for writing your own custom PCells to be used with PICwriter

Contribute
----------

This project got started because I wanted to make it easier to generate simple lithography masks for in-house fabrication of PICs at MIT.  If you find this project useful, or have ideas for new components to add to the library, please feel free to contribute to the project!

- Issue Tracker: `github.com/DerekK88/PICwriter/issues <https://github.com/DerekK88/PICwriter/issues>`_
- Source Code: `github.com/DerekK88/PICwriter <https://github.com/DerekK88/PICwriter>`_

Guide
^^^^^
.. toctree::
   :maxdepth: 2

   installation.rst
   tutorial.rst
   component-documentation.rst
   picsim-documentation.rst
   toolkit-documentation.rst
   license.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

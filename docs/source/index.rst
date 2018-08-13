PICwriter Documentation
=======================

Picwriter (Photonic-Integrated-Circuit Writer) is a free Python module, built above the gdspy module, aimed at simplifying the process of designing complex GDSII masks for photonic integrated circuits through a prebuilt library of easy-to-implement PCells (technically all sub-classes of the gdspy Cell class). Supported blocks include waveguides, straight grating couplers, focusing grating couplers, tapers, directional couplers, multi-mode interferometers (MMI's), resonators, spiral structures, and more that are coming soon!

Features
--------

The ultimate goal of this module is to reduce the time required to generate photonic integrated circuit mask designs, by extending the functionality of the gdspy library.

* High-level specification of common building blocks for photonic-integrated circuits
* Fabrication specific masks. Specify the photoresist type (`'+'` or `'-'`) and fabrication type (such as `'ETCH'`) and PICwriter will generate the appropriate mask files for single-layer electron-beam or photolithography.
* All library components are subclasses of the `gdspy Cell class <http://gdspy.readthedocs.io/en/latest/library.html#cell>`_, so gdspy Cell features such as `rotation()`, `copy()`, `flatten()`, `get_bounding_box()`, etc. are all supported.
* Unique cell identifiers. Add components to your mask layout without worrying about name-clashes.

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

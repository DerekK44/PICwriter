PICwriter Documentation
=======================

Picwriter (Photonic-Integrated-Circuit Writer) is a Python module, built above the gdspy module, aimed at simplifying the process of designing complex masks for photonic integrated circuits through a prebuilt library of easy-to-implement PCells (technically all sub-classes of the gdspy Cell class). Supported blocks currently include: waveguides, straight grating couplers, focusing grating couplers, tapers. Multi-mode interferometers (MMI's), resonators, spiral structures, and more are coming soon!

Features
--------

The ultimate goal of this module is to reduce the time required to generate photonic integrated circuit mask designs, by extending the functionality of the gdspy library.

* High-level specification of common building blocks for photonic-integrated circuits
* Fabrication specific masks. Specify the photoresist type (`'+'` or `'-'`) and fabrication type (such as `'ETCH'`) and PICwriter will generate the appropriate mask files for electron-beam or photolithography.
* All library components are subclasses of the gdspy Cell class, so gdspy Cell features such as `rotation()`, `copy()`, `flatten()`, `get_bounding_box()`, etc. are all supported.
* Unique cell identifiers. Add components to your mask layout without worrying about name-clashes.

Installation
============

PICwriter is tested on python versions 2.7, 3.4, 3.5, and 3.6 on Linux, OS X, and Windows.  Please check `here <https://github.com/DerekK88/PICwriter>`_ for the current build status (if building from source).

Installation (Linux / OS X)
---------------------------

(**Option 1**) Install PICwriter by first downloading the source code `here <https://github.com/DerekK88/PICwriter>`_. and then run:::

    python setup.py install

(**Option 2**) Install PICwriter by running:::

    pip install picwriter
    
Installation (Windows)
----------------------

The best way of obtaining the library is by installing the prebuilt binaries.

* First, go to the `gdspy avvpeyor project page <https://ci.appveyor.com/project/heitzmann/gdspy>`_, then click the python environment that matches your python environment, click the **Artifacts** tab, and then download the corresponding `dist\gdspy-1.X.X.X.whl` wheel file.
* Open up a command prompt (type `cmd` in the search bar), navigate to your downloads, then install via:::

    pip install dist\gdspy-1.X.X.X.whl
    
* Next, install the PICwriter library by following the same procedure at the `picwriter appveyor page <https://ci.appveyor.com/project/DerekK88/picwriter>`_ to install the corresponding prebuilt picwriter `.whl` file.
* In a command prompt, install with pip::

    pip install dist\picwriter-1.X.X.X.whl
    
Building from source is also possible. For installing gdspy, an appropriate build environment is required for compilation of the C extension modules.

Getting Started
===============

Once PICwriter is installed, check that it is installed (along with gdspy) by running:

    import gdspy
    import picwriter
    
in a python file or python prompt.  To get a feel for using the PICwriter library, checkout the tutorial here.

Contribute
----------

- Issue Tracker: github.com/DerekK88/PICwriter/issues
- Source Code: github.com/DerekK88/PICwriter

Guide
^^^^^
.. toctree::
   :maxdepth: 2

   license.rst
   help.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

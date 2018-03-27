Installation
============

PICwriter is tested on python versions 2.7, 3.4, 3.5, and 3.6 on Linux, OS X, and Windows.  Please check `here <https://github.com/DerekK88/PICwriter>`_ for the current build status (if building from source).

Requirements
------------

A working version of python is required for using the PICwriter library.  You can go to `python.org <https://www.python.org/downloads/>`_ to download python (or check if it's installed on your computer by running `python -\\-version` in a command prompt or terminal.  I personally recommend downloading `Anaconda <https://www.anaconda.com/download/>`_ since it includes several nice scientific libraries, the conda package manager, Spyder IDE, and other niceties.

Installation (Linux / OS X)
---------------------------

(**Option 1 (preferred)**) Install PICwriter by first downloading the source code `here <https://github.com/DerekK88/PICwriter>`_. and then in the picwriter directory run::

    python setup.py install
    
(**Option 2:**) Install PICwriter by running::

    pip install picwriter
    
Installation (Windows)
----------------------

The best way of obtaining the library is by installing the prebuilt binaries.

* First, go to the `gdspy appveyor project page <https://ci.appveyor.com/project/heitzmann/gdspy>`_, then click the python environment that matches your python version and processor type.  For example, if you have a 64-bit processor with Python version 3.5 (you can check by running `python --version` in a command prompt) then you would click 'PYTHON=C:\Python35-x64'.  Then, click the **Artifacts** tab and download the corresponding `dist\gdspy-1.X.X.X.whl` wheel file.
* Open up a command prompt (type `cmd` in the search bar), navigate to your downloads, then install the appropriate `.whl` file via::

    pip install gdspy-1.X.X.X.whl
    
* Next, install the PICwriter library by following the same procedure as before at the `picwriter appveyor page <https://ci.appveyor.com/project/DerekK88/picwriter>`_ to install the corresponding prebuilt picwriter `.whl` file.
* In a command prompt, navigate to your downloads and install the appropriate `.whl` file with pip::

    pip install picwriter-1.X.X.X.whl
    
Building from source is also possible. For installing gdspy, an appropriate build environment is required for compilation of the C extension modules.

Getting Started
---------------

You can check that PICwriter and gdspy are properly installed by running::

    import gdspy
    import picwriter
    
in a python file or python prompt.  To get a feel for using the PICwriter library, checkout the Tutorial page.

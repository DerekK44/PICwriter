Linux/OS: [![Build Status](https://travis-ci.org/DerekK88/PICwriter.svg?branch=master)](https://travis-ci.org/DerekK88/PICwriter)
Windows: [![Build status](https://ci.appveyor.com/api/projects/status/f9q96u9na63hy3ce?svg=true)](https://ci.appveyor.com/project/DerekK88/PICwriter)
Documentation: [![Documentation Status](https://readthedocs.org/projects/picwriter/badge/?version=latest)](http://picwriter.readthedocs.io/en/latest/?badge=latest)

# PICwriter README
Picwriter (Photonic-Integrated-Circuit Writer) is a [Python](https://www.python.org/) module, built above the [gdspy](https://github.com/heitzmann/gdspy) module, aimed at simplifying the process of designing complex masks for photonic integrated circuits through a prebuilt library of easy-to-implement PCells (technically all sub-classes of the gdspy Cell class).  Supported blocks currently include: 
* waveguides (strip, slot, and sub-wavelength grating)
* grating couplers (straight and focusing)
* tapers
* directional couplers
* spiral structures (auto-generated from specified waveguide length)
* 1x2 multi-mode interferometers
* 2x2 multi-mode interferometers
* ring & disk resonators with automatic bus waveguide wrapping
* distributed bragg reflectors
* Mach-Zehnder interferometers
* alignment markers (for photolithography and ebeam lithography)
* metal routes
* bond pads

Stay tuned, more components are coming soon!  In the meantime, check out the documentation for this project at [picwriter.readthedocs.io](http://picwriter.readthedocs.io).

## Features
The ultimate goal of this module is to reduce the time required to generate photonic integrated circuit mask designs, by extending the functionality of the gdspy library.
* High-level specification of common building blocks for photonic-integrated circuits
* Fabrication specific masks.  Specify the photoresist type (`'+'` or `'-'`) and fabrication type (such as `'ETCH'`) and PICwriter will generate the appropriate mask files for electron-beam or photolithography.
* All library components are subclasses of the gdspy Cell class, so gdspy Cell features such as `rotation()`, `copy()`, `flatten()`, `get_bounding_box()`, etc. are all supported.
* Unique cell identifiers.  Add components to your mask layout without worrying about name-clashes.

## Installation

### Dependencies:
With a working version of python, all dependencies should be automatically installed through the instructions below.

* [Python](http://www.python.org/) (tested with versions 2.7, 3.4, 3.5, 3.6 for Linux/OS, tested with versions 2.7, 3.4, 3.5, 3.6, 2.7-x64, 3.4-x64, 3.5-x64, 3.6-x64 for Windows.)
* [gdspy](https://github.com/heitzmann/gdspy) (tested with versions 2.7, 3.4, 3.5, and 3.6)
* [Numpy](http://numpy.scipy.org/)
* [UUID](https://pypi.python.org/pypi/uuid/)
* [SciPy](https://www.scipy.org/)
* [Python-future](http://python-future.org/) (only for Python 2)

### Linux / OS X
Both options should automatically install all dependencies (like gdspy, numpy, etc.).

Option 1: using [pip](https://docs.python.org/3/installing/):

```sh
pip install picwriter
```

Option 2: download the source from [github](https://github.com/DerekK88/picwriter) and build/install with:

```sh
python setup.py install
```

### Windows

The best way of obtaining the library is by installing the prebuilt binaries.

* First, go to the [gdspy appveyor project page](https://ci.appveyor.com/project/heitzmann/gdspy), then click the python environment that matches your python version and processor type.  For example, if you have a 64-bit processor with Python version 3.5 (you can check by running `python --version` in a command prompt) then you would click 'PYTHON=C:\Python35-x64'.  Then, click the **Artifacts** tab and download the corresponding `dist\gdspy-1.X.X.X.whl` wheel file.
* Open up a command prompt (type `cmd` in the search bar), navigate to your downloads, then install via:

```sh
pip install dist\gdspy-1.X.X.X.whl
```
    
* Next, install the PICwriter library by following the same procedure as before at the [picwriter appveyor page](https://ci.appveyor.com/project/DerekK88/picwriter) to install the corresponding prebuilt picwriter `.whl` file.
* In a command prompt, navigate to your downloads and install with pip:

```sh
pip install dist\picwriter-1.X.X.X.whl
```

Building from source is also possible. For installing gdspy, an appropriate build environment is required for compilation of the C extension modules.

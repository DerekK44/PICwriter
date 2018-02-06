Linux/OS: [![Build Status](https://travis-ci.org/DerekK88/picwriter.svg?branch=master)](https://travis-ci.org/DerekK88/picwriter)
Windows: [![Build status](https://ci.appveyor.com/api/projects/status/f9q96u9na63hy3ce?svg=true)](https://ci.appveyor.com/project/DerekK88/picwriter)

# PICwriter README
Picwriter (Photonic-Integrated-Circuit Writer) is a Python module, built above the [gdspy](https://github.com/heitzmann/gdspy) module, aimed at simplifying the process of designing complex masks for photonic integrated circuits through a prebuilt library of easy-to-implement PCells (technically all sub-classes of the gdspy Cell class).  Supported blocks currently include: waveguides, straight grating couplers, focusing grating couplers, tapers.  Multi-mode interferometers (MMI's), resonators, spiral structures, and more are coming soon!

## Features
The ultimate goal of this module is to reduce the time required to generate photonic integrated circuit mask designs, by extending the functionality of the gdspy library.
* High-level specification of common building blocks for photonic-integrated circuits
* Fabrication specific masks.  Specify the photoresist type (`'+'` or `'-'`) and fabrication type (such as `'ETCH'`) and PICwriter will generate the appropriate mask files for electron-beam or photolithography.
* All library components are subclasses of the gdspy Cell class, so gdspy Cell features such as 'rotation()', 'copy()', 'flatten()', 'get_bounding_box()', etc. are all supported.
* Unique cell identifiers.  Add components to your mask layout without worrying about name-clashes.

## Installation

### Dependencies:

* [Python](http://www.python.org/) (tested with versions 2.7, 3.3, 3.4, 3.5, 3.6, 3.7, nightly for Linux/OS, tested with versions 2.7, 3.4, 3.5, 3.6, 2.7-x64, 3.4-x64, 3.5-x64, 3.6-x64 for Windows.)
* [gdspy](https://github.com/heitzmann/gdspy) (tested with versions 2.7, 3.4, 3.5, and 3.6)
* [Numpy](http://numpy.scipy.org/)
* [Python-future](http://python-future.org/) (only for Python 2)

### Linux / OS X
Both options should automatically install all dependencies (like gdspy, numpy, etc.).  This module is in the early planning stage, so stay tuned for the actual release :)

Option 1: using [pip](https://docs.python.org/3/installing/) (coming soon):

```sh
pip install picwriter
```

Option 2: download the source from [github](https://github.com/DerekK88/picwriter) and build/install with:

```sh
python setup.py install
```

### Windows
Installation via `pip` and building from source as above are possible.  For installing gdspy, an appropriate [build environment](https://wiki.python.org/moin/WindowsCompilers) is required for compilation of the C extension modules.

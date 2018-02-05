Linux/OS: [![Build Status](https://travis-ci.org/DerekK88/picwriter.svg?branch=master)](https://travis-ci.org/DerekK88/picwriter)
Windows: [![Build status](https://ci.appveyor.com/api/projects/status/f9q96u9na63hy3ce?svg=true)](https://ci.appveyor.com/project/DerekK88/picwriter)

# PICwriter README
Nothing here yet, though stay tuned for updates to come!

Picwriter (Photonic-Integrated-Circuit Writer) will be a Python module, built above the fantastic [gdspy](https://github.com/heitzmann/gdspy) module, aimed at simplifying the process of designing complex masks for photonic integrated circuits through a prebuilt library of easy-to-implement parameterized cells (PCells).  Supported blocks will include: waveguides, grating couplers, tapers, multi-mode interferometers (MMI's), resonators, spiral structures, and more!

## Installation

### Dependencies:

* [Python](http://www.python.org/) (tested with versions 2.7, 3.3, 3.4, 3.5, 3.6, 3.7, nightly for Linux/OS, tested with versions 2.7, 3.4, 3.5, 3.6, 2.7-x64, 3.5-x64, 3.6-x64 for Windows.  *Note you may need to install gdspy from Github if running Python3.4-x64 on Windows*)
* [gdspy](https://github.com/heitzmann/gdspy) (tested with versions 2.7, 3.4, 3.5, and 3.6)
* [Numpy](http://numpy.scipy.org/)
* [Python-future](http://python-future.org/) (only for Python 2)

### Linux / OS X
Both options should automatically install all dependencies (like gdspy, numpy, etc.).  This module is in the early planning stage, so stay tuned for the actual release :)

Option 1: using [pip](https://docs.python.org/3/installing/):

```sh
pip install picwriter
```

Option 2: download the source from [github](https://github.com/DerekK88/picwriter) and build/install with:

```sh
python setup.py install
```

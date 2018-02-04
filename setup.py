#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""

from setuptools import setup

setup(name='picwriter',
      version='0.0',
      description='Mask generation tool',
      url='http://github.com/DerekK88/picwriter',
      author='Derek Kita',
      license='MIT',
      classifiers=[
        # How mature is this project? Common values are
        'Development Status :: 1 - Planning',
        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
    
        # Pick your license as you wish (should match "license" above)
         'License :: OSI Approved :: MIT License',
    
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        ],
      keywords='mask writing library',
      packages=['picwriter'],
      install_requires=['gdspy', 'numpy'],
      zip_safe=False)
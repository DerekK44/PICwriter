#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: DerekK88
"""

from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='picwriter',
      version='0.3',
      description='Mask generation tool',
      long_description=readme(),
      url='http://github.com/DerekK88/picwriter',
      author='Derek Kita',
      license='MIT',
      classifiers=[
        # How mature is this project? Common values are
        'Development Status :: 2 - Pre-Alpha',
        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
    
        # Pick your license as you wish (should match "license" above)
         'License :: OSI Approved :: MIT License',
    
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        ],
      keywords='mask writing library',
      packages=['picwriter', 'picwriter.components'],
      install_requires=['gdspy', 'numpy'],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)

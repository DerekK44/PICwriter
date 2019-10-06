# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from .waveguide import WaveguideTemplate, Waveguide
from .electrical import MetalTemplate, MetalRoute, Bondpad
from .taper import Taper
from .gratingcoupler import (
    GratingCoupler,
    GratingCouplerStraight,
    GratingCouplerFocusing,
)
from .spiral import Spiral
from .mmi1x2 import MMI1x2
from .mmi2x2 import MMI2x2
from .ring import Ring
from .disk import Disk
from .alignmentmarker import AlignmentCross, AlignmentTarget
from .mzi import (
    MachZehnder,
    MachZehnderSwitch1x2,
    MachZehnderSwitchDC1x2,
    MachZehnderSwitchDC2x2,
)
from .dbr import DBR
from .directionalcoupler import DirectionalCoupler
from .contradc import ContraDirectionalCoupler
from .swgcontradc import SWGContraDirectionalCoupler
from .stripslotconverter import StripSlotConverter
from .stripslotyconverter import StripSlotYConverter
from .stripslotmmiconverter import StripSlotMMIConverter
from .adiabaticcoupler import AdiabaticCoupler
from .fullcoupler import FullCoupler
from .zerolengthcavity import ZeroLengthCavity
from .sbend import SBend
from .ebend import EBend, EulerSBend
from .bbend import BBend
from .ysplitter import SplineYSplitter

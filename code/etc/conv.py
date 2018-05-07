#!/usr/bin/env python

from __future__ import print_function
from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np
import sys

if len(sys.argv) != 3:
    print("usage: {} <infile> <outfile>".format(sys.argv[0]), file=sys.stderr)
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]
img = imread(infile)
imsave(outfile, img)

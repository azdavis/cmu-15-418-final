from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np
import sys

if len(sys.argv) != 3:
    print("usage: " + sys.argv[0] + " <infile> <outfile>")
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]
img = imread(infile)
imsave(outfile, img)

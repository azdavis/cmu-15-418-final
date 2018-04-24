from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np
import sys

guy = sys.argv[1]
print guy
img = imread(guy + ".jpg").astype(np.int32)
imsave(guy + ".ppm", img)

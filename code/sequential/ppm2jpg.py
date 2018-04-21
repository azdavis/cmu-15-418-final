from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np
import sys

guy = sys.argv[1]
print guy
img = imread(guy + ".ppm").astype(np.int32)
imsave(guy + ".jpg", img)

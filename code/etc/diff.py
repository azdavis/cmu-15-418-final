
from scipy.ndimage import imread
import numpy as np
import sys

guy = sys.argv[1]
print guy
guy2 = sys.argv[2]
print guy2
img = imread(guy + ".ppm").astype(np.uint8)
img2 = imread(guy2 + ".ppm").astype(np.uint8)

width = len(img[0])
height = len(img)

for i in range(height):
    for j in range(width):
        if (img[i][j][0] != img2[i][j][0] or
           img[i][j][1] != img2[i][j][1] or
           img[i][j][2] != img2[i][j][2]):
            print "diff ", img[i][j], img2[i][j], i, j

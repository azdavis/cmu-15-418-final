#!/usr/bin/env python

from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np
import math
import sys

if len(sys.argv) != 3:
    print("usage: " + sys.argv[0] + " <infile> <outfile>")
    sys.exit()

infile = sys.argv[1]
outfile = sys.argv[2]

img = imread(infile).astype(np.int32)
height, width, _ = np.shape(img)

walls = np.copy(img, True)
original = np.copy(img, True)

ltRtWallDenom = 7
ltWall = width / ltRtWallDenom
rtWall = (width * (ltRtWallDenom - 1)) / ltRtWallDenom
tpWallDenom = 8
tpWall = height / tpWallDenom

for i in range(height):
    walls[i][ltWall] = np.array([255,0,0])
    walls[i][rtWall] = np.array([0,255,0])

for j in range(width):
    walls[tpWall][j] = np.array([0,0,255])

bucket_size = 32
colors = 256
buckets = colors / bucket_size
color_counts = [
    [
        [ 0
            for _ in range(buckets)
        ]
        for _ in range(buckets)
    ]
    for _ in range(buckets)
]

ranges = [
    (0, ltWall, 0, height),
    (rtWall, width, 0, height),
    (0, width, 0, tpWall)
]

for xmin, xmax, ymin, ymax in ranges:
    for i in range(ymin, ymax):
        for j in range(xmin, xmax):
            this = img[i][j]
            r = this[0] / bucket_size
            g = this[1] / bucket_size
            b = this[2] / bucket_size
            color_counts[r][g][b] += 1

totalBCPix = ltWall * height + (width - rtWall) * height + tpWall * width
bcThresh = 0.005 * totalBCPix

dude = np.copy(img, True)
mask = np.zeros((height, width))

for i in range(height):
    for j in range(width):
        this = dude[i][j]
        r = this[0] / bucket_size
        g = this[1] / bucket_size
        b = this[2] / bucket_size
        if color_counts[r][g][b] < bcThresh:
            dude[i][j] = np.array([0,255,0])
            mask[i][j] = 1

newMask = np.copy(mask, True)
# Clean up mask
for i in range(2, height-2):
    for j in range(2, width-2):
        this = mask[i][j]
        if this == 0:
            borderSum = (mask[i-1][j] + mask[i][j-1] +
                         mask[i+1][j] + mask[i][j+1] +
                         mask[i-2][j] + mask[i][j-2] +
                         mask[i+2][j] + mask[i][j+2])
            if borderSum >= 2:
               dude[i][j] = np.array([0,0,0])
               newMask[i][j] = 1
mask = newMask

# Blur
blurred = np.zeros((height, width, 3), dtype=np.uint8)
blurDim = 11
blurKernel = np.ones((blurDim, blurDim), dtype=np.float32)

box_size = len(blurKernel)
for row in range(height):
    for col in range(width):
        count = 0.0
        red = 0.0
        green = 0.0
        blue = 0.0
        for i_k in range(len(blurKernel)):
            for j_k in range(len(blurKernel[0])):
                weight = blurKernel[i_k][j_k]
                i = row - (box_size / 2) + i_k
                j = col - (box_size / 2) + j_k
                if (i < 0 or i >= height or j < 0 or j >= width):
                    continue
                elif (mask[i][j] == 1):
                    continue
                red += weight * original[i][j][0]
                green += weight * original[i][j][1]
                blue += weight * original[i][j][2]
                count += weight
        if (count == 0):
            continue
        blurred[row][col][0] = red / count
        blurred[row][col][1] = green / count
        blurred[row][col][2] = blue / count

# Put filter on mask
for i in range(len(blurred)):
    for j in range(len(blurred[0])):
        if mask[i][j] == 1:
            blurred[i][j] = original[i][j]

imsave(outfile, blurred)

from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "elephant"
guy = "img/" + guy

print("prelims")

img = imread(guy + ".ppm").astype(np.int32)
height, width, _ = np.shape(img)

walls = np.copy(img, True)
original = np.copy(img, True)

ltRtWallDenom = 7
ltWall = width / ltRtWallDenom
rtWall = (width * (ltRtWallDenom - 1)) / ltRtWallDenom
tpWallDenom = 8
tpWall = height / tpWallDenom

print("show walls")

for i in range(height):
    walls[i][ltWall] = np.array([255,0,0])
    walls[i][rtWall] = np.array([0,255,0])

for j in range(width):
    walls[tpWall][j] = np.array([0,0,255])

imsave(guy + "_walls.ppm", walls)

print("get color_counts")

bucket_size = 16
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

ranges =  [
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
bcThresh = 0.01 * totalBCPix

print("use color_counts")

dude = np.copy(img, True)
mask = np.zeros((height, width))

for i in range(height):
    for j in range(width):
        this = dude[i][j]
        r = this[0] / bucket_size
        g = this[1] / bucket_size
        b = this[2] / bucket_size
        if color_counts[r][g][b] > bcThresh:
            dude[i][j] = np.array([0,255,0])
            mask[i][j] = 1

imsave(guy + "_predude.ppm", dude)

print("cleaning up mask")
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

imsave(guy + "_dude.ppm", dude)
# Blur
print "blur image"
blurred = np.zeros((height, width, 3))
blurKernel = [
                   [1, 4, 7, 4, 1],
                   [4, 16, 26, 16, 4],
                   [7, 26, 41, 26, 7],
                   [4, 16, 26, 16, 4],
                   [1, 4, 7, 4, 1]
                  ]
blurKernel = [[1] * 11] * 11
box_size = len(blurKernel)
for row in range(height):
    for col in range(width):
        count = 0
        for i_k in range(len(blurKernel)):
            for j_k in range(len(blurKernel[0])):
                weight = blurKernel[i_k][j_k]
                i = row - (box_size / 2) + i_k
                j = col - (box_size / 2) + j_k

                if (i < 0 or i >= height or j < 0 or j >= width):
                    continue
                elif (mask[i][j] == 1):
                    continue
                blurred[row][col][0] += weight * original[i][j][0]
                blurred[row][col][1] += weight * original[i][j][1]
                blurred[row][col][2] += weight * original[i][j][2]
                count += weight
        if (count == 0):
            continue
        blurred[row][col][0] = float(blurred[row][col][0]) / count
        blurred[row][col][1] = float(blurred[row][col][1]) / count
        blurred[row][col][2] = float(blurred[row][col][2]) / count

imsave(guy + "_blurred.ppm", blurred)

print("put on filter")
# Put filter on mask
for i in range(len(blurred)):
    for j in range(len(blurred[0])):
        if (i+1 >= height) or (j+1 >= width):
            continue
        if mask[i+1][j+1] == 1:
            blurred[i][j] = original[i+1][j+1]
imsave(guy + "_portrait.ppm", blurred)

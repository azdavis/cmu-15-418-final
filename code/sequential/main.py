from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "elephant"
guy = "img/" + guy

print("prelims")

img = imread(guy + ".jpg").astype(np.int32)
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

imsave(guy + "_walls.jpg", walls)

threshold = 30
def hasColorDiff(color1, color2):
    return (
        abs(color1[0] - color2[0]) +
        abs(color1[1] - color2[1]) +
        abs(color1[2] - color2[2])
    ) > threshold

print("get background")

def getBackgroundColors(image, ranges):
    ret = []
    for xmin, xmax, ymin, ymax in ranges:
        for i in range(ymin, ymax):
            for j in range(xmin, xmax):
                this = image[i][j]
                diff = True
                for ind in range(len(ret)):
                    x = ret[ind]
                    diff = diff and hasColorDiff(this, x[0])
                    if not hasColorDiff(this, x[0]):
                        x[1] += 1
                if diff:
                    ret.append([this, 1])
    return ret

background = getBackgroundColors(
    img,
    [
        (0, ltWall, 0, height),
        (rtWall, width, 0, height),
        (0, width, 0, tpWall)
    ]
)

print("filter background")
# Filter background colors
print background
totalBCPix = ltWall * height + (width - rtWall) * height + tpWall * width
bcThresh = 0.01 * totalBCPix
background = filter(lambda x: x[1] > bcThresh, background)
print background

print("use background")

dude = np.copy(img, True)
mask = np.zeros((height, width))

for i in range(height):
    for j in range(width):
        this = dude[i][j]
        diff = True
        for bc in background:
            diff = diff and hasColorDiff(this, bc[0])
        if diff:
            dude[i][j] = np.array([0,255,0])
            mask[i][j] = 1

imsave(guy + "_predude.jpg", dude)

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

imsave(guy + "_dude.jpg", dude)
# Blur
blurKernel = [[1.0/8, 1.0/8, 1.0/8],
              [1.0/8, 0, 1.0/8],
              [1.0/8, 1.0/8, 1.0/8]
             ]
blurred = np.zeros((height, width, 3))
print np.shape(blurred)
print np.shape(original)

for kY in range(len(blurKernel)):
    for kX in range(len(blurKernel[0])):
        blur = blurKernel[kY][kX]
        if blur = 0:
            continue
        for i in range(len(original)):
            for j in range(len(original[i])):
                if (i + kY >= height) or (j + kX >= width):
                    continue
                if (i + 1 >= height) or (j + 1 >= width):
                    continue
                blurred[i+1][j+1][0] += blur * original[i+kY][j+kX][0]
                blurred[i+1][j+1][1] += blur * original[i+kY][j+kX][1]
                blurred[i+1][j+1][2] += blur * original[i+kY][j+kX][2]

imsave(guy + "_blurred.jpg", blurred)

# Put filter on mask
for i in range(len(blurred)):
    for j in range(len(blurred[0])):
        if (i+1 >= height) or (j+1 >= width):
            continue
        if mask[i+1][j+1] == 1:
            blurred[i][j] = original[i+1][j+1]
imsave(guy + "_portrait.jpg", blurred)

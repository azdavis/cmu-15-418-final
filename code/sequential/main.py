from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "farnam"
guy = "img/" + guy

print("prelims")

img = imread(guy + ".jpg").astype(np.int32)
height, width, _ = np.shape(img)

walls = np.copy(img, True)

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
                for x in ret:
                    diff = diff and hasColorDiff(this, x)
                if diff:
                    ret.append(this)
    return ret

background = getBackgroundColors(
    img,
    [
        (0, ltWall, 0, height),
        (rtWall, width, 0, height),
        (0, width, 0, tpWall)
    ]
)

print("use background")

dude = np.copy(img, True)

for i in range(height):
    for j in range(width):
        this = dude[i][j]
        diff = True
        for bc in background:
            diff = diff and hasColorDiff(this, bc)
        if diff:
            dude[i][j] = np.array([255,0,0])

imsave(guy + "_dude.jpg", dude)

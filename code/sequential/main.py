from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "farnam"
guy = "img/" + guy

img = imread(guy + ".jpg").astype(np.int32)
height, width, _ = np.shape(img)

walls = np.copy(img, True)

wall = 6
leftWall = width / wall
rightWall = (width * (wall - 1)) / wall

for i in range(height):
    walls[i][leftWall] = np.array([255,0,0])
    walls[i][rightWall] = np.array([0,255,0])

imsave(guy + "_walls.jpg", walls)

threshold = 30
def hasColorDiff(color1, color2):
    return (
        abs(color1[0] - color2[0]) +
        abs(color1[1] - color2[1]) +
        abs(color1[2] - color2[2])
    ) > threshold

background = []
for i in range(height):
    for j in range(leftWall):
        this = img[i][j]
        diff = True
        for bc in background:
            diff = diff and hasColorDiff(this, bc)
        if diff:
            background.append(this)

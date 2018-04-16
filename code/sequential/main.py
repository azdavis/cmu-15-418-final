from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "farnam"
guy = "img/" + guy

img = imread(guy + ".jpg")
imgcpy = np.copy(img, True)
print np.shape(img)
(height, width, color) = np.shape(img)

wall = 6
leftWall = width / wall
rightWall = (width * (wall - 1)) / wall

for i in range(height):
    imgcpy[i][leftWall] = np.array([255,0,0])
    imgcpy[i][rightWall] = np.array([0,255,0])

imsave(guy + "_walls.jpg", imgcpy) # See walls

img = img.astype(np.int32) # DEFAULT NUMPY IMAGE IS UINT8
threshold = 30
def hasColorDiff(color1, color2):
    return (abs(color1[0] - color2[0]) +
            abs(color1[1] - color2[1]) +
            abs(color1[2] - color2[2])) > threshold
background = []
# Get color profile of background
for i in range(height):
    for j in range(leftWall):
        color = img[i][j]
        diff = True
        for bc in background:
            diff = diff and hasColorDiff(color, bc)

        if diff:
            background.append(color)

print len(background)
print background

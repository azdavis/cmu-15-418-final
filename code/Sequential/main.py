from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

img = imread("Banana.jpg")

print np.shape(img)
(height, width, color) = np.shape(img)

# Convert to grayscale
grayscale = np.zeros((height, width))

for row in range(height):
    for col in range(width):
        grayscale[row][col] = sum(img[row][col]) / 3



# Blur with box filter, take average of square around center pixel
box_size = 10
blurred = np.zeros((height, width))
for row in range(height):
    for col in range(width):
        total = 0
        count = 0
        for i in range(row - (box_size / 2), row + (box_size / 2)):
            for j in range(col - (box_size / 2), col + (box_size / 2)):
                if (i < 0 or i >= height or j < 0 or j >= width):
                    continue
                count += 1
                total += grayscale[i][j]
        if count == 0:
            count = 1
        blurred[row][col] = (total / count)

# Line Energy
line_energy = blurred


imsave("Banana_blurred.jpg", blurred)
imsave("Banana_segmented.jpg", img)

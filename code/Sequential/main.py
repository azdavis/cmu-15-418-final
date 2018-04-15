from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "Banana"

img = imread(guy + ".jpg")

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

# compute gradient
gradient_kernel = [[0, 1, 0],
                   [1, -4, 1],
                   [0, 1, 0]
                  ]
kernel_size = len(gradient_kernel)
edge_energy = np.zeros((height, width))
for row in range(height):
    for col in range(width):
        total = 0
        for i in range(row - (kernel_size / 2), row + (kernel_size / 2)):
            for j in range(col - (kernel_size / 2), col + (kernel_size / 2)):
                if (i < 0 or i >= height or j < 0 or j >= width):
                    continue
                k_i = (kernel_size/2) + i - row
                k_j = (kernel_size/2) + j - col
                total += blurred[i][j] * gradient_kernel[k_i][k_j]
        edge_energy[row][col] = total

imsave(guy + "_blurred.jpg", blurred)
imsave(guy + "_edge.jpg", edge_energy)
imsave(guy + "_segmented.jpg", img)

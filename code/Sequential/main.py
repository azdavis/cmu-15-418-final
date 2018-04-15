from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

img = imread("Banana.jpg")

print np.shape(img)
(width, height, color) = np.shape(img)

grayscale = np.zeros((width, height))

for row in range(width):
    for col in range(height):
        grayscale[row][col] = sum(img[row][col]) / 3

imsave("Banana_gray.jpg", greyscale)
imsave("Banana_segmented.jpg", img)

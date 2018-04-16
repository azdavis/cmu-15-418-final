from scipy.ndimage import imread
from scipy.misc import imsave
import numpy as np

guy = "farnam"
guy = "img/" + guy

img = imread(guy + ".jpg")
height, width, _ = np.shape(img)
print(height, width)
imsave(guy + "_fella.jpg", img)

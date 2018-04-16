from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "farnam"
guy = "img/" + guy

img = imread(guy + ".jpg")
imgcpy = imread(guy + ".jpg")
print np.shape(img)
(height, width, color) = np.shape(img)

# Convert to grayscale
grayscale = np.zeros((height, width))

for row in range(height):
    for col in range(width):
        grayscale[row][col] = sum(img[row][col]) / 3

# Blur with gaussian filter
box_size = 5
blurred = np.zeros((height, width))
gauss_kernel = [
                   [1, 4, 7, 4, 1],
                   [4, 16, 26, 16, 4],
                   [7, 26, 41, 26, 7],
                   [4, 16, 26, 16, 4],
                   [1, 4, 7, 4, 1]
                  ]
for row in range(height):
    for col in range(width):
        count = 0
        total = 0
        for i_k in range(box_size):
            for j_k in range(box_size):
                weight = gauss_kernel[i_k][j_k]
                i = row - (box_size / 2) + i_k
                j = col - (box_size / 2) + j_k

                if (i < 0 or i >= height or j < 0 or j >= width):
                    continue
                total += weight * grayscale[i][j]
                count += weight
        blurred[row][col] = total / count

# Line Energy
line_energy = blurred

# compute gradient
gradient_kernel = [
                   [0, 0, 1, 0, 0],
                   [0, 0, 2, 0, 0],
                   [1, 2, -12, 2, 1],
                   [0, 0, 2, 0, 0],
                   [0, 0, 1, 0, 0]
                  ]
kernel_size = len(gradient_kernel)
edge_energy = np.zeros((height, width))
for row in range(height):
    for col in range(width):
        total = 0
        dirs = [(-2,0), (-1,0), (2,0), (1,0), (0,1), (0,2), (0,-1), (0,-2)]
        count = 0
        for direction in dirs:
            i = direction[0] + row
            j = direction[1] + col
            i_k = direction[0] + (kernel_size / 2)
            j_k = direction[1] + (kernel_size / 2)
            if (i < 0 or i >= height or j < 0 or j >= width):
                continue
            total += blurred[i][j] * gradient_kernel[i_k][j_k]
            count += gradient_kernel[i_k][j_k]
        total += blurred[row][col] * count * -1
        edge_energy[row][col] = abs(total)

# Energy
total_energy =(edge_energy)
total_energy = np.clip(total_energy, 0, None)
threshold = 60

# Type of point in snake (x, y)
topSnake = []
edgeTopSnakePts = [] # Has all the points for top snake for edges
for i in range(width):
    topSnake.append((i, 0))
    edgeTopSnakePts.append([])
leftSnake = []
edgeLeftSnakePts = [] # Has all the points for left snake for edges
for i in range(height):
    leftSnake.append((0, i))
    edgeLeftSnakePts.append([])

topSnakePts = edgeTopSnakePts
leftSnakePts = edgeLeftSnakePts
topSnakeEnd = height - 1
leftSnakeEnd = width - 1
for i in range(topSnakeEnd):
    for j in range(len(topSnake)):
        point = topSnake[j]
        currentEnergy = total_energy[point[1]][point[0]]
        nextEnergy = total_energy[point[1] + 1][point[0]]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            topSnakePts.append((point[0], point[1]))
            img[point[1]][point[0]] =  np.array([0,255,0])
        topSnake[j] = (point[0], point[1] + 1)

for i in range(leftSnakeEnd):
    for j in range(len(leftSnake)):
        point = leftSnake[j]
        currentEnergy = total_energy[point[1]][point[0]]
        nextEnergy = total_energy[point[1]][point[0] + 1]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            leftSnakePts.append((point[0], point[1]))
            img[point[1]][point[0]] =  np.array([255,0,0])
        leftSnake[j] = (point[0] + 1, point[1])

imsave(guy + "_segmented.jpg", img) # Edge as Energy
imsave(guy + "_energy.jpg", total_energy)

threshold = 10
total_energy = line_energy
img = imgcpy
# Type of point in snake (x, y)
topSnake = []
pixTopSnakePts = [] # Has all the points for top snake for pixels
for i in range(width):
    topSnake.append((i, 0))
    pixTopSnakePts.append([])
leftSnake = []
pixLeftSnakePts = [] # Has all the points for left snake for pixels
for i in range(height):
    leftSnake.append((0, i))
    pixLeftSnakePts.append([])

topSnakePts = pixTopSnakePts
leftSnakePts = pixLeftSnakePts
topSnakeEnd = height - 1
leftSnakeEnd = width - 1
for i in range(topSnakeEnd):
    for j in range(len(topSnake)):
        point = topSnake[j]
        currentEnergy = total_energy[point[1]][point[0]]
        nextEnergy = total_energy[point[1] + 1][point[0]]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            topSnakePts.append((point[0], point[1]))
            img[point[1]][point[0]] =  np.array([0,255,0])
        topSnake[j] = (point[0], point[1] + 1)

for i in range(leftSnakeEnd):
    for j in range(len(leftSnake)):
        point = leftSnake[j]
        currentEnergy = total_energy[point[1]][point[0]]
        nextEnergy = total_energy[point[1]][point[0] + 1]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            leftSnakePts.append((point[0], point[1]))
            img[point[1]][point[0]] =  np.array([255,0,0])
        leftSnake[j] = (point[0] + 1, point[1])

imsave(guy + "_segmented_rough.jpg", img) # Raw Pixel as energy

imsave(guy + "_blurred.jpg", blurred)
imsave(guy + "_edge.jpg", edge_energy)

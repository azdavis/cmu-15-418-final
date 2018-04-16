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



# Blur with box filter, take average of square around center pixel
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
gradient_kernel = [[0, 1, 0],
                   [1, -4, 1],
                   [0, 1, 0]
                  ]
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

# Type of point in snake [(x, y), hasConverged]
topSnake = []
for i in range(width):
    topSnake.append([(i, 0), 0, (i, 0)])
leftSnake = []
rightSnake = []
for i in range(height):
    leftSnake.append([(0, i), 0, (0, i)])
    rightSnake.append([(width-1, i), 0, (width-1,i)])

topSnakeEnd = height - 1
leftSnakeEnd = width - 1
rightSnakeEnd = width - 1
for i in range(topSnakeEnd):
    for j in range(len(topSnake)):
        point = topSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1] + 1][point[0][0]]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            topSnake[j][1] = diff
            topSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([0,255,0])
        topSnake[j][0] = (point[0][0], point[0][1] + 1)

for i in range(leftSnakeEnd):
    for j in range(len(leftSnake)):
        point = leftSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1]][point[0][0] + 1]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            leftSnake[j][1] = diff
            leftSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([255,0,0])
        leftSnake[j][0] = (point[0][0] + 1, point[0][1])

for i in range(rightSnakeEnd):
    for j in range(len(rightSnake)):
        point = rightSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1]][point[0][0] - 1]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            rightSnake[j][1] = diff
            rightSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([0,0,255])
        rightSnake[j][0] = (point[0][0] - 1, point[0][1])

imsave(guy + "_segmented.jpg", img)
imsave(guy + "_energy.jpg", total_energy)
threshold = 10
total_energy = line_energy
img = imgcpy
topSnake = []
for i in range(width):
    topSnake.append([(i, 0), 0, (i, 0)])
leftSnake = []
rightSnake = []
for i in range(height):
    leftSnake.append([(0, i), 0, (0, i)])
    rightSnake.append([(width-1, i), 0, (width-1,i)])

topSnakeEnd = height - 1
leftSnakeEnd = width - 1
rightSnakeEnd = width - 1
for i in range(topSnakeEnd):
    for j in range(len(topSnake)):
        point = topSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1] + 1][point[0][0]]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            topSnake[j][1] = diff
            topSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([0,255,0])
        topSnake[j][0] = (point[0][0], point[0][1] + 1)

for i in range(leftSnakeEnd):
    for j in range(len(leftSnake)):
        point = leftSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1]][point[0][0] + 1]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            leftSnake[j][1] = diff
            leftSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([255,0,0])
        leftSnake[j][0] = (point[0][0] + 1, point[0][1])

for i in range(rightSnakeEnd):
    for j in range(len(rightSnake)):
        point = rightSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1]][point[0][0] - 1]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > threshold):
            rightSnake[j][1] = diff
            rightSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([0,0,255])
        rightSnake[j][0] = (point[0][0] - 1, point[0][1])
imsave(guy + "_segmented_rough.jpg", img)

imsave(guy + "_blurred.jpg", blurred)
imsave(guy + "_edge.jpg", edge_energy)

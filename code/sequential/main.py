from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "large_elephant"
guy = "img/" + guy

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
        dirs = [(-1,0), (1,0), (0,1), (0,-1)]
        count = 0
        for direction in dirs:
            i = direction[0] + row
            j = direction[1] + col
            i_k = direction[0] + (kernel_size / 2)
            j_k = direction[1] + (kernel_size / 2)
            if (i < 0 or i >= height or j < 0 or j >= width):
                continue
            total += blurred[i][j] * gradient_kernel[i_k][j_k]
            count += 1
        total += blurred[row][col] * count * -1
        edge_energy[row][col] = abs(total)

# Energy
total_energy = (-5 * line_energy) + (200 * edge_energy)
threshold = 70

# Type of point in snake [(x, y), hasConverged]
topSnake = []
for i in range(width):
    topSnake.append([(i, 0), 0, (i, 0)])
leftSnake = []
rightSnake = []
for i in range(height):
    leftSnake.append([(0, i), 0, (0, i)])
    rightSnake.append([(width-1, i), 0, (width-1,i)])

topSnakeEnd = height / 2
leftSnakeEnd = width / 2
rightSnakeEnd = width / 2
for i in range(topSnakeEnd):
    for j in range(len(topSnake)):
        point = topSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1] + 1][point[0][0]]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > point[1] and (abs(point[1] - diff) > threshold)):
            topSnake[j][1] = diff
            topSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([0,255,0])
        else:
            topSnake[j][0] = (point[0][0], point[0][1] + 1)

for i in range(leftSnakeEnd):
    for j in range(len(leftSnake)):
        point = leftSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1]][point[0][0] + 1]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > point[1] and (abs(point[1] - diff) > threshold)):
            leftSnake[j][1] = diff
            leftSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([255,0,0])
        else:
            leftSnake[j][0] = (point[0][0] + 1, point[0][1])

for i in range(rightSnakeEnd):
    for j in range(len(rightSnake)):
        point = rightSnake[j]
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1]][point[0][0] - 1]
        diff = abs(nextEnergy - currentEnergy)
        if (diff > point[1] and (abs(point[1] - diff) > threshold)):
            rightSnake[j][1] = diff
            rightSnake[j][2] = (point[0][0], point[0][1])
            img[point[0][1]][point[0][0]] =  np.array([0,0,255])
        else:
            rightSnake[j][0] = (point[0][0] - 1, point[0][1])


for pt in topSnake:

    img[pt[2][1]][pt[2][0]] = np.array([0,255,0])

for pt in leftSnake:

    img[pt[2][1]][pt[2][0]] = np.array([255,0,0])

for pt in rightSnake:

    img[pt[2][1]][pt[2][0]] = np.array([0,0,255])

imsave(guy + "_blurred.jpg", blurred)
imsave(guy + "_energy.jpg", total_energy)
imsave(guy + "_edge.jpg", edge_energy)
imsave(guy + "_segmented.jpg", img)

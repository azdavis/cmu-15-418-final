from scipy.misc import imsave
from scipy.ndimage import imread
import numpy as np

guy = "Banana"
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
box_size = 5
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
total_energy = -1 * line_energy + 100 * edge_energy
threshold = 120

# Type of point in snake [(x, y), hasConverged]
topSnake = []
for i in range(width):
    topSnake.append([(i, 0), False])
leftSnake = []
rightSnake = []
for i in range(height):
    leftSnake.append([(0, i), False])
    rightSnake.append([(width-1, i), False])

for i in range(height-1):
    for j in range(len(topSnake)):
        point = topSnake[j]
        if point[1] == True:
            continue
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1] + 1][point[0][0]]
        if (abs(nextEnergy - currentEnergy) > threshold):
            # Converged
            topSnake[j][1] = True
            #topSnake[j][0] = (point[0][0], point[0][1] + box_size)
        else:
            topSnake[j][0] = (point[0][0], point[0][1] + 1)

for i in range(width-1):
    for j in range(len(leftSnake)):
        point = leftSnake[j]
        if point[1] == True:
            continue
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1]][point[0][0] + 1]
        if (abs(nextEnergy - currentEnergy) > threshold):
            # Converged
            leftSnake[j][1] = True
            #leftSnake[j][0] = (point[0][0] + box_size, point[0][1])
        else:
            leftSnake[j][0] = (point[0][0] + 1, point[0][1])

for i in range(width-1):
    for j in range(len(rightSnake)):
        point = rightSnake[j]
        if point[1] == True:
            continue
        currentEnergy = total_energy[point[0][1]][point[0][0]]
        nextEnergy = total_energy[point[0][1]][point[0][0] - 1]
        if (abs(nextEnergy - currentEnergy) > threshold):
            # Converged
            rightSnake[j][1] = True
            #rightSnake[j][0] = (point[0][0] - box_size, point[0][1])
        else:
            rightSnake[j][0] = (point[0][0] - 1, point[0][1])

for snake in [leftSnake, rightSnake, topSnake]:
    for pt in snake:
        if ((pt[0][1] == height-1) or
            (pt[0][0] == width-1) or
            (pt[0][0] == 0)):
            continue

        img[pt[0][1]][pt[0][0]] = np.array([0,255,0])

imsave(guy + "_blurred.jpg", blurred)
imsave(guy + "_edge.jpg", edge_energy)
imsave(guy + "_segmented.jpg", img)

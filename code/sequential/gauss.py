import math
import numpy as np

width = 100;
height = 100;
a = np.zeros((width, height), dtype=np.float32)

sigma = width / 4;
def gauss(x, y):
    x = float(x)
    y = float(y)
    return ((1 / (2 * math.pi * sigma * sigma)) *
           (math.exp(-1 * (x ** 2 + y ** 2) / (2 * sigma * sigma))))

centerX = width/2
centerY = width/2
for i in range(height):
    for j in range(width):
        x = abs(j - centerX)
        y = abs(i - centerY)
        print x, y
        a[i][j] = gauss(x, y)

np.savetxt("g", a),

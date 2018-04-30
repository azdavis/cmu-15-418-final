import numpy as np
blurKernel = np.zeros((30,30), dtype=np.int8)
for i in range(30) :
    for j in range(30):
        x = (30/2) - j
        y = (30/2) - i
        if (x * x + y * y <= 15 * 15):
            print (x * x + y * y)
            blurKernel[i][j] = 1;

for row in blurKernel:
    print row
np.savetxt("1", blurKernel)

export uniform int func(uniform int x, uniform int y) {
    return x + y + 1;
}

task void blur_task(uniform int width,
                    uniform int height,
                    uniform unsigned int8 imgData[],
                    uniform float blurKernel[],
                    uniform unsigned int8 blurData[],
                    uniform unsigned int8 mask[],
                    uniform int rowsPerTask) {

    uniform int ystart = taskIndex * rowsPerTask;
    uniform int yend = min(ystart + rowsPerTask, height);
    uniform int FILTER_SIZE = 50;

    foreach (row = ystart ... yend, col = 0 ... width) {
        // Foreground Pixel
        if (mask[row * width + col] == 1) {
            continue;
        }
        // BG Pixel
        float count = 0;
        int i_k, j_k;
        float red = 0;
        float green = 0;
        float blue = 0;
        for (i_k = 0; i_k < FILTER_SIZE; i_k++) {
            for (j_k = 0; j_k < FILTER_SIZE; j_k++) {
                float weight = blurKernel[i_k * FILTER_SIZE + j_k];
                int i = row - (FILTER_SIZE / 2) + i_k;
                int j = col - (FILTER_SIZE / 2) + j_k;

                if (i < 0 || i >= height || j < 0 || j >= width) {
                    continue;
                } else if (mask[i * width + j] == 1) {
                    continue;
                }
                red += weight * (imgData[((width * i + j) * 3)]);
                green += weight * (imgData[((width * i + j) * 3) + 1]);
                blue += weight * (imgData[((width * i + j) * 3) + 2]);
                count += weight;
            }
        }
        if (count == 0) {
            continue;
        }
        blurData[(3*(row * width + col))] = (unsigned int8)(red / count);
        blurData[(3*(row * width + col))+1] = (unsigned int8)(green / count);
        blurData[(3*(row * width + col))+2] = (unsigned int8)(blue / count);
    }
}

export void blur(uniform int width,
                 uniform int height,
                 uniform unsigned int8 imgData[],
                 uniform float blurKernel[],
                 uniform unsigned int8 blurData[],
                 uniform unsigned int8 mask[]) {

    uniform int taskNum = height;
    uniform int rowsPerTask = height / taskNum; // 1 row per task
    launch[taskNum] blur_task(width,
                              height,
                              imgData,
                              blurKernel,
                              blurData,
                              mask,
                              rowsPerTask);
}


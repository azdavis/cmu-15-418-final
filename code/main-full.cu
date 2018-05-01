#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include "lib/cycletimer.h"
#include "lib/etc.h"
#include "lib/ppm.h"

#ifdef DEBUG
#define CUDA_CHECK cudaCheck(cudaPeekAtLastError(), __FILE__, __LINE__)
static inline void cudaCheck(cudaError_t code, const char *file, int line) {
    if (code == cudaSuccess) {
        return;
    }
    fprintf(stderr, "%s:%d: %s\n", file, line, cudaGetErrorString(code));
    exit(EXIT_FAILURE);
}
#else
#define CUDA_CHECK ((void) 0)
#endif

static inline __host__ __device__ int div_ceil(int n, int d) {
    return (n + (d - 1)) / d;
}


static inline __device__ int cudaGetBucketIdx(int r, int g, int b) {
    return r * BUCKETS * BUCKETS + g * BUCKETS + b;
}

__global__ void getColorDist(
    int width,
    int height,
    int *color_counts,
    PPMPixel *imgData,
    int ltWall,
    int rtWall,
    int tpWall
) {
    int j = blockIdx.x * blockDim.x + threadIdx.x;
    int i = blockIdx.y * blockDim.y + threadIdx.y;

    if (i >= height || j >= width) {
        return;
    }
    if (j >= ltWall && j < rtWall && i > tpWall) {
        return;
    }

    PPMPixel pt = imgData[i * width + j];
    int bucketIdx = cudaGetBucketIdx(
                    pt.red / BUCKET_SIZE,
                    pt.green / BUCKET_SIZE,
                    pt.blue / BUCKET_SIZE);

    atomicAdd(&color_counts[bucketIdx], 1);
}

__global__ void initMask(
    int width,
    int height,
    char *oldMask,
    int *color_counts,
    PPMPixel *imgData,
    int bcThresh
) {
    int j = blockIdx.x * blockDim.x + threadIdx.x;
    int i = blockIdx.y * blockDim.y + threadIdx.y;

    if (i >= height || j >= width) {
        return;
    }

    PPMPixel pt = imgData[i * width + j];
    unsigned char r = pt.red / BUCKET_SIZE;
    unsigned char g = pt.green / BUCKET_SIZE;
    unsigned char b = pt.blue / BUCKET_SIZE;
    if (color_counts[cudaGetBucketIdx(r, g, b)] < bcThresh) {
        oldMask[i * width + j] = 1;
    }
}

__global__ void buildMask(
    int width,
    int height,
    char *oldMask,
    char *mask
) {

    int j = blockIdx.x * blockDim.x + threadIdx.x;
    int i = blockIdx.y * blockDim.y + threadIdx.y;
    if (i < 2 || j < 2 || i >= height - 2 || j >= width - 2) {
        return;
    }

    __syncthreads();

    // Clean up mask
    char thisPx = oldMask[i * width + j];
    if (thisPx == 0) {
        int borderSum =
            oldMask[(i - 1) * width + j] +
            oldMask[i * width + j - 1] +
            oldMask[(i + 1) * width + j] +
            oldMask[i * width + j + 1] +
            oldMask[(i - 2) * width + j] +
            oldMask[i * width + j - 2] +
            oldMask[(i + 2) * width + j] +
            oldMask[i * width + j + 2];
        if (borderSum >= 2) {
            mask[i * width + j] = 1;
        }
    }
}

__global__ void blur(
    int width,
    int height,
    PPMPixel *imgData,
    float *blurKernel,
    PPMPixel *blurData,
    char *mask
) {

    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int sqIdx = threadIdx.y * SQ_DIM + threadIdx.x;

    // Load Kernel into shared mem
    __shared__ float sharedBlurKernel[FILTER_SIZE * FILTER_SIZE];
    int blurKernelCopyLen = div_ceil(FILTER_SIZE * FILTER_SIZE,
                                    SQ_DIM * SQ_DIM);
    int index;
    for (int ind = 0; ind < blurKernelCopyLen; ind++) {
        index = ind + sqIdx * blurKernelCopyLen;
        if (index >= FILTER_SIZE * FILTER_SIZE) {
            continue;
        }
        sharedBlurKernel[index] = blurKernel[index];
    }

    // Load image into shared memory
    __shared__ PPMPixel sharedImgData[SHARED_IMG_DATA_DIM*SHARED_IMG_DATA_DIM];
    int imgDataCopyLen = div_ceil(SHARED_IMG_DATA_DIM * SHARED_IMG_DATA_DIM,
                                  SQ_DIM * SQ_DIM);

    int imgIndex;
    int rowOffset = blockIdx.y * SQ_DIM - (FILTER_SIZE / 2);
    int colOffset = blockIdx.x * SQ_DIM - (FILTER_SIZE / 2);

    for (int ind = 0; ind < imgDataCopyLen; ind++) {

        index = ind + sqIdx * imgDataCopyLen;
        int imgRow = rowOffset + (index / SHARED_IMG_DATA_DIM);
        int imgCol = colOffset + (index % SHARED_IMG_DATA_DIM);

        imgIndex = imgRow * width + imgCol;
        if (imgRow < 0 || imgCol < 0) {
            continue;
        }
        else if (index < 0 || index >= SHARED_IMG_DATA_DIM * SHARED_IMG_DATA_DIM) {
            continue;
        }
        else if (imgIndex < 0 || imgIndex >= width * height) {
            continue;
        }
        sharedImgData[index] = imgData[imgIndex];
    }

    __syncthreads();

    if (row < 0 || row >= height || col < 0 || col >= width) {
        return;
    }
    if (mask[row * width + col] == 1) {
        return;
    }

    float count = 0;
    int i_k, j_k;
    float red = 0;
    float green = 0;
    float blue = 0;
    for (i_k = 0; i_k < FILTER_SIZE; i_k++){
        for (j_k = 0; j_k < FILTER_SIZE; j_k++){
            float weight = sharedBlurKernel[i_k*FILTER_SIZE + j_k];
            int i = row - (FILTER_SIZE / 2) + i_k;
            int j = col - (FILTER_SIZE / 2) + j_k;

            if (i < 0 || i >= height || j < 0 || j >= width) {
                continue;
            } else if (mask[i * width + j] == 1) {
                continue;
            } else if (i - rowOffset < 0 || i - rowOffset >= SHARED_IMG_DATA_DIM
                       || j - colOffset < 0
                       || j - colOffset >= SHARED_IMG_DATA_DIM) {
                continue;
            }
            PPMPixel pt = sharedImgData[SHARED_IMG_DATA_DIM * (i - rowOffset) + j - colOffset];
            //PPMPixel pt = imgData[width * (i) + j];
            red += weight * (pt.red);
            green += weight * (pt.green);
            blue += weight * (pt.blue);
            count += weight;
        }
    }

    if (count != 0) {
        blurData[row * width + col].red = (unsigned char)(red / count);
        blurData[row * width + col].green = (unsigned char)(green / count);
        blurData[row * width + col].blue = (unsigned char)(blue / count);
    }
}

int main(int argc, char **argv) {
    if (argc != 3) {
        printf("usage: %s <infile> <outfile>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    char *infile = argv[1];
    char *outfile = argv[2];

    double start;

    printf("begin\n");
    start = currentSeconds();

    PPMImage *img = readPPM(infile);
    if (img == NULL) {
        exit(EXIT_FAILURE);
    }

    printf("load image: %lf\n", currentSeconds() - start);
    start = currentSeconds();

    int *color_counts =
        (int *)calloc(BUCKETS * BUCKETS * BUCKETS, sizeof(int));
    char *oldMask =
        (char *)calloc(img->width * img->height, sizeof(char));
    char *mask =
        (char *)calloc(img->width * img->height, sizeof(char));
    float *blurKernel =
        (float *)calloc(FILTER_SIZE * FILTER_SIZE, sizeof(float));
    PPMPixel *blurData =
        (PPMPixel *)calloc(img->width * img->height, sizeof(PPMPixel));

    if (
        color_counts == NULL ||
        oldMask == NULL ||
        mask == NULL ||
        blurKernel == NULL ||
        blurData == NULL
    ) {
        exit(EXIT_FAILURE);
    }

    PPMPixel *cudaImgData;
    cudaMalloc(&cudaImgData, img->width * img->height * sizeof(PPMPixel));
    cudaMemcpy(cudaImgData, img->data,
        img->width * img->height * sizeof(PPMPixel),
        cudaMemcpyHostToDevice);

    PPMPixel *cudaBlurData;
    cudaMalloc(&cudaBlurData, img->width * img->height * sizeof(PPMPixel));
    cudaMemcpy(cudaBlurData, img->data,
        img->width * img->height * sizeof(PPMPixel),
        cudaMemcpyHostToDevice);

    // Even bokeh circle blur
    for (int i = 0; i < FILTER_SIZE; i++) {
        for (int j = 0; j < FILTER_SIZE; j++) {
            int x = (FILTER_SIZE/2) - j;
            int y = (FILTER_SIZE/2) - i;
            if (x * x + y * y < (FILTER_SIZE/2) * (FILTER_SIZE/2)) {
                blurKernel[i * FILTER_SIZE + j] = 1.0;
            }
        }
    }
    float *cudaBlurKernel;
    cudaMalloc(&cudaBlurKernel, FILTER_SIZE * FILTER_SIZE * sizeof(float));
    cudaMemcpy(cudaBlurKernel, blurKernel,
        FILTER_SIZE * FILTER_SIZE * sizeof(float),
        cudaMemcpyHostToDevice);

    int *cudaColorCounts;
    cudaMalloc(&cudaColorCounts, BUCKETS * BUCKETS * BUCKETS * sizeof(int));

    char *cudaOldMask;
    cudaMalloc(&cudaOldMask, img->width * img->height * sizeof(char));

    char *cudaMask;
    cudaMalloc(&cudaMask, img->width * img->height * sizeof(char));

    printf("malloc and cudamalloc and memcpy: %lf\n", currentSeconds() - start);
    start = currentSeconds();
    // Get Walls
    int ltWall = img->width / LTRTWALLDENOM;
    int rtWall = (img->width * (LTRTWALLDENOM - 1)) / LTRTWALLDENOM;
    int tpWall = img->height / TPWALLDENOM;

    // Get color distribution

    cudaMemcpy(cudaColorCounts, color_counts,
        BUCKETS * BUCKETS * BUCKETS * sizeof(int),
        cudaMemcpyHostToDevice);

    // Dims for every pixel
    dim3 threadsPerBlock(SQ_DIM, SQ_DIM);
    dim3 blocks(div_ceil(img->width, SQ_DIM), div_ceil(img->height, SQ_DIM));

    getColorDist<<<blocks, threadsPerBlock>>>(
        img->width,
        img->height,
        cudaColorCounts,
        cudaImgData,
        ltWall,
        rtWall,
        tpWall
    );
    CUDA_CHECK;

    printf("get color_counts: %lf\n", currentSeconds() - start);
    start = currentSeconds();

    int totalBCPix =
        ltWall * img->height +
        (img->width - rtWall) * img->height +
        tpWall * img->width;

    int bcThresh = BCTHRESH_DECIMAL * totalBCPix;

    cudaMemcpy(cudaOldMask, oldMask,
        img->width * img->height * sizeof(char),
        cudaMemcpyHostToDevice);

    initMask<<<blocks, threadsPerBlock>>>(
        img->width,
        img->height,
        cudaOldMask,
        cudaColorCounts,
        cudaImgData,
        bcThresh
    );

    printf("get oldMask: %lf\n", currentSeconds() - start);
    start = currentSeconds();

    cudaMemcpy(cudaMask, cudaOldMask,
        img->width * img->height * sizeof(char),
        cudaMemcpyDeviceToDevice);

    buildMask<<<blocks, threadsPerBlock>>>(
        img->width,
        img->height,
        cudaOldMask,
        cudaMask
    );

    printf("get mask: %lf\n", currentSeconds() - start);
    start = currentSeconds();

    // Blur
    printf("finished mask, starting blur\n");

    blur<<<blocks, threadsPerBlock>>>(
        img->width,
        img->height,
        cudaImgData,
        cudaBlurKernel,
        cudaBlurData,
        cudaMask
    );

    cudaDeviceSynchronize();
    cudaMemcpy(
        blurData,
        cudaBlurData,
        img->width * img->height * sizeof(PPMPixel),
        cudaMemcpyDeviceToHost
    );

    printf("get blurData: %lf\n", currentSeconds() - start);
    start = currentSeconds();

    PPMPixel *oldData = img->data;
    img->data = blurData;

    errno = 0;
    writePPM(outfile, img);
    if (errno != 0) {
        exit(EXIT_FAILURE);
    }
    printf("write image: %lf\n", currentSeconds() - start);

    free(oldData);
    free(color_counts);
    free(blurKernel);
    free(img);
    free(img->data);
    cudaFree(cudaImgData);
    cudaFree(cudaBlurKernel);
    cudaFree(cudaMask);
    cudaFree(cudaOldMask);
    return 0;
}

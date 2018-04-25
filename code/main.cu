#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <string>
#include "lib/ppm.h"
#include "lib/cycletimer.h"

#define LTRTWALLDENOM 7
#define TPWALLDENOM 8
#define BUCKET_SIZE 32
#define COLORS 256
#define BCTHRESH_DECIMAL 0.005
#define FILTER_SIZE 50
#define BUCKETS (COLORS / BUCKET_SIZE)
#define SQ_DIM 32
#define SHARED_IMG_DATA_DIM (FILTER_SIZE + SQ_DIM)

#define CUDA_CHECK cudaCheck(cudaPeekAtLastError(), __FILE__, __LINE__)
static inline void cudaCheck(cudaError_t code, const char *file, int line) {
    if (code == cudaSuccess) {
        return;
    }
    fprintf(stderr, "%s:%d: %s\n", file, line, cudaGetErrorString(code));
    exit(EXIT_FAILURE);
}

typedef struct {
    int xmin, xmax, ymin, ymax;
} range;

static inline __host__ __device__ int div_ceil(int n, int d) {
    return (n + (d - 1)) / d;
}

static int getBucketIdx(int r, int g, int b) {
    return r * BUCKETS * BUCKETS + g * BUCKETS + b;
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
    int rowOffset = blockIdx.x * SQ_DIM - (FILTER_SIZE / 2);
    int colOffset = blockIdx.y * SQ_DIM - (FILTER_SIZE / 2);

    int blockX = blockIdx.x;
    int blockY = blockIdx.y;


    if ((sqIdx == 0) && (blockX == 0) && (blockY == 0)) {
        printf("sqIdx %d blockX %d blockY %d rowOffset %d colOffset %d\n", sqIdx, blockIdx.x, blockIdx.y, rowOffset, colOffset);
        //printf("copy len %d , shared_img_dat_dim %d\n", imgDataCopyLen, SHARED_IMG_DATA_DIM);
    }
    for (int ind = 0; ind < imgDataCopyLen; ind++) {

        index = ind + sqIdx * imgDataCopyLen;
        int imgRow = rowOffset + (index / SHARED_IMG_DATA_DIM);
        int imgCol = colOffset + (index % SHARED_IMG_DATA_DIM);

        imgIndex = imgRow * width + imgCol;
        if (imgRow < 0 || imgCol < 0) {
            continue;
        }
        if (index < 0 || index >= SHARED_IMG_DATA_DIM * SHARED_IMG_DATA_DIM) {
            if (sqIdx == 0 && blockIdx.x == 2 && blockIdx.y == 2) {
                printf("ind %d writing from imgIndex %d to shared index %d\n", ind, imgIndex, index);
            }
            continue;
        }
        if (imgIndex < 0 || imgIndex >= width * height) {
            if (sqIdx == 0 && blockIdx.x == 2 && blockIdx.y == 2) {
                printf("ind %d writing from imgIndex %d to shared index %d\n", ind, imgIndex, index);
            }
            continue;
        }
        sharedImgData[index] = imgData[imgIndex];

        printf("ind %d writing from imgIndex %d to shared index %d blockX %d blockY %d innerRow %d innerCol %d imgRow %d imgCol %d\n", ind, imgIndex, index, blockIdx.x, blockIdx.y, index / SHARED_IMG_DATA_DIM, index % SHARED_IMG_DATA_DIM, imgRow, imgCol);
    }

    __syncthreads();

    if (row < 0 || row >= height || col < 0 || col >= width) {
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

    int deviceCount = 0;
    std::string name;
    cudaError_t err = cudaGetDeviceCount(&deviceCount);

    printf("---------------------------------------------------------\n");
    printf("Initializing CUDA for Portrait Mode\n");
    printf("Found %d CUDA devices\n", deviceCount);

    for (int i = 0; i < deviceCount; i++) {
        cudaDeviceProp deviceProps;
        cudaGetDeviceProperties(&deviceProps, i);
        name = deviceProps.name;

        printf("Device %d: %s\n", i, deviceProps.name);
        printf("   SMs:        %d\n", deviceProps.multiProcessorCount);
        printf("   Global mem: %.0f MB\n",
                     static_cast<float>(deviceProps.totalGlobalMem) / (1024 * 1024));
        printf("   CUDA Cap:   %d.%d\n", deviceProps.major, deviceProps.minor);
    }

    printf("begin\n");
    start = currentSeconds();
    PPMImage *img = readPPM(infile);
    printf("load image: %lf\n", currentSeconds() - start);
    start = currentSeconds();

    int *color_counts = (int *)malloc(BUCKETS * BUCKETS * BUCKETS * sizeof(int));
    char *oldMask = (char *)calloc(img->width * img->height, sizeof(char));
    char *mask = (char *)calloc(img->width * img->height, sizeof(char));
    float *blurKernel =
            (float *)malloc(FILTER_SIZE * FILTER_SIZE * sizeof(float));
    PPMPixel *blurData =
            (PPMPixel *)calloc(img->width * img->height, sizeof(PPMPixel));
    if (
        img == NULL ||
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

    // Even box blur
    for (int i = 0; i < FILTER_SIZE; i++) {
        for (int j = 0; j < FILTER_SIZE; j++) {
            blurKernel[i * FILTER_SIZE + j] = 1.0;
        }
    }
    float *cudaBlurKernel;
    cudaMalloc(&cudaBlurKernel, FILTER_SIZE * FILTER_SIZE * sizeof(float));
    cudaMemcpy(cudaBlurKernel, blurKernel,
        FILTER_SIZE * FILTER_SIZE * sizeof(float),
        cudaMemcpyHostToDevice);

    printf("malloc and cudamalloc and memcpy: %lf\n", currentSeconds() - start);
    start = currentSeconds();
    // Get Walls
    int ltWall = img->width / LTRTWALLDENOM;
    int rtWall = (img->width * (LTRTWALLDENOM - 1)) / LTRTWALLDENOM;
    int tpWall = img->height / TPWALLDENOM;

    // Get color distribution
    range rs[] = {
        {0, ltWall, 0, img->height},
        {rtWall, img->width, 0, img->height},
        {0, img->width, 0, tpWall},
    };

    int i, j, ri;
    for (ri = 0; ri < 3; ri++) {
        range r = rs[ri];
        for (i = r.ymin; i < r.ymax; i++) {
            for (j = r.xmin; j < r.xmax; j++) {
                PPMPixel *pt = getPixel(j, i, img);
                color_counts[
                    getBucketIdx(
                        pt->red / BUCKET_SIZE,
                        pt->green / BUCKET_SIZE,
                        pt->blue / BUCKET_SIZE)
                ] += 1;
            }
        }
    }
    printf("get color_counts: %lf\n", currentSeconds() - start);
    start = currentSeconds();

    int totalBCPix =
        ltWall * img->height +
        (img->width - rtWall) * img->height +
        tpWall * img->width;

    int bcThresh = BCTHRESH_DECIMAL * totalBCPix;

    for (i = 0; i < img->height; i++) {
        for (j = 0; j < img->width; j++) {
            PPMPixel *pt = getPixel(j, i, img);
            unsigned char r = pt->red / BUCKET_SIZE;
            unsigned char g = pt->green / BUCKET_SIZE;
            unsigned char b = pt->blue / BUCKET_SIZE;
            if (color_counts[getBucketIdx(r, g, b)] < bcThresh) {
                oldMask[i * img->width + j] = 1;
            }
        }
    }

    printf("get oldMask: %lf\n", currentSeconds() - start);
    start = currentSeconds();
    memcpy(mask, oldMask, img->width * img->height * sizeof(char));

    // Clean up mask
    for (i = 2; i < img->height - 2; i++) {
        for (j = 2; j < img->width - 2; j++) {
            char thisPx = oldMask[i * img->width + j];
            if (thisPx == 0) {
                int borderSum =
                    oldMask[(i - 1) * img->width + j] +
                    oldMask[i * img->width + j - 1] +
                    oldMask[(i + 1) * img->width + j] +
                    oldMask[i * img->width + j + 1] +
                    oldMask[(i - 2) * img->width + j] +
                    oldMask[i * img->width + j - 2] +
                    oldMask[(i + 2) * img->width + j] +
                    oldMask[i * img->width + j + 2];
                if (borderSum >= 2) {
                    mask[i * img->width + j] = 1;
                }
            }
        }
    }
    printf("get mask: %lf\n", currentSeconds() - start);
    start = currentSeconds();

    // Blur
    printf("finished mask, starting blur\n");
    char *cudaMask;
    cudaMalloc(&cudaMask, img->width * img->height * sizeof(char));
    cudaMemcpy(cudaMask, mask,
        img->width * img->height * sizeof(char),
        cudaMemcpyHostToDevice);

    dim3 threadsPerBlock(SQ_DIM, SQ_DIM);
    dim3 blocks(div_ceil(img->width, SQ_DIM), div_ceil(img->height, SQ_DIM));

    CUDA_CHECK;
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

    // Put filter on mask
    int height = img->height;
    int width = img->width;
    for (i = 0; i < height; i++) {
        for (j = 0; j < width; j++) {
            if (mask[i * width + j] == 1) {
                PPMPixel *pt = getPixel(j, i, img);
                blurData[i * width + j].red = pt->red;
                blurData[i * width + j].green = pt->green;
                blurData[i * width + j].blue = pt->blue;
            }
        }
    }
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
    return 0;
}

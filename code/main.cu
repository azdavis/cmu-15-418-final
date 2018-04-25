#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <string>
#include "ppm.h"

#define RGB_COMPONENT_COLOR 255
#define LTRTWALLDENOM 7
#define TPWALLDENOM 8
#define BUCKET_SIZE 32
#define COLORS 256
#define BCTHRESH_DECIMAL 0.005
#define FILTER_SIZE 50
#define BUCKETS (COLORS / BUCKET_SIZE)
#define SQ_DIM 32

#if 1
#define CUDA_CHECK cudaCheck(cudaPeekAtLastError(), __FILE__, __LINE__)
static inline void cudaCheck(cudaError_t code, const char *file, int line) {
    if (code == cudaSuccess) {
        return;
    }
    fprintf(stderr, "%s:%d: %s\n", file, line, cudaGetErrorString(code));
    exit(EXIT_FAILURE);
}
#else
#define CUDA_CHECK ((void)0)
#endif

typedef struct {
    int xmin, xmax, ymin, ymax;
} range;

static inline __host__ __device__ int div_ceil(int n, int d) {
    return (n + (d - 1)) / d;
}

static int getBucketIdx(int r, int g, int b) {
    return r * BUCKETS * BUCKETS + g * BUCKETS + b;
}

__global__ void blur(int width, int height, PPMPixel *imgData,
                                         float *blurKernel, PPMPixel *blurData, char *mask) {

    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int sqIdx = threadIdx.y * SQ_DIM + threadIdx.x;

    // Load Kernel into shared mem
    __shared__ float sharedBlurKernel[FILTER_SIZE * FILTER_SIZE];
    int blurKernelCopyLen = div_ceil(FILTER_SIZE * FILTER_SIZE,
                                    SQ_DIM * SQ_DIM);
    for (int ind = 0; ind < blurKernelCopyLen; ind++) {
        int index = ind + sqIdx * blurKernelCopyLen;
        if (index >= FILTER_SIZE * FILTER_SIZE) {
            continue;
        }
        sharedBlurKernel[index] = blurKernel[index];
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
            PPMPixel pt = imgData[width * i + j];
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

__host__ int main(int argc, char **argv) {
    if (argc != 3) {
        printf("usage: %s <infile> <outfile>\n", argv[0]);
        return 0;
    }
    char *infile = argv[1];
    char *outfile = argv[2];

    int deviceCount = 0;
    std::string name;
    cudaError_t err = cudaGetDeviceCount(&deviceCount);

    printf("---------------------------------------------------------\n");
    printf("Initializing CUDA for CudaRenderer\n");
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

    PPMImage *img = readPPM(infile);
    if (img == NULL) {
        exit(1);
    }

    int *color_counts = (int *)malloc(BUCKETS * BUCKETS * BUCKETS * sizeof(int));
    if (color_counts == NULL)
        exit(1);
    char *oldMask = (char *)calloc(img->width * img->height, sizeof(char));
    if (oldMask == NULL)
        exit(1);
    char *mask = (char *)calloc(img->width * img->height, sizeof(char));
    if (mask == NULL)
        exit(1);
    float *blurKernel =
            (float *)malloc(FILTER_SIZE * FILTER_SIZE * sizeof(float));
    if (blurKernel == NULL)
        exit(1);
    PPMPixel *blurData =
            (PPMPixel *)calloc(img->width * img->height, sizeof(PPMPixel));
    if (blurData == NULL)
        exit(1);

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
                         FILTER_SIZE * FILTER_SIZE * sizeof(float), cudaMemcpyHostToDevice);

    // Get Walls
    int ltWall = img->width / LTRTWALLDENOM;
    int rtWall = (img->width * (LTRTWALLDENOM - 1)) / LTRTWALLDENOM;
    int tpWall = img->height / TPWALLDENOM;

    // Get color distribution
    range rs[3];
    rs[0].xmin = 0;
    rs[0].xmax = ltWall;
    rs[0].ymin = 0;
    rs[0].ymax = img->height;
    rs[1].xmin = rtWall;
    rs[1].xmax = img->width;
    rs[1].ymin = 0;
    rs[1].ymax = img->height;
    rs[2].xmin = 0;
    rs[2].xmax = img->width;
    rs[2].ymin = 0;
    rs[2].ymax = tpWall;

    int i, j, ri;
    for (ri = 0; ri < 3; ri++) {
        range r = rs[ri];
        for (i = r.ymin; i < r.ymax; i++) {
            for (j = r.xmin; j < r.xmax; j++) {
                PPMPixel *pt = getPixel(j, i, img);
                color_counts[getBucketIdx(pt->red / BUCKET_SIZE,
                                                                    pt->green / BUCKET_SIZE,
                                                                    pt->blue / BUCKET_SIZE)] += 1;
            }
        }
    }

    int totalBCPix = (ltWall * img->height + (img->width - rtWall) * img->height +
                                        tpWall * img->width);
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

    memcpy(mask, oldMask, img->width * img->height * sizeof(char));

    // Clean up mask
    for (i = 2; i < img->height - 2; i++) {
        for (j = 2; j < img->width - 2; j++) {
            char thisPx = oldMask[i * img->width + j];
            if (thisPx == 0) {
                int borderSum = (oldMask[(i - 1) * img->width + j] +
                                                 oldMask[i * img->width + j - 1] +
                                                 oldMask[(i + 1) * img->width + j] +
                                                 oldMask[i * img->width + j + 1] +
                                                 oldMask[(i - 2) * img->width + j] +
                                                 oldMask[i * img->width + j - 2] +
                                                 oldMask[(i + 2) * img->width + j] +
                                                 oldMask[i * img->width + j + 2]);
                if (borderSum >= 2) {
                    mask[i * img->width + j] = 1;
                }
            }
        }
    }

    // Blur
    printf("finished mask, starting blur\n");
    char *cudaMask;
    cudaMalloc(&cudaMask, img->width * img->height * sizeof(char));
    cudaMemcpy(cudaMask, mask, img->width * img->height * sizeof(char),
                         cudaMemcpyHostToDevice);

    dim3 threadsPerBlock(SQ_DIM, SQ_DIM);
    dim3 blocks(div_ceil(img->width, SQ_DIM), div_ceil(img->height, SQ_DIM));

    CUDA_CHECK;
    blur<<<blocks, threadsPerBlock>>>(img->width, img->height, cudaImgData,
                                                                        cudaBlurKernel, cudaBlurData, cudaMask);
    cudaDeviceSynchronize();
    cudaMemcpy(blurData, cudaBlurData,
                         img->width * img->height * sizeof(PPMPixel),
                         cudaMemcpyDeviceToHost);
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

    PPMPixel *oldData = img->data;
    img->data = blurData;

    errno = 0;
    writePPM(outfile, img);
    if (errno != 0) {
        exit(1);
    }

    free(oldData);
    free(color_counts);
    free(blurKernel);
    free(img);
    free(img->data);
    cudaFree(cudaImgData);
    cudaFree(cudaBlurKernel);
    return 0;
}

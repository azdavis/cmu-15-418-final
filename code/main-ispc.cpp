#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include "lib/cycletimer.h"
#include "lib/etc.h"
#include "lib/ppm.h"

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s <infile> <outfile>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    char *infile = argv[1];
    char *outfile = argv[2];

    double start = currentSeconds();

    PPMImage *img = readPPM(infile);
    if (img == NULL) {
        exit(EXIT_FAILURE);
    }
    int W = img->width;
    int H = img->height;

    int ltWall = W / LTRTWALLDENOM;
    int rtWall = (W * (LTRTWALLDENOM - 1)) / LTRTWALLDENOM;
    int tpWall = H / TPWALLDENOM;

    int *color_counts = (int *) calloc(BUCKETS * BUCKETS * BUCKETS, sizeof(int));
    char *oldMask = (char *) calloc(W * H, sizeof(char));
    char *mask = (char *) calloc(W * H, sizeof(char));
    float *blurKernel = (float *) calloc(FILTER_SIZE * FILTER_SIZE, sizeof(float));
    PPMPixel *blurData = (PPMPixel *) calloc(W * H, sizeof(PPMPixel));
    if (color_counts == NULL ||
        oldMask == NULL ||
        mask == NULL ||
        blurKernel == NULL ||
        blurData == NULL) {
        exit(EXIT_FAILURE);
    }

    printf("{\"init\":%lf", currentSeconds() - start);
    start = currentSeconds();

    range rs[] = {
        {0, ltWall, 0, H},
        {rtWall, W, 0, H},
        {0, W, 0, tpWall},
    };

    int i, j, ri;
    for (ri = 0; ri < 3; ri++) {
        range r = rs[ri];
        for (i = r.ymin; i < r.ymax; i++) {
            for (j = r.xmin; j < r.xmax; j++) {
                PPMPixel *pt = getPixel(j, i, img);
                int idx = getBucketIdx(
                        pt->red / BUCKET_SIZE,
                        pt->green / BUCKET_SIZE,
                        pt->blue / BUCKET_SIZE);
                color_counts[idx] += 1;
            }
        }
    }

    printf(",\"color_counts\":%lf", currentSeconds() - start);
    start = currentSeconds();

    int totalBCPix =
        ltWall * H +
        (W - rtWall) * H +
        tpWall * W;

    int bcThresh = BCTHRESH_DECIMAL * totalBCPix;

    #pragma omp parallel for shared(i) private(j)
    for (i = 0; i < H; i++) {
        for (j = 0; j < W; j++) {
            PPMPixel *pt = getPixel(j, i, img);
            unsigned char r = pt->red / BUCKET_SIZE;
            unsigned char g = pt->green / BUCKET_SIZE;
            unsigned char b = pt->blue / BUCKET_SIZE;
            if (color_counts[getBucketIdx(r, g, b)] < bcThresh) {
                oldMask[i * W + j] = 1;
            }
        }
    }

    printf(",\"build_mask\":%lf", currentSeconds() - start);
    start = currentSeconds();

    memcpy(mask, oldMask, W * H * sizeof(char));

    #pragma omp parallel for shared(i) private(j)
    for (i = 2; i < H - 2; i++) {
        for (j = 2; j < W - 2; j++) {
            char cur = oldMask[i * W + j];
            if (cur == 0) {
                int borderSum =
                    oldMask[(i - 1) * W + j] +
                    oldMask[i * W + j - 1] +
                    oldMask[(i + 1) * W + j] +
                    oldMask[i * W + j + 1] +
                    oldMask[(i - 2) * W + j] +
                    oldMask[i * W + j - 2] +
                    oldMask[(i + 2) * W + j] +
                    oldMask[i * W + j + 2];
                if (borderSum >= 2) {
                    mask[i * W + j] = 1;
                }
            }
        }
    }

    printf(",\"refine_mask\":%lf", currentSeconds() - start);
    start = currentSeconds();

    #pragma omp parallel for shared(i) private(j)
    for (i = 0; i < FILTER_SIZE; i++) {
        for (j = 0; j < FILTER_SIZE; j++) {
            int x = (FILTER_SIZE/2) - j;
            int y = (FILTER_SIZE/2) - i;
            if (x * x + y * y < (FILTER_SIZE/2) * (FILTER_SIZE/2)) {
                blurKernel[i * FILTER_SIZE + j] = 1.0;
            }
        }
    }

    int row, col;
    #pragma omp parallel for schedule(dynamic) shared(row) private(col)
    for (row = 0; row < H; row++) {
        for (col = 0; col < W; col++) {
            // Foreground Pixel
            if (mask[row * W + col] == 1) {
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

                    if (i < 0 || i >= H || j < 0 || j >= W) {
                        continue;
                    } else if (mask[i * W + j] == 1) {
                        continue;
                    }
                    PPMPixel *pt = getPixel(j, i, img);
                    red += weight * (pt->red);
                    green += weight * (pt->green);
                    blue += weight * (pt->blue);
                    count += weight;
                }
            }
            if (count == 0) {
                continue;
            }
            blurData[row * W + col].red = (unsigned char)(red / count);
            blurData[row * W + col].green = (unsigned char)(green / count);
            blurData[row * W + col].blue = (unsigned char)(blue / count);
        }
    }

    #pragma omp parallel for shared(i) private(j)
    for (i = 0; i < H; i++) {
        for (j = 0; j < W; j++) {
            if (mask[i * W + j] == 1) {
                PPMPixel *pt = getPixel(j, i, img);
                blurData[i * W + j].red = pt->red;
                blurData[i * W + j].green = pt->green;
                blurData[i * W + j].blue = pt->blue;
            }
        }
    }

    PPMPixel *oldData = img->data;
    img->data = blurData;

    printf(",\"blur\":%lf", currentSeconds() - start);
    start = currentSeconds();

    errno = 0;
    writePPM(outfile, img);
    if (errno != 0) {
        exit(EXIT_FAILURE);
    }

    free(oldData);
    free(color_counts);
    free(blurKernel);
    free(img);
    free(img->data);
    printf(",\"clean_up\":%lf}", currentSeconds() - start);
    return 0;
}

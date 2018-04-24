#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <string>

#define RGB_COMPONENT_COLOR 255
#define LTRTWALLDENOM 7
#define TPWALLDENOM 8
#define BUCKET_SIZE 32
#define COLORS 256
#define BCTHRESH_DECIMAL 0.005
#define FILTER_SIZE 50
#define BUCKETS (COLORS / BUCKET_SIZE)

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
#define CUDA_CHECK ((void) 0)
#endif


typedef struct {
     int xmin, xmax, ymin, ymax;
} range;

// PPM reading writing code guided from:
// https://stackoverflow.com/questions/2693631/read-ppm-file-and-store-it-in-an-array-coded-with-c

typedef struct {
     unsigned char red,green,blue;
} PPMPixel;

typedef struct {
     int width, height;
     PPMPixel *data;
} PPMImage;

static PPMImage *readPPM(const char *filename)
{
    char buff[16];
    PPMImage *img;
    FILE *fp;
    int c, rgb_comp_color;
    //open PPM file for reading
    fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "Unable to open file '%s'\n", filename);
        exit(1);
    }

    //read image format
    if (!fgets(buff, sizeof(buff), fp)) {
      perror(filename);
      exit(1);
    }

    //check the image format
    if (buff[0] != 'P' || buff[1] != '6') {
        fprintf(stderr, "Invalid image format (must be 'P6')\n");
        exit(1);
    }

    //alloc memory form image
    img = (PPMImage *)malloc(sizeof(PPMImage));
    if (!img) {
         fprintf(stderr, "Unable to allocate memory\n");
         exit(1);
    }

    //check for comments
    c = getc(fp);
    while (c == '#') {
    while (getc(fp) != '\n') ;
         c = getc(fp);
    }

    ungetc(c, fp);
    //read image size information
    if (fscanf(fp, "%d %d", &img->width, &img->height) != 2) {
         fprintf(stderr, "Invalid image size (error loading '%s')\n", filename);
         exit(1);
    }

    //read rgb component
    if (fscanf(fp, "%d", &rgb_comp_color) != 1) {
         fprintf(stderr, "Invalid rgb component (error loading '%s')\n", filename);
         exit(1);
    }

    //check rgb component depth
    if (rgb_comp_color!= RGB_COMPONENT_COLOR) {
         fprintf(stderr, "'%s' does not have 8-bits components\n", filename);
         exit(1);
    }

    while (fgetc(fp) != '\n') ;
    //memory allocation for pixel data
    img->data = (PPMPixel*)malloc(img->width * img->height * sizeof(PPMPixel));

    if (!img) {
         fprintf(stderr, "Unable to allocate memory\n");
         exit(1);
    }

    //read pixel data from file
    if (fread(img->data, 3 * img->width, img->height, fp) != img->height) {
         fprintf(stderr, "Error loading image '%s'\n", filename);
         exit(1);
    }

    fclose(fp);
    return img;
}

void writePPM(const char *filename, PPMImage *img)
{
    FILE *fp;
    //open file for output
    fp = fopen(filename, "wb");
    if (!fp) {
         fprintf(stderr, "Unable to open file '%s'\n", filename);
         exit(1);
    }

    //write the header file
    //image format
    fprintf(fp, "P6\n");

    //image size
    fprintf(fp, "%d %d\n",img->width,img->height);

    // rgb component depth
    fprintf(fp, "%d\n",RGB_COMPONENT_COLOR);

    // pixel data
    fwrite(img->data, 3 * img->width, img->height, fp);
    fclose(fp);
}

static PPMPixel* getPixel(int x, int y, PPMImage *img)
{
    return &(img->data[x + y * img->width]);
}

static void setPixel(int x, int y, PPMImage *img,
                     unsigned char R, unsigned char G, unsigned char B)
{
    img->data[x + y * img->width].red = R;
    img->data[x + y * img->width].green = G;
    img->data[x + y * img->width].blue = B;
}

static int getBucketIdx(int r, int g, int b)
{
    return r * BUCKETS * BUCKETS + g * BUCKETS + b;
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

    for (int i=0; i<deviceCount; i++) {
        cudaDeviceProp deviceProps;
        cudaGetDeviceProperties(&deviceProps, i);
        name = deviceProps.name;

        printf("Device %d: %s\n", i, deviceProps.name);
        printf("   SMs:        %d\n", deviceProps.multiProcessorCount);
        printf(
            "   Global mem: %.0f MB\n",
            static_cast<float>(deviceProps.totalGlobalMem) / (1024 * 1024)
        );
        printf("   CUDA Cap:   %d.%d\n", deviceProps.major, deviceProps.minor);
    }

    PPMImage *img = readPPM(infile);

    int *color_counts = (int*) malloc(BUCKETS * BUCKETS * BUCKETS * sizeof(int));
    if (color_counts == NULL)
        exit(1);
    char *oldMask = (char*) calloc(img->width * img->height, sizeof(char));
    if (oldMask == NULL)
        exit(1);
    char *mask = (char*) calloc(img->width * img->height, sizeof(char));
    if (mask == NULL)
        exit(1);
    float *blurKernel = (float*) malloc(FILTER_SIZE * FILTER_SIZE * sizeof(float));
    if (blurKernel == NULL)
        exit(1);
    PPMPixel *blurData = (PPMPixel*) calloc(img->width * img->height, sizeof(PPMPixel));
    if (blurData == NULL)
        exit(1);

    PPMPixel *cudaImgData;
    cudaMalloc(&cudaImgData, img->width * img->height * sizeof(PPMPixel));
    cudaMemcpy(cudaImgData,
               img->data,
               img->width * img->height * sizeof(PPMPixel),
               cudaMemcpyHostToDevice
    );

    float *cudaBlurKernel;
    cudaMalloc(&cudaBlurKernel, FILTER_SIZE * FILTER_SIZE * sizeof(float));
    cudaMemcpy(cudaBlurKernel,
               blurKernel,
               FILTER_SIZE * FILTER_SIZE * sizeof(float),
               cudaMemcpyHostToDevice
    );

    // Get Walls
    int ltWall = img->width / LTRTWALLDENOM;
    int rtWall = (img->width * (LTRTWALLDENOM - 1)) / LTRTWALLDENOM;
    int tpWall = img->height / TPWALLDENOM;

    // Get color distribution
    range rs[3];
    rs[0].xmin = 0; rs[0].xmax = ltWall;
    rs[0].ymin = 0; rs[0].ymax = img->height;
    rs[1].xmin = rtWall; rs[1].xmax = img->width;
    rs[1].ymin = 0; rs[1].ymax = img->height;
    rs[2].xmin = 0; rs[2].xmax = img->width;
    rs[2].ymin = 0; rs[2].ymax = tpWall;

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

    int totalBCPix = (ltWall * img->height +
                     (img->width - rtWall) * img->height +
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
    for (i = 2; i < img->height-2; i++) {
        for (j = 2; j < img->width-2; j++) {
            char thisPx = oldMask[i * img->width + j];
            if (thisPx == 0) {
                int borderSum = (oldMask[(i-1) * img->width + j] +
                                 oldMask[i * img->width + j-1] +
                                 oldMask[(i+1) * img->width + j] +
                                 oldMask[i * img->width + j+1] +
                                 oldMask[(i-2) * img->width + j] +
                                 oldMask[i * img->width + j-2] +
                                 oldMask[(i+2) * img->width + j] +
                                 oldMask[i * img->width + j+2]);
                if (borderSum >= 2) {
                   mask[i * img->width + j] = 1;
                }
            }
        }
    }

    // Blur
    printf("finished mask, starting blur\n");
    // Even box blur
    for (i = 0; i < FILTER_SIZE; i++) {
        for (j = 0; j < FILTER_SIZE; j++) {
            blurKernel[i * FILTER_SIZE + j] = 1.0;
        }
    }

    int width = img->width;
    int height = img->height;
    int row, col;
    for (row = 0; row < height; row++) {
        if (row % 100 == 0) {
            printf("finished row %d\n", row);
        }
        for (col = 0; col < width; col++) {
            float count = 0;
            int i_k, j_k;
            float red = 0;
            float green = 0;
            float blue = 0;
            for (i_k = 0; i_k < FILTER_SIZE; i_k++){
                for (j_k = 0; j_k < FILTER_SIZE; j_k++){
                    float weight = blurKernel[i_k*FILTER_SIZE + j_k];
                    int i = row - (FILTER_SIZE / 2) + i_k;
                    int j = col - (FILTER_SIZE / 2) + j_k;

                    if (i < 0 || i >= height || j < 0 || j >= width) {
                        continue;
                    }
                    else if (mask[i * width + j] == 1) {
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

            blurData[row*width + col].red = (unsigned char) (red / count);
            blurData[row*width + col].green = (unsigned char) (green / count);
            blurData[row*width + col].blue = (unsigned char) (blue / count);
        }
    }
    // Put filter on mask
    for (i = 0; i < height; i++) {
        for (j = 0; j < width; j++) {
            if (mask[i*width + j] == 1) {
                PPMPixel *pt = getPixel(j, i, img);
                blurData[i*width + j].red = pt->red;
                blurData[i*width + j].green = pt->green;
                blurData[i*width + j].blue = pt->blue;
            }
        }
    }

    PPMPixel *oldData = img->data;
    img->data = blurData;

    writePPM(outfile, img);

    free(oldData);
    free(color_counts);
    free(blurKernel);
    free(img);
    free(img->data);
    cudaFree(cudaImgData);
    cudaFree(cudaBlurKernel);
    return 0;
}

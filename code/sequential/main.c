#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RGB_COMPONENT_COLOR 255
#define LTRTWALLDENOM 7
#define TPWALLDENOM 8
#define BUCKET_SIZE 32
#define COLORS 256
#define BCTHRESH_DECIMAL 0.005
#define FILTER_SIZE 11

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
    int buckets = COLORS / BUCKET_SIZE;
    return r * buckets * buckets + g * buckets + b;
}

int main(void) {

    // Initializtion
    PPMImage *img;
    char base[100] = "img/";
    char guy[100];
    strcat(base, "elephant2");

    strcpy(guy, base);
    strcat(guy, ".ppm");
    img = readPPM(guy);

    // Get Walls
    int ltWall = img->width / LTRTWALLDENOM;
    int rtWall = (img->width * (LTRTWALLDENOM - 1)) / LTRTWALLDENOM;
    int tpWall = img->height / TPWALLDENOM;

    // Get color distribution
    int buckets = COLORS / BUCKET_SIZE;
    int *color_counts = malloc(buckets * buckets * buckets * sizeof(int));
    if (color_counts == NULL)
        exit(1);

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

    char *oldMask = calloc(img->width * img->height, sizeof(char));
    if (oldMask == NULL)
        exit(1);

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

    char *mask = calloc(img->width * img->height, sizeof(char));
    if (mask == NULL)
        exit(1);
    memcpy(mask, oldMask, img->width * img->height * sizeof(char));

    // Clean up mask
    for (i = 2; i < img->height-2; i++) {
        for (j = 2; j < img->width-2; j++) {
            char this = oldMask[i * img->width + j];
            if (this == 0) {
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
    float *blurKernel = malloc(FILTER_SIZE * FILTER_SIZE * sizeof(float));
    if (blurKernel == NULL)
        exit(1);
    // Even box blur
    for (i = 0; i < FILTER_SIZE; i++) {
        for (j = 0; j < FILTER_SIZE; j++) {
            mask[i * FILTER_SIZE + j] = 1.0;
        }
    }

    PPMPixel *blurData = malloc(img->width * img->height * sizeof(PPMPixel));
    if (blurData == NULL)
        exit(1);

    int width = img->width;
    int height = img->height;
    int row, col;
    for (row = 0; row < height; row++) {
        for (col = 0; col < width; col++) {
            float count = 0;
            int i_k, j_k;
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
                    blurData[row*width + col].red += (weight *
                                                    (getPixel(j, i, img))->red);
                    blurData[row*width + col].green += (weight *
                                                  (getPixel(j, i, img))->green);
                    blurData[row*width + col].blue += (weight *
                                                   (getPixel(j, i, img))->blue);
                    count += weight;
                }
            }
            if (count == 0) {
                continue;
            }
            blurData[row*width + col].red /= count;
            blurData[row*width + col].green /= count;
            blurData[row*width + col].blue /= count;
        }
    }
    PPMPixel *oldData = img->data;
    img->data = blurData;
    free(oldData);

    strcpy(guy, base);
    strcat(guy, "_blurred.ppm");
    writePPM(guy, img);

    free(color_counts);
    free(blurKernel);
    free(img);
    free(img->data);
    return 0;
}

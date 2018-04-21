#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RGB_COMPONENT_COLOR 255
#define LTRTWALLDENOM 7
#define TPWALLDENOM 8
#define BUCKETSIZE 32
#define COLORS 256

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
    int buckets = COLORS / BUCKETSIZE
    return r * buckets * buckets + g * buckets + b;
}


int main(void) {

    // Initializion
    PPMImage *img;
    char base[100] = "img/";
    char guy[100];
    strcat(base, "elephant2");

    strcpy(guy, base);
    strcat(guy, ".ppm");
    img = readPPM(guy);

    int ltWall = img->width / LTRTWALLDENOM;
    int rtWall = (img->width * (LTRTWALLDENOM - 1)) / LTRTWALLDENOM;
    int tpWall = img->height / TPWALLDENOM;

    int i, j;
    for (i = 0; i < img->height; i++) {
        setPixel(ltWall, i, img, 255, 0, 0);
        setPixel(rtWall, i, img, 0, 255, 0);
    }

    for (j = 0; j < img->width; j++) {
        setPixel(j, tpWall, img, 0, 0, 255);
    }
    strcpy(guy, base);
    strcat(guy, "_walls.ppm");
    writePPM(guy, img);
    return 0;
}

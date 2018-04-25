#include <stdio.h>
#include <stdlib.h>
#include "ppm.h"

// https://stackoverflow.com/questions/2693631

PPMImage *readPPM(const char *fname) {
    char buff[16];
    PPMImage *img;
    FILE *fp;
    int c, rgb_comp_color;
    fp = fopen(fname, "rb");
    if (!fp) {
        fprintf(stderr, "Unable to open file '%s'\n", fname);
        return NULL;
    }

    if (!fgets(buff, sizeof(buff), fp)) {
        perror(fname);
        return NULL;
    }

    if (buff[0] != 'P' || buff[1] != '6') {
        fprintf(stderr, "Invalid image format (must be 'P6')\n");
        return NULL;
    }

    img = (PPMImage *)malloc(sizeof(PPMImage));
    if (!img) {
        fprintf(stderr, "Unable to allocate memory\n");
        return NULL;
    }

    c = getc(fp);
    while (c == '#') {
        while (getc(fp) != '\n') {}
        c = getc(fp);
    }

    ungetc(c, fp);
    if (fscanf(fp, "%d %d", &img->width, &img->height) != 2) {
        fprintf(stderr, "Invalid image size (error loading '%s')\n", fname);
        return NULL;
    }

    if (fscanf(fp, "%d", &rgb_comp_color) != 1) {
        fprintf(stderr, "Invalid rgb component (error loading '%s')\n", fname);
        return NULL;
    }

    if (rgb_comp_color != RGB_COMPONENT_COLOR) {
        fprintf(stderr, "'%s' does not have 8-bits components\n", fname);
        return NULL;
    }

    while (fgetc(fp) != '\n') {}
    img->data = (PPMPixel *)malloc(img->width * img->height * sizeof(PPMPixel));

    if (!img) {
        fprintf(stderr, "Unable to allocate memory\n");
        return NULL;
    }

    if (fread(img->data, 3 * img->width, img->height, fp) != img->height) {
        fprintf(stderr, "Error loading image '%s'\n", fname);
        return NULL;
    }

    fclose(fp);
    return img;
}

void writePPM(const char *fname, PPMImage *img) {
    FILE *fp;
    fp = fopen(fname, "wb");
    if (!fp) {
        fprintf(stderr, "Unable to open file '%s'\n", fname);
        return;
    }
    fprintf(fp, "P6\n");
    fprintf(fp, "%d %d\n", img->width, img->height);
    fprintf(fp, "%d\n", RGB_COMPONENT_COLOR);
    fwrite(img->data, 3 * img->width, img->height, fp);
    fclose(fp);
}

PPMPixel *getPixel(int x, int y, PPMImage *img) {
    return &(img->data[x + y * img->width]);
}

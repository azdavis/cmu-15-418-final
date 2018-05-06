#ifndef PPM_H
#define PPM_H

#define RGB_COMPONENT_COLOR 255

typedef struct {
    unsigned char red, green, blue;
} PPMPixel;

typedef struct {
    int width, height;
    PPMPixel *data;
} PPMImage;

PPMImage *readPPM(const char *filename);
void writePPM(const char *filename, PPMImage *img);
PPMPixel *getPixel(int x, int y, PPMImage *img);

#endif

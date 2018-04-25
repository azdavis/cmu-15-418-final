#ifndef PPM_H
#define PPM_H

#ifdef __cplusplus
extern "C" {
#endif

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
void setPixel(int x, int y, PPMImage *img, unsigned char R,
    unsigned char G, unsigned char B);

#ifdef __cplusplus
}
#endif

#endif

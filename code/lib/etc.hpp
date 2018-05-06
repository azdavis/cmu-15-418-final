#ifndef ETC_H
#define ETC_H

#ifdef __cplusplus
extern "C" {
#endif

#define LTRTWALLDENOM 7
#define TPWALLDENOM 8
#define BUCKET_SIZE 32
#define COLORS 256
#define BCTHRESH_DECIMAL 0.005
#define FILTER_SIZE 50
#define BUCKETS (COLORS / BUCKET_SIZE)
#define SQ_DIM 32
#define SHARED_IMG_DATA_DIM (FILTER_SIZE + SQ_DIM)

typedef struct {
    int xmin, xmax, ymin, ymax;
} range;

int getBucketIdx(int r, int g, int b);

#ifdef __cplusplus
}
#endif

#endif

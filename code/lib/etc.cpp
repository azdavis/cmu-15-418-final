#include "etc.hpp"

int getBucketIdx(int r, int g, int b) {
    return r * BUCKETS * BUCKETS + g * BUCKETS + b;
}

#!/bin/sh

set -efu

make main-c main-cu

for image in large_elephant.ppm; do
    time ./main-c img/$image 1
    time ./main-cu img/$image 2
    if cmp 1 2; then
        echo "Results match: $image"
    else
        echo "Results differ: $image"
    fi
    rm 1 2
done

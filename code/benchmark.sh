#!/bin/sh

set -efux

make main-c main-cu

for image in large_elephant.ppm; do
    time ./main-c img/$image c.ppm
    time ./main-cu img/$image cu.ppm
    if cmp c.ppm cu.ppm; then
        echo "Results match: $image"
        rm c.ppm cu.ppm
    else
        echo "Results differ: $image"
    fi
done

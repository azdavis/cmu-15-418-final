#!/bin/sh

set -efux

for image in elephant.ppm; do
    time ./main-c img/$image c.ppm
    time ./main-cu img/$image cu.ppm
    time ./main-omp img/$image omp.ppm
    if cmp c.ppm cu.ppm && cmp c.ppm omp.ppm; then
        echo "Results match: $image"
        rm c.ppm cu.ppm omp.ppm
    else
        echo "Results differ: $image"
    fi
done

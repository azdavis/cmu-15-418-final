#!/bin/sh

set -efu

if [ $# -ne 1 ]; then
    echo "usage: $0 <infile>"
    exit 1
fi

time ./main-c $1 c.ppm
time ./main-cu $1 cu.ppm
time ./main-omp $1 omp.ppm
time ./main-full-cu $1 full-cu.ppm
if cmp c.ppm cu.ppm && cmp c.ppm omp.ppm && cmp c.ppm full-cu.ppm; then
    echo "Results match: $1"
    rm c.ppm cu.ppm omp.ppm
else
    echo "Results differ: $1"
fi

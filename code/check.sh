#!/bin/sh

set -efu

if [ $# -ne 1 ]; then
    echo "usage: $0 <infile>"
    exit 1
fi

for x in c cu omp ispc; do
    ./main-$x $1 $x.ppm
    if [ $x = c ]; then
        continue
    fi
    if cmp c.ppm $x.ppm; then
        echo "Results for '$x' on '$1' match"
        rm $x.ppm
    else
        echo "Results for '$x' on '$1' differ"
        exit 1
    fi
done

rm c.ppm

#!/bin/sh

set -efu

if [ $# -ne 1 ]; then
    echo "usage: $0 <infile>"
    exit 1
fi

for x in cpp cu omp ispc; do
    ./main-$x $1 $x.ppm >/dev/null
    if [ $x = cpp ]; then
        continue
    fi
    if cmp cpp.ppm $x.ppm; then
        echo "Results for '$x' on '$1' match"
        rm $x.ppm
    else
        echo "Results for '$x' on '$1' differ"
        exit 1
    fi
done

rm cpp.ppm

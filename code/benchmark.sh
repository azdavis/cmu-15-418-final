set -efu

make main-c main-cu

for image in elephant.ppm; do
    time ./main-c img/$image -o 1
    time ./main-cu img/$image -o 2
    if cmp 1 2; then
        echo "Results match: $image"
    else
        echo "Results differ: $image"
    fi
done

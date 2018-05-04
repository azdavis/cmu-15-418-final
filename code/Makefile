CC = gcc
CFLAGS = -Wall -O3 -Wno-unknown-pragmas
OMPFLAGS = -fopenmp -DOMP
CUDAC = nvcc
CUDAFLAGS = -O3 -DCUDA -m64 --gpu-architecture compute_61
ISPC = /usr/local/depot/ispc-v1.9.1-linux/ispc
ISPFLAGS = -O3 --target=avx1-i32x8 --arch=x86-64
OBJS = lib/cycletimer.o lib/ppm.o lib/etc.o

.PHONY: all help clean regress benchmark results

all: main-c main-omp main-cu test ## make all 4 implementations

help: ## show this help
	@grep -F '##' Makefile | grep -Fv '@grep' | sed -E 's/:.*##/:/'

clean: ## rm all generated files
	rm -rf main-c main-omp main-cu main-ispc lib/*.o

regress: all ## check all implementations have the same output on a small test case
	./check.sh img/elephant.ppm

benchmark: all ## same as regress, but a larger test case
	./check.sh img/large_elephant.ppm

results: all ## run each implementation a few times for each image, summarize results in LaTeX tables
	./results.py

main-c: main.c $(OBJS) ## the sequential C implementation
	$(CC) $(CFLAGS) -o $@ $^

main-omp: main.c $(OBJS) ## the C implementation with OMP on
	$(CC) $(CFLAGS) $(OMPFLAGS) -o $@ $^

main-cu: main.cu $(OBJS) ## the CUDA implementation
	$(CUDAC) $(CUDAFLAGS) -o $@ $^

test: test.c lib/test_ispc.o lib/test_ispc.h
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c %.h
	$(CC) $(CFLAGS) -c -o $@ $<

%_ispc.o %_ispc.h: %.ispc
	$(ISPC) $(ISPFLAGS) -o $*_ispc.o -h $*_ispc.h $^

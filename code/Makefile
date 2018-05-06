CC = gcc
CFLAGS = -Wall -O3 -Wno-unknown-pragmas
OMPFLAGS = -fopenmp -DOMP
CUDAC = nvcc
CUDAFLAGS = -O3 -DCUDA -m64 --gpu-architecture compute_61
OBJS = lib/cycletimer.o lib/ppm.o lib/etc.o

.PHONY: all help clean regress benchmark results

all: main-c main-omp main-cu ## make all 3 implementations

help: ## show this help
	@grep -F '##' Makefile | grep -Fv '@grep' | sed -E 's/:.*##/:/'

clean: ## rm all generated files
	rm -rf main-c main-omp main-cu lib/*.o

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

%.o: %.c %.h
	$(CC) $(CFLAGS) -c -o $@ $<

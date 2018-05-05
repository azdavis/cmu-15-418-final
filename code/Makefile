CC = gcc
CFLAGS = -Wall -O3 -Wno-unknown-pragmas
OMPFLAGS = -fopenmp -DOMP
CUDAC = nvcc
CUDAFLAGS = -O3 -DCUDA -m64 --gpu-architecture compute_61
OBJS = lib/cycletimer.o lib/ppm.o lib/etc.o

.PHONY: all clean regress benchmark results

all: main-c main-omp main-cu

clean:
	rm -rf main-c main-omp main-cu lib/*.o

regress: all
	./check.sh img/elephant.ppm

benchmark: all
	./check.sh img/large_elephant.ppm

results: all
	./results.py

main-c: main.c $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

main-omp: main.c $(OBJS)
	$(CC) $(CFLAGS) $(OMPFLAGS) -o $@ $^

main-cu: main.cu $(OBJS)
	$(CUDAC) $(CUDAFLAGS) -o $@ $^

%.o: %.c %.h
	$(CC) $(CFLAGS) -c -o $@ $<

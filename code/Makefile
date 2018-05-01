CC = cc
CFLAGS = -Wall -O3
OMPFLAGS = -fopenmp -DOMP
CUDAC = nvcc
CUDAFLAGS = -O3 -DCUDA -m64 --gpu-architecture compute_61
OBJS = lib/cycletimer.o lib/ppm.o lib/etc.o

.PHONY: all clean

all: main-c main-omp main-cu main-full-cu

clean:
	rm -rf main-c main-omp main-cu main-full-cu lib/*.o

main-c: main.c $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

main-omp: main.c $(OBJS)
	$(CC) $(CFLAGS) $(OMPFLAGS) -o $@ $^

main-cu: main.cu $(OBJS)
	$(CUDAC) $(CUDAFLAGS) -o $@ $^

main-full-cu: main-full.cu $(OBJS)
	$(CUDAC) $(CUDAFLAGS) -o $@ $^

%.o: %.c %.h
	$(CC) $(CFLAGS) -c -o $@ $<

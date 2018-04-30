CC = cc
CFLAGS = -Wall -O3
OMPFLAGS = -fopenmp -DOMP
CUDAC = nvcc
CUDAFLAGS = -O3 -m64 --gpu-architecture compute_61
OBJS = lib/cycletimer.o lib/ppm.o lib/etc.o

.PHONY: all clean

all: main-c main-omp main-cu

clean:
	rm -rf main-c main-omp main-cu lib/*.o

main-c: main.c $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

main-omp: main.c $(OBJS)
	$(CC) $(CFLAGS) $(OMPFLAGS) -o $@ $^

main-cu: main.cu $(OBJS)
	$(CUDAC) $(CUDAFLAGS) -o $@ $^

%.o: %.c %.h
	$(CC) $(CFLAGS) -c -o $@ $<

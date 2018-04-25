CC = cc
CFLAGS = -Wall -O3
CUDAC = nvcc
CUDAFLAGS = -O3 -m64 --gpu-architecture compute_61
OBJS = lib/cycletimer.o lib/ppm.o

.PHONY: all clean

all: main-c main-cu

clean:
	rm -rf main-cu main-c lib/*.o

main-c: main.c $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

main-cu: main.cu $(OBJS)
	$(CUDAC) $(CUDAFLAGS) -o $@ $^

%.o: %.c %.h
	$(CC) $(CFLAGS) -c -o $@ $<

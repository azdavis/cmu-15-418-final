CC = cc
CFLAGS = -O3
CUDAC = nvcc
CUDACFLAGS = -O3 -m64 --gpu-architecture compute_61

.PHONY: all clean

all: main-c main-cu

clean:
	rm -rf main-cu main-c *.o

main-c: main.c
	$(CC) $(CFLAGS) -o $@ $<

main-cu: main.cu
	$(CUDAC) $(CUDACFLAGS) -o $@ $<

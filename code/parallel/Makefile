CUDAC = nvcc
CUDACFLAGS = -O3 -m64 --gpu-architecture compute_61
OBJDIR = objs

.PHONY: all clean

all: main

clean:
	rm -rf main

main: main.cu
	$(CUDAC) $(CUDACFLAGS) -o $@ $<

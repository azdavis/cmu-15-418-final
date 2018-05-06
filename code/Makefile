CXX = g++
CFLAGS = -Wall -O3 -Wno-unknown-pragmas
OMPFLAGS = -fopenmp -DOMP
CUDAC = /usr/local/depot/cuda-8.0/bin/nvcc
CUDAFLAGS = -O3 -DCUDA -m64 --gpu-architecture compute_61
ISPC = /usr/local/depot/ispc-v1.9.1-linux/ispc
ISPFLAGS = -O3 --target=avx1-i32x8 --arch=x86-64
OBJS = lib/cycletimer.o lib/ppm.o lib/etc.o
ISPC_DEPS = $(OBJS) lib/portrait_ispc.o lib/portrait_ispc.hpp lib/tasksys.o
ISPC_FLAGS = -lpthread

.PHONY: all help clean regress benchmark

all: main-cpp main-omp main-cu main-ispc ## make all 4 implementations

help: ## show this help
	@grep -F '##' Makefile | grep -Fv '@grep' | sed -E 's/:.*##/:/'

clean: ## rm all generated files
	rm -rf main-cpp main-omp main-cu main-ispc lib/*.o lib/*_ispc.hpp results.tex

regress: all ## check all implementations have the same output on a small test case
	./check.sh img/elephant.ppm

benchmark: all ## same as regress, but a larger test case
	./check.sh img/large_elephant.ppm

results.tex: all ## run each implementation a few times for each image, summarize results in LaTeX tables
	./mk-results.py >$@

main-cpp: main.cpp $(OBJS) ## the sequential CPP implementation
	$(CXX) $(CFLAGS) -o $@ $^

main-omp: main.cpp $(OBJS) ## the CPP implementation with OMP on
	$(CXX) $(CFLAGS) $(OMPFLAGS) -o $@ $^

main-cu: main.cu $(OBJS) ## the CUDA implementation
	$(CUDAC) $(CUDAFLAGS) -o $@ $^

main-ispc: main-ispc.cpp $(ISPC_DEPS) ## the ISPC implementation
	$(CXX) $(CFLAGS) $(ISPC_FLAGS) -o $@ $^

lib/tasksys.o: lib/tasksys.cpp
	$(CXX) $(CFLAGS) -c -o $@ $<

%.o: %.cpp %.hpp
	$(CXX) $(CFLAGS) -c -o $@ $<

%_ispc.o %_ispc.hpp: %.ispc
	$(ISPC) $(ISPFLAGS) -o $*_ispc.o -h $*_ispc.hpp $^

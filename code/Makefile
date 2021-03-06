CXX = g++
CFLAGS = -Wall -O3 -Wno-unknown-pragmas
OMPFLAGS = -fopenmp -DOMP
CUDAC = /usr/local/depot/cuda-8.0/bin/nvcc
CUDAFLAGS = -O3 -DCUDA -m64 --gpu-architecture compute_61
ISPC = /usr/local/depot/ispc-v1.9.1-linux/ispc
ISPFLAGS = -O3 --target=avx1-i32x8 --arch=x86-64
OBJS = lib/cycletimer.o lib/ppm.o lib/etc.o
ISPCDEPS = $(OBJS) lib/portrait_ispc.o lib/portrait_ispc.hpp lib/tasksys.o
ISPCFLAGS = -lpthread

.SUFFIXES:
.PHONY: all help clean regress

all: main-cpp main-omp main-cu main-ispc ## make all 4 progs

help: ## show this help
	@grep -F '##' Makefile | grep -Fv '@grep' | sed -E 's/:.*##/:/'

clean: ## rm all generated files
	rm -rf main-cpp main-omp main-cu main-ispc lib/*.o lib/*_ispc.hpp results.tex

results.tex: all ## summarize timing results for each prog on each img
	./mk-results.py >$@

main-cpp: main.cpp $(OBJS) ## the sequential CPP prog
	$(CXX) $(CFLAGS) -o $@ $^

main-omp: main.cpp $(OBJS) ## the CPP prog with OMP on
	$(CXX) $(CFLAGS) $(OMPFLAGS) -o $@ $^

main-cu: main.cu $(OBJS) ## the CUDA prog
	$(CUDAC) $(CUDAFLAGS) -o $@ $^

main-ispc: main-ispc.cpp $(ISPCDEPS) ## the ISPC + OMP prog
	$(CXX) $(CFLAGS) $(ISPCFLAGS) $(OMPFLAGS) -o $@ $^

%.o: %.cpp %.hpp
	$(CXX) $(CFLAGS) -c -o $@ $<

%_ispc.o %_ispc.hpp: %.ispc
	$(ISPC) $(ISPFLAGS) -o $*_ispc.o -h $*_ispc.hpp $^

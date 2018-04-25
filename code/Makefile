CC = cc
CFLAGS = -O3
CUDAC = nvcc
CUDACFLAGS = -O3 -m64 --gpu-architecture compute_61
OBJS = cycletimer.o

.PHONY: all clean

all: main-c main-cu

clean:
	rm -rf main-cu main-c *.o

main-c: main.c $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $@ $<

main-cu: main.cu $(OBJS)
	$(CUDAC) $(CUDACFLAGS) $(OBJS) -o $@ $<

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

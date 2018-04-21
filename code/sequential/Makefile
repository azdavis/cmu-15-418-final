.SUFFIXES:
.PHONY: all

all: main
	./main

clean:
	rm -rf main

main: main.c
	$(CC) $(CFLAGS) -o $@ $<

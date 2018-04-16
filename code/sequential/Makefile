.SUFFIXES:
.PHONY: all

all:
	python main.py

clean:
	rm -rf main

main: main.c
	$(CC) $(CFLAGS) -o $@ $<

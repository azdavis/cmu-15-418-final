TEXC = pdflatex
TEXFLAGS = -halt-on-error -output-directory=build

.SUFFIXES:
.PHONY: all clean
.PRECIOUS: build/%.pdf

all: $(patsubst %.tex,build/%.pdf,$(wildcard *.tex))

clean:
	rm -rf build

build/%.pdf: %.tex
	mkdir -p $(dir $@)
	for x in 1 2; do $(TEXC) $(TEXFLAGS) $< $(Q); done

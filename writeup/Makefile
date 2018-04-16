TEXC = pdflatex
TEXFLAGS = -halt-on-error -output-directory=build

.SUFFIXES:
.PHONY: all clean
.PRECIOUS: build/%.pdf

all: \
	build/proposal-checkpoint.pdf \
	build/proposal.pdf \
	build/checkpoint-01.pdf

clean:
	rm -rf build

build/%.pdf: %.tex
	mkdir -p $(dir $@)
	for x in 1 2; do $(TEXC) $(TEXFLAGS) $< $(Q); done

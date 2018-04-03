TEXC = pdflatex
TEXFLAGS = -halt-on-error

.SUFFIXES:
.PHONY: all clean
.PRECIOUS: %.pdf

all: proposal.pdf

clean:
	rm -rf *.aux *.log *.pdf

%.pdf: %.tex
	for x in 1 2; do $(TEXC) $(TEXFLAGS) $< $(Q); done

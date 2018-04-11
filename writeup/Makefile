TEXC = pdflatex
TEXFLAGS = -halt-on-error

.SUFFIXES:
.PHONY: all clean
.PRECIOUS: %.pdf

all: proposal-checkpoint.pdf proposal.pdf

clean:
	rm -rf *.aux *.log *.out *.pdf

%.pdf: %.tex
	for x in 1 2; do $(TEXC) $(TEXFLAGS) $< $(Q); done

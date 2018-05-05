#!/usr/bin/env python

from __future__ import print_function
import json
import os
import subprocess
import sys

iters = 10

out_fname = "./out.ppm"

in_fnames = [
    "./img/bluejay.ppm",
    "./img/elephant.ppm",
    "./img/flower.ppm",
    "./img/large_elephant.ppm",
    "./img/purp.ppm",
    "./img/tiger.ppm",
]

C = "./main-c"
OMP = "./main-omp"
CUDA = "./main-cu"

programs = [
    C,
    OMP,
    CUDA,
]

time_items = [
    u"init",
    u"color_counts",
    u"old_mask",
    u"new_mask",
    u"blur",
    u"clean_up",
]

def dict_sum(a):
    ret = 0
    for x in a:
        ret += a[x]
    return ret

def dict_is_lt(a, b):
    return dict_sum(a) - dict_sum(b) < 0

data = {}

for prog in programs:
    data[prog] = {}
    for in_f in in_fnames:
        data[prog][in_f] = None
        for i in range(iters):
            print(prog, in_f, i, file=sys.stderr)
            out = subprocess.check_output([prog, in_f, out_fname])
            new = json.loads(out)
            cur = data[prog][in_f]
            if cur is None or dict_is_lt(new, cur):
                data[prog][in_f] = new

os.remove(out_fname)

table_begin = "\\begin{tabular}{l|l|l|l|l|l}"
row_header = "    Item & C & OMP & Speedup & CUDA & Speedup"
row = "{} & {:.5f} & {:.5f} & {:.5f} & {:.5f} & {:.5f}"
with_slash = "\\\\  "
no_slash = "    "

for in_f in in_fnames:
    print("\\subsection{" + in_f + "}")
    print(table_begin)
    print(row_header)
    print(with_slash + "\\hline")
    first = True
    for ti in time_items:
        c = data[C][in_f][ti]
        omp = data[OMP][in_f][ti]
        cuda = data[CUDA][in_f][ti]
        if first:
            print(no_slash, end="")
        else:
            print(with_slash, end="")
        first = False
        print(row.format(str(ti), c, omp, c / omp, cuda, c / cuda))
    print("\\end{tabular}")

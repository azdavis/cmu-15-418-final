#!/usr/bin/env python

from __future__ import print_function
import json
import subprocess
import sys

iters = 10

devnull = "/dev/null"

in_fnames = [
    "./img/bluejay.ppm",
    "./img/elephant.ppm",
    "./img/flower.ppm",
    "./img/large_elephant.ppm",
    "./img/purp.ppm",
    "./img/tiger.ppm",
]

cpp_prog = "./main-cpp"
omp_prog = "./main-omp"
cuda_prog = "./main-cu"
ispc_prog = "./main-ispc"

programs = [
    cpp_prog,
    omp_prog,
    cuda_prog,
    ispc_prog,
]

time_items = [
    u"init",
    u"color_counts",
    u"build_mask",
    u"refine_mask",
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
            out = subprocess.check_output([prog, in_f, devnull])
            new = json.loads(out)
            cur = data[prog][in_f]
            if cur is None or dict_is_lt(new, cur):
                data[prog][in_f] = new

table_begin = "\\begin{tabular}{r|r|r|r|r|r|r|r}"
with_slash = "\\\\  "
no_slash = "    "
slash_hline = with_slash + "\\hline"
row_header = no_slash + (
    "Item & C++ & "
    "OMP & Speedup & "
    "CUDA & Speedup & "
    "ISPC & Speedup"
)
float_str = " & {:.4f}"

def print_line(title, get, sums=None):
    print(title, end="")
    cpp_time = 0
    for prog in programs:
        time = get(prog)
        if sums is not None:
            sums[prog] += time
        print(float_str.format(time), end="")
        if prog == cpp_prog:
            cpp_time = time
        else:
            print(float_str.format(cpp_time / time), end="")
    print("")

for in_f in in_fnames:
    print("\\subsection{" + in_f + "}")
    print(table_begin)
    print(row_header)
    print(slash_hline)
    sums = {}
    for prog in programs:
        sums[prog] = 0
    first = True
    for ti in time_items:
        if first:
            print(no_slash, end="")
        else:
            print(with_slash, end="")
        first = False
        print_line(
            str(ti).replace("_", " "),
            lambda prog: data[prog][in_f][ti],
            sums
        )
    print(slash_hline)
    print(no_slash, end="")
    print_line("total", lambda prog: sums[prog])
    print("\\end{tabular}")

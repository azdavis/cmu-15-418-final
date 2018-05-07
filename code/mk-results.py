#!/usr/bin/env python

from __future__ import print_function
import json
import subprocess
import sys
import os

if len(sys.argv) != 1:
    print("usage: {}".format(sys.argv[0]), file=sys.stderr)
    sys.exit(1)

iters = 10

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
ispc_prog = "./main-ispc"
cuda_prog = "./main-cu"

programs = [
    # cpp_prog must be first
    cpp_prog,
    omp_prog,
    ispc_prog,
    cuda_prog,
]

table_begin = "\\begin{tabular}{r|r|r|r|r|r|r|r}"
with_slash = "\\\\  "
no_slash = "    "
slash_hline = with_slash + "\\hline"
row_header = no_slash + (
    "Item & C++ & "
    "OMP & Speedup & "
    "ISPC & Speedup & "
    "CUDA & Speedup"
)
float_str = " & {:.4f}"

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

def print_row(title, get):
    print(title, end="")
    cpp_time = None
    for prog in programs:
        time = get(prog)
        print(float_str.format(time), end="")
        if cpp_time is None:
            # cpp_prog must be first
            cpp_time = time
        else:
            print(float_str.format(cpp_time / time), end="")
    print("")

def get_out_f(in_f, prog, i):
    return "{}-{}-{}.ppm".format(
        in_f.replace(".ppm", ""),
        prog.replace("./", ""),
        i,
    )

data = {}

for in_f in in_fnames:
    data[in_f] = {}
    check = None
    for prog in programs:
        data[in_f][prog] = None
        for i in range(iters):
            out_f = get_out_f(in_f, prog, i)
            print("img: {}, prog: {}, iter: {}/{}... ".format(
                in_f, prog, i + 1, iters), file=sys.stderr, end="")
            out = subprocess.check_output([prog, in_f, out_f])
            if check is None:
                # cpp_prog must be first
                print("create ref img", file=sys.stderr)
                check = out_f
            elif subprocess.call(["cmp", check, out_f]) == 0:
                print("matches ref img", file=sys.stderr)
                os.remove(out_f)
            else:
                print("DOES NOT match ref img", file=sys.stderr)
                sys.exit(1)
            new = json.loads(out)
            cur = data[in_f][prog]
            if cur is None or dict_is_lt(new, cur):
                data[in_f][prog] = new
    os.remove(check)

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
        print(no_slash if first else with_slash, end="")
        first = False
        get = lambda prog: data[in_f][prog][ti]
        print_row(str(ti).replace("_", " "), get)
        for prog in programs:
            sums[prog] += get(prog)
    print(slash_hline)
    print(no_slash, end="")
    print_row("total", lambda prog: sums[prog])
    print("\\end{tabular}")

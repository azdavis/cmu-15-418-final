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

images = [
    "./img/bluejay.ppm",
    "./img/elephant.ppm",
    "./img/flower.ppm",
    "./img/large_elephant.ppm",
    "./img/purp.ppm",
    "./img/tiger.ppm",
]

# first program is used as reference for correctness and speedup
programs = [
    "./main-cpp",
    "./main-omp",
    "./main-ispc",
    "./main-cu",
]

table_begin = "\\begin{tabular}{r|r|r|r|r|r|r|r}"
with_slash = "\\\\  "
no_slash = "    "
slash_hline = with_slash + "\\hline"
float_str = " & {:.4f}"

# order should match programs
row_header = no_slash + (
    "Item & C++ & "
    "OMP & Speedup & "
    "ISPC & Speedup & "
    "CUDA & Speedup"
)

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
    ref_time = None
    for prog in programs:
        time = get(prog)
        print(float_str.format(time), end="")
        if ref_time is None:
            ref_time = time
        else:
            print(float_str.format(ref_time / time), end="")
    print("")

data = {}

for img in images:
    data[img] = {}
    check = None
    for prog in programs:
        data[img][prog] = None
        for i in range(iters):
            img_disp = img.replace(".ppm", "")
            prog_disp = prog.replace("./", "")
            i_disp = str(i + 1)
            outf = "{}-{}-{}.ppm".format(img_disp, prog_disp, i_disp)
            print("img: {}, prog: {}, iter: {}/{}... ".format(
                img_disp, prog_disp, i_disp, iters), file=sys.stderr, end="")
            time_json = subprocess.check_output([prog, img, outf])
            if check is None:
                print("create ref img", file=sys.stderr)
                check = outf
            elif subprocess.call(["cmp", check, outf]) == 0:
                print("matches ref img", file=sys.stderr)
                os.remove(outf)
            else:
                print("DOES NOT match ref img", file=sys.stderr)
                sys.exit(1)
            new = json.loads(time_json)
            cur = data[img][prog]
            if cur is None or dict_is_lt(new, cur):
                data[img][prog] = new
    os.remove(check)

for img in images:
    print("\\subsection{" + img + "}")
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
        get = lambda prog: data[img][prog][ti]
        print_row(str(ti).replace("_", " "), get)
        for prog in programs:
            sums[prog] += get(prog)
    print(slash_hline)
    print(no_slash, end="")
    print_row("total", lambda prog: sums[prog])
    print("\\end{tabular}")

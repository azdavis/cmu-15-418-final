#!/usr/bin/env python

import subprocess
import json
import os

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

programs = [
    "./main-c",
    "./main-omp",
    "./main-cu"
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
            print(prog, in_f, i)
            out = subprocess.check_output([prog, in_f, out_fname])
            new = json.loads(out)
            cur = data[prog][in_f]
            if cur is None or dict_is_lt(new, cur):
                data[prog][in_f] = new

os.remove(out_fname)
print(data)

 # -*- coding: utf-8 -*-
__version__ = "0.3.3"
__description__ = f"""
A word tool for text operation, such as match, count
    v{__version__}, developed by devseed
"""

import os
import csv
import codecs
import logging
import argparse
from glob import glob
from io import StringIO
from collections import Counter
from typing import Callable, Tuple, List, Union

import numpy as np

try:
    from libutil import readlines, writelines, readbytes, writebytes, filter_loadfiles, load_ftext
except ImportError:
    exec("from libutil_v0_6 import readlines, writelines, readbytes, writebytes, filter_loadfiles, load_ftext")

# algorithms for string
def calc_lcs(s1: str, s2: str, cache_max=256) -> int:
    """
    longeset common sequence length of s1 and s2
    """

    l1, l2 = len(s1), len(s2)
    if l1 == 0: return l2
    if l2 == 0: return l1
    if cache_max <= 0:
        res = np.zeros((l1+1, l2+1), dtype=np.uint16)
        calc_lcs._res = None                                                                             
    else:
        if not hasattr(calc_lcs, "_res") or calc_lcs._res is None or calc_lcs._res.shape[0] < cache_max:
            res = np.zeros((cache_max, cache_max), dtype=np.uint16)
            calc_lcs._res = res
        else: 
            res = calc_lcs._res
            res[:l1+1, :l2+1].fill(0)

    res[:l1+1, :l2+2].fill(0)
    for i in range(1, l1+1):
        for j in range(1, l2+1):
            if s1[i-1] == s2[j-1]: res[i][j] = res[i-1][j-1] + 1
            else: res[i][j] = max(res[i-1][j], res[i][j-1])
    return res[l1][l2]

def calc_lev(s1: str, s2: str, cache_max=256) -> int:
    """
    Levenshtein distance (edit value)
    """
    
    l1, l2 = len(s1), len(s2)
    if l1 == 0: return l2
    if l2 == 0: return l1
    if cache_max <= 0:
        res = np.zeros((l1, l2), dtype=np.uint16)
        calc_lev._res = None
    else:
        if not hasattr(calc_lev, "_res") or calc_lev._res is None or calc_lev._res.shape[0] < cache_max:
            res = np.zeros((cache_max, cache_max), dtype=np.uint16)
            calc_lev._res = res
        else: 
            res = calc_lev._res
            res[:l1, :l2].fill(0)
    
    for i in range(0, l1):
        for j in range(0, l2):
            if min(i, j) == 0: # empty string, insert all in s1
                res[i][j] = max(i, j)
            else: 
                t = 1 if s1[i] != s2[j] else 0
                res[i][j] = min(
                    res[i-1][j] + 1, # insert 1 char in s1
                    res[i][j-1] + 1, # delete 1 char in s1
                    res[i-1][j-1] + t # replace 1 char in s1 if s1[1] != s2[j]
                )
    return res[l1-1][l2-1]

# text operation
@filter_loadfiles([(0, "utf-8", "ignore", True), (1, "utf-8", "ignore", True)])
def match_line(lines1obj: List[str], lines2obj: List[str], *, 
    show_progress=False, min_len=0, 
    f_distance: Callable[[str, str], int]=None, 
    f_theshod: Callable[[str, str, int], bool]=None) -> Tuple[np.ndarray, np.ndarray]:
    """
    match the lines1 and lines 2 by calculate the distance
    :param show_progess: print the match result for every line
    :param min_len: the min length to match
    :param f_distance: f_distance(s1, s2), calculate the distance of two text
    :param f_theshod:  f_theshod(s1, s2, d), if skip match, return False
    :return: (l1match, l2match), for record index, -1 for no match 
    """ 

    def distance(s1, s2) -> int:
        return calc_lev(s1, s2)

    def threshod(s1, s2, d) -> bool:
        l1, l2 = len(s1), len(s2)
        if max(d/l1, d/l2) < 0.25: return True
        if d <= 3 and max(l1, l2) > 2*d: return True
        return False

    lines1, lines2 = lines1obj, lines2obj
    line1_match = -np.ones(len(lines1), dtype=np.int32)
    line2_match = -np.ones(len(lines2), dtype=np.int32)
    if f_distance == None: f_distance = distance
    if f_theshod == None: f_theshod = threshod
    for i1, s1 in enumerate(lines1):
        match_flag = False
        i2min, dmin = 0, 0x7fffffff
        if len(s1) < min_len : continue # skip small text
        for i2, s2 in enumerate(lines2):
            d = f_distance(s1, s2)
            if d < dmin: 
                i2min, dmin = i2, d
                if d==0: break
            elif d == dmin and line2_match[i2] < 0:
                i2min, dmin = i2, d
        s2 = lines2[i2min]
        if f_theshod(s1, s2, dmin): 
            match_flag = True
            line1_match[i1], line2_match[i2min] = i2min, i1
        if show_progress:
            print(f"{i1+1}/{len(lines1)} {match_flag} d={dmin} i2={i2min} s1='{s1}' s2='{s2}'")
    return line1_match, line2_match

@filter_loadfiles((0, "utf-8", "ignore", True))
def count_line(linesobj: Union[List[str], str]) -> Counter:
    """
    count the char in lines
    :param linesobj: lines or file name
    :return: char counter
    """
    
    counter =  Counter()
    lines = linesobj
    for line in lines:
        for c in line:
            counter[c] += 1

    return counter

def save_counter(counter: Counter, outpath=None, n=None) -> List[str]:
    """
    save counter to csv file
    """
    
    sbufio = StringIO()
    chars = counter.most_common(n)
    wr = csv.DictWriter(sbufio, ["char", "count"])
    wr.writeheader()
    for (k, v) in chars:
        t = {"char": k, "count": v}
        wr.writerow(t)
    lines = sbufio.getvalue().splitlines(keepends=True)
    if outpath:
        writebytes(outpath, writelines(lines))
    
    return lines

@filter_loadfiles((0, 'utf8'))
def load_counter(inobj: Union[str, List[str]]) -> Counter:
    """
    load counter from csv file
    """
    
    lines = inobj
    counter = Counter()
    for row in csv.DictReader(lines):
        counter.update({row["char"]: int(row["count"])})

    return counter

def cli(cmdstr=None):
    def cmd_match(args):
        logging.debug(repr(args))
        if args.format == "text":
           inobj1, inobj2 = args.inpath1, args.inpath2
        elif args.format in ("ftext_org", "ftext_now"):
            if args.format == "ftext_org":
                inobj1, _ = load_ftext(args.inpath1)
                inobj2, _ = load_ftext(args.inpath2)
            else:
                _, inobj1 = load_ftext(args.inpath1)
                _, inobj2 = load_ftext(args.inpath2)
            inobj1, inobj2 = [t.text for t in inobj1], [t.text for t in inobj2]
            t1match, _ = match_line(inobj1, inobj2)

        sbufio = StringIO()
        wr = csv.DictWriter(sbufio, ["index1", "index2", "text1", "text2"])
        wr.writeheader()
        for i1 in range(t1match.shape[0]):
            i2 = t1match[i1]
            text1, text2 = inobj1[i1], None if i2 < 0 else inobj2[i2]
            t = {"index1": i1, "index2": i2, "text1": text1, "text2": text2}
            wr.writerow(t)
            logging.info(t)
        if args.outpath:
            writebytes(args.outpath, codecs.BOM_UTF8 + writelines([sbufio.getvalue()]))

    def cmd_count(args):
        logging.debug(repr(args))
        
        # gather inpaths
        inpaths = []
        for path in args.inpaths:
            if os.path.isdir(path):
                inpaths.extend(glob(os.path.join(path, "*.txt")))
            else: inpaths.extend(glob(path))
        
        # load inpaths
        counter = Counter()
        n_lines = 0
        for inpath in inpaths:
            if args.format == "counter":
                cur_counter = load_counter(inpath)
                n_lines  += len(cur_counter)
                counter += cur_counter
            else:
                if args.format == "text": 
                    lines = readlines(readbytes(inpath))
                elif args.format in ("ftext_org", "ftext_now"):
                    if args.format == "ftext_org": ftexts, _ = load_ftext(inpath)
                    else: _, ftexts = load_ftext(inpath)
                    lines = [t.text for t in ftexts]
                n_lines += len(lines)
                _counter = count_line(lines)
                n_chars = sum(_counter.values())
                n_types = len(_counter)
                counter.update(_counter)
                logging.info(f"n_line={len(lines)} n_char={n_chars} n_type={n_types} path={inpath}")

        # summary charset and save
        n_chars = sum(counter.values())
        n_types = len(counter)
        logging.info(f"n_line={n_lines} n_char={n_chars} n_type={n_types} path=*")
        if args.outpath: save_counter(counter, args.outpath, args.most_common)

    p = argparse.ArgumentParser(description=__description__)
    p2 = p.add_subparsers(title="operations")
    p_match = p2.add_parser("match", help="match texts or ftexts in two files")
    p_count = p2.add_parser("count", help="count texts or ftexts information")
    for t in (p_match, p_count):
        t.add_argument("-o", "--outpath", default="out")
        t.add_argument("--log_level", default="info", help="set log level", 
            choices=("none", "critical", "error", "warning", "info", "debug"))
        t.add_argument("--format", choices=["ftext_org", "ftext_now", "text", "counter"], 
            default="text", help="the format of input file")
        
    p_match.set_defaults(handler=cmd_match)
    p_match.add_argument("inpath1")
    p_match.add_argument("inpath2")
    p_count.set_defaults(handler=cmd_count)
    p_count.add_argument("inpaths", nargs='+', help="inpaths to count, can aslo use glob")
    p_count.add_argument("-n", "--most_common", type=int, 
        default=None, help="show how many most common chars")

    args = p.parse_args(cmdstr.split(' ') if cmdstr else None)
    loglevel = args.log_level if hasattr(args, "log_level") else "info"
    logging.basicConfig(level=logging.getLevelName(loglevel.upper()), 
                    format="%(levelname)s:%(funcName)s: %(message)s")
    if hasattr(args, "handler"): args.handler(args)
    else: p.print_help()

if __name__ == "__main__":
    cli()

"""
history:
v0.1, match_texts, write_format_multi, read_format_multi
v0.2, count_glphy for building font
v0.2.1, fix read_format_multi bug
v0.2.2, add typing hint and no dependency to bintext
v0.3, reamke with libutil v0.6
v0.3.1, change count inpath to mutlity directory, add save|load_counter
v0.3.2, change match_line to use lev distance, fix threadshod bug
v0.3.3, add cmd_count counter choice to merge multi counter
"""
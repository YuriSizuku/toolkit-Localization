"""
A tool to change some texts codepage in files,
    v0.1, developed by devseed
"""

import os
import sys
import codecs
import argparse
from copy import deepcopy

def datacpcvt(data: bytearray, texts: list, 
    fromcp='936', tocp='932', middlecp=None, 
    minsize=4, copydata=False, singlematch=False, 
    outpath="") -> bytearray:
    """
    search decode(fromcp) -> encode(tocp)
    search decode(middlecp) -> encode(fromcp).decode(tocp) -> encode(middlecp)
    """        
    if copydata: data = deepcopy(data)
    texts.sort(key=lambda s: len(s), reverse=True)
    for i, text in enumerate(texts):
        text = text.rstrip('\n').rstrip('\r')
        start = 0
        findflag = False
        try:
            if middlecp: frombytes = text.encode(middlecp)
            else: frombytes = text.encode(fromcp)
        except UnicodeError as e:
            print(e)
        while start < len(data):
            idx = data.find(frombytes, start)
            if idx < 0:
                # if not findflag: print(f"-text{i}, {text} not found!")
                break
            else:
                findflag = True
                size = len(frombytes)
                try:
                    if middlecp:
                        _text = ""
                        for c in text:
                            try:
                                c = c.encode(fromcp).decode(tocp)
                            except UnicodeError as e:
                                pass
                            _text += c
                        tocpbytes = _text.encode(middlecp)
                    else:
                        tocpbytes = text.encode(tocp)
                    if size > minsize:
                        data[idx: idx+size] = tocpbytes
                        print(f"+text{i}, {text} finished at 0x{idx:x}!")
                    size = len(tocpbytes)
                except UnicodeError as e:
                    print(e)
                start = idx + size
                if singlematch: break
    if outpath!="":
        with open(outpath, 'wb') as fp:
            fp.write(data)
    return data

def filecpcvt(inpath, fromcp, tocp, outpath="out"):
    fp = codecs.open(inpath, 'r', encoding=fromcp)
    fp2 = codecs.open(outpath, 'w', encoding=tocp)
    lines = fp.readlines()
    fp2.writelines(lines)
    fp.close()
    fp2.close()

def debug():
    pass

def main(cmdstr=None):
    parser = argparse.ArgumentParser(description=
        "convert the file from a codepage to another codepage")
    parser.add_argument('inpath', type=str)
    parser.add_argument('-o', '--outpath', default='out', type=str)
    parser.add_argument('-l', '--list', type=str,
        default='', help='the replace text list')
    parser.add_argument('--fromcp', type=str, default='932')
    parser.add_argument('--middlecp', type=str, default=None)
    parser.add_argument('--tocp', type=str, default='936')
    parser.add_argument('--minsize', type=int, default=2)
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=0)
    parser.add_argument('--singlematch', action='store_true', 
        help="use this flag for only match once")
    if cmdstr is None: args = parser.parse_args()
    else:  args = parser.parse_args(args=cmdstr.split(' '))
    
    if args.list=='':
        filecpcvt(args.inpath, args.fromcp, args.tocp, args.outpath)
    else:
        with codecs.open(args.list, 'r', 'utf-8') as fp:
            texts = fp.readlines()
        with open(args.inpath, 'rb') as fp:
            data = bytearray(fp.read())
            if args.end==0: data = data[args.start:]
            else:  data = data[args.start: args.end]
        datacpcvt(data, texts, 
            args.fromcp, args.tocp, args.middlecp,
            minsize=args.minsize, singlematch=args.singlematch, 
            outpath=args.outpath)

if __name__ == "__main__":
    # debug()
    main()
    pass
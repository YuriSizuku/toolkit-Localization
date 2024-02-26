"""
util functions and structures for galgame localization
  v0.6, developed by devseed
"""

import os
import gzip
import codecs
import zipfile
from io import BytesIO
from dataclasses import dataclass
from typing import Union, List, Tuple

__version__  = 600

# util functions
def readlines(data: bytes, encoding='utf-8', enc_error='ignore') -> List[str]:
    i = 0
    start = 0
    lines = []
    while i < len(data): 
        if data[i] == ord('\r'):
            if i+1 < len(data) and data[i+1] == '\n': i += 1
            lines.append(str(data[start: i+1], encoding, enc_error))
            start = i+1
        elif data[i] == ord('\n'):
            lines.append(str(data[start: i+1], encoding, enc_error))
            start = i+1
        i += 1
    return lines

def writelines(lines: List[str], encoding='utf-8', enc_error='ignore') -> bytes:
    bufio = BytesIO()
    for line in lines:
        bufio.write(line.encode(encoding, enc_error))
    return bufio.getbuffer()

def loadfiles(indexs=None):
    if indexs == None: indexs = [0]
    if type(indexs) == int:  indexs = [indexs]

    def load_gz(path) -> bytes: # path/x.gz 
        with gzip.GzipFile(path, 'rb') as fp: 
            return fp.read()
        
    def load_zip(path) -> bytes: # path1/x.zip>path2/y
        path1, path2 = path.split(".zip>")
        path2 = path2.replace('\\', '/')
        with zipfile.ZipFile(path1 + ".zip", 'r') as fp1:
            with fp1.open(path2, 'r') as fp2:
                return fp2.read()
    
    def load_direct(path) -> bytes:
        with open(path, 'rb') as fp:
            return fp.read()

    def load_file(path: str) -> bytes:
        if os.path.splitext(path)[1] == '.gz': data = load_gz(path)
        elif ".zip>" in path: data = load_zip(path)
        else: data = load_direct(path)
        return data
    
    def wrapper1(func): # decorator(dec_args)(func)(fun_args)
        def wrapper2(*args, **kw):
            newargs = list(args)
            for i, t in enumerate(indexs):
                if type(t) == int and type(newargs[t]) == str: 
                    newargs[t] = load_file(newargs[t])
                elif type(t) == str and t in kw and type(kw[t]) == str:
                    kw[t] = load_file(kw[t])
            return func(*newargs, **kw)
        return wrapper2
    return wrapper1

# structures
@dataclass
class ftext_t:
    addr: int = 0
    size: int = 0
    text: str = ""

@dataclass
class tbl_t:
    tcode : bytes = b""
    tchar : str = ""

@dataclass
class jtable_t: # jump table
    addr: int = 0
    addr_new: int = 0
    toaddr: int = 0
    toaddr_new: int = 0

@dataclass
class msg_t:
    id: int = 0
    msg: str = ""
    type: int = 0

# serilization functions
def dump_ftext(ftexts1: List[ftext_t], ftexts2: List[ftext_t], outpath: str = None, *,  
                encoding="utf-8", width_index = (5, 6, 3)) -> List[str]:
    """
    format text, such as ●num|addr|size● text
    :param ftexts1[]: text dict array in '○' line, 
    :param ftexts2[]: text dict array in '●' line
    :return: ftext lines
    """

    width_num, width_addr, width_size = width_index
    if width_num==0: width_num = len(str(len(ftexts1)))
    if width_addr==0: width_addr = len(hex(max(t.addr for t in ftexts1))) - 2
    if width_size==0: width_size = len(hex(max(t.size for t in ftexts1))) - 2

    lines = []
    fstr1 = "○{num:0%dd}|{addr:0%dX}|{size:0%dX}○ {text}\n" \
            % (width_num, width_addr, width_size)
    fstr2 = fstr1.replace('○', '●')
    if not ftexts1: ftexts1 = [None for x in ftexts2]
    if not ftexts2: ftexts2 = [None for x in ftexts1]
    for i, (t1, t2) in enumerate(zip(ftexts1, ftexts2)):
        if t1: lines.append(fstr1.format(num=i, addr=t1.addr, size=t1.size, text=t1.text))
        if t2: lines.append(fstr2.format(num=i, addr=t2.addr, size=t2.size, text=t2.text))
        lines.append("\n")

    if outpath:
        with codecs.open(outpath, 'w', encoding) as fp:
            fp.writelines(lines)

    return lines 

@loadfiles(0)
def load_ftext(inobj: Union[str, List[str]], *, 
        encoding="utf-8") -> Tuple[List[ftext_t], List[ftext_t]]:
    """
    format text, such as ●num|addr|size● text
    :param inobj: can be path, or lines[] 
    :return: ftexts1[]: text dict array in '○' line, 
             ftexts2[]: text dict array in '●' line
    """

    ftexts1, ftexts2 = [], []
    lines = readlines(inobj, encoding, 'ignore') if type(inobj) != list else inobj
    for line in lines:
        indicator = line[0]
        if indicator == "#": continue
        if indicator not in {"○", "●"}: continue
        line  = line.rstrip('\n').rstrip('\r')
        _, t1, t2 = line.split(indicator)
        ftext = ftext_t(text=t2[1:])
        try: 
            _, t12, t13 = t1.split('|')
            ftext.addr, ftext.size = int(t12, 16), int(t13, 16)
        except ValueError: pass 
        if indicator=='○': ftexts1.append(ftext)
        else: ftexts2.append(ftext)

    return ftexts1, ftexts2

def dump_tbl(tbl: List[tbl_t], outpath=None, *, encoding='utf-8')  -> List[str]:
    lines = []
    for t in tbl:
        raw_str = ""
        for d in t.tcode: raw_str += f"{d:02X}"
        line = ("{:s}={:s}\n".format(raw_str, t.tchar))
        lines.append(line)
    if outpath:
        with codecs.open(outpath, "w", encoding) as fp:
            fp.writelines(lines)
    return lines

@loadfiles(0)
def load_tbl(inobj: Union[str, List[str]], *, encoding='utf-8') ->  List[tbl_t]:
    """
    tbl file format "tcode=tchar", 
    :param inobj: can be path, or lines_text[] 
    :return: [(charcode, charstr)]
    """

    tbl: List[tbl_t] = []
    lines = readlines(inobj, encoding, 'ignore') if type(inobj) != list else inobj
    for line in lines:
        indicator = line[0]
        if indicator == "#": continue
        line = line.rstrip('\n').rstrip('\r')
        if len(line) <= 0: continue
        if line.find("==") == -1: t1, tchar = line.split('=')
        else: t1 = line.split('=')[0]; tchar = '='
        tcode = bytearray()
        for i in range(0, len(t1), 2):
            tcode.append(int(t1[i: i+2], 16)) 
        tbl.append(tbl_t(bytes(tcode), tchar))

    return tbl

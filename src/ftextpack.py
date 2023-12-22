g_description = """
A flexible format and low memory use implementation 
for general dynamic localization
   v0.1.1, developed by devseed

   use ftextpack.h to load dynamicly    
"""

import os
import re
import struct
import codecs
import argparse
import zlib
from ctypes import *
from io import BytesIO
from glob import glob
from typing import Union, List, Tuple, Dict, Callable, Any

FTEXTPACK_VERSION = 110

# util functions
def dump_ftext(ftexts1:List[Dict[str,Union[int,str]]], 
    ftexts2: List[Dict[str, Union[int, str]]], 
    outpath: str="", *, num_width=5, 
    addr_width=6, size_width=3) -> List[str]:
    """
    ftexts1, ftexts2 -> ftext lines
    text dict is as {'addr':, 'size':, 'text':}
    :param ftexts1[]: text dict array in '○' line, 
    :param ftexts2[]: text dict array in '●' line
    :return: ftext lines
    """

    if num_width==0:
        num_width = len(str(len(ftexts1)))
    if addr_width==0:
        d = max([t['addr'] for t in ftexts1])
        addr_width = len(hex(d))-2
    if size_width==0:
        d = max([t['size'] for t in ftexts1])
        size_width = len(hex(d))-2

    fstr1 = "○{num:0"+ str(num_width) + "d}|{addr:0" + str(addr_width) + "X}|{size:0"+ str(size_width) + "X}○ {text}\n"
    fstr2 = fstr1.replace('○', '●')
    lines = []

    length = 0
    if ftexts1 == None: 
        length = len(ftexts2)
        fstr2 += '\n'
    if ftexts2 == None: 
        length = len(ftexts1)
        fstr1 += '\n'
    if ftexts1 != None and ftexts2 != None : 
        length = min(len(ftexts1), len(ftexts2))
        fstr2 += '\n'

    for i in range(length):
        if ftexts1 != None:
            t1 = ftexts1[i]
            lines.append(fstr1.format(
                num=i,addr=t1['addr'],size=t1['size'],text=t1['text']))
        if ftexts2 != None:
            t2 = ftexts2[i]
            lines.append(fstr2.format(
                num=i,addr=t2['addr'],size=t2['size'],text=t2['text']))

    if outpath != "":
        with codecs.open(outpath, 'w', 'utf-8') as fp:
            fp.writelines(lines)
    return lines 

def load_ftext(ftextobj: Union[str, List[str]], 
    only_text = False ) -> List[Dict[str, Union[int, str]]]:
    """
    ftext lines  -> ftexts1, ftexts2
    text dict is as {'addr':, 'size':, 'text':}
    :param inobj: can be path, or lines[] 
    :return: ftexts1[]: text dict array in '○' line, 
             ftexts2[]: text dict array in '●' line
    """

    ftexts1, ftexts2 = [], []
    if type(ftextobj) == str: 
        with codecs.open(ftextobj, 'r', 'utf-8') as fp: 
            lines = fp.readlines()
    else: lines = ftextobj

    if only_text == True: # This is used for merge_text
        re_line1 = re.compile(r"^○(.+?)○[ ](.*)")
        re_line2 = re.compile(r"^●(.+?)●[ ](.*)")
        for line in lines:
            line = line.strip("\n").strip('\r')
            m = re_line1.match(line)
            if m is not None:
                ftexts1.append({'addr':0,'size':0,'text': m.group(2)})
            m = re_line2.match(line)
            if m is not None:
                ftexts2.append({'addr':0,'size':0,'text': m.group(2)})
    else:
        re_line1 = re.compile(r"^○(\d*)\|(.+?)\|(.+?)○[ ](.*)")
        re_line2 = re.compile(r"^●(\d*)\|(.+?)\|(.+?)●[ ](.*)")
        for line in lines:
            line = line.strip("\n").strip('\r')
            m = re_line1.match(line)
            if m is not None:
                ftexts1.append({'addr':int(m.group(2),16),
                'size':int(m.group(3),16),'text': m.group(4)})
            m = re_line2.match(line)
            if m is not None:
                ftexts2.append({'addr':int(m.group(2),16),
                'size':int(m.group(3),16),'text': m.group(4)})
    return ftexts1, ftexts2

def load_tbl(inobj: Union[str, List[str]], 
    encoding='utf-8') ->  List[Tuple[bytes, str]]:
    """
    tbl file format "code(XXXX) = utf-8 charcode", 
        the sequence is the same as the text
    :param inobj: can be path, or lines_text[] 
    :return: [(charcode, charstr)]
    """

    tbl = []
    if type(inobj) == str: 
        with codecs.open(inobj, 'r', encoding=encoding) as fp: 
            lines = fp.readlines()
    else: lines = inobj

    re_line = re.compile(r'([0-9|A-F|a-f]*)=(\S|\s)$')
    for line in lines:
        line = line.rstrip('\n').rstrip('\r')
        if not line : break
        m = re_line.match(line)
        if m is not None:
            d = int(m.group(1), 16)
            if d<0xff:
                charcode = struct.pack("<B", d)
            elif d>0xff and d<0xffff:
                charcode = struct.pack(">H", d)
            else:
                charcode = struct.pack(">BBB", 
                    d>>16, (d>>8)&0xff, d&0xff)
            c = m.group(2)
            tbl.append((charcode, c))
    return tbl

    def wrapper(*args, **kw):
        if type(args[argidx]) == str: 
            with open(args[argidx], 'rb') as fp: 
                args[argidx] = fp.read()
        return func(*args, **kw)
    return wrapper

def encode_tbl(text: str, tbl: List[Tuple[bytes, str]], replace_encerror=None) -> bytes:
    """
    encoding the text by tbl
    :param tbl: for example [(charcode, c),...], c is the str
    :return: the encoded bytesarray
    """

    if replace_encerror=="": replace_encerror=None
    data = BytesIO()
    for c in text:
        flag = False
        for i in range(len(tbl)):
            if tbl[i][1] == c:
                data.write(tbl[i][0])
                flag =True
                break
        if flag is False:
            if replace_encerror: 
                data.write(bytes(replace_encerror))
            else: 
                print("Encodingtbl failed with "+ c + " in tbl")
                return None
    return data.getvalue()

# ftextpack functions
class ftextpack_textinfo_t(Structure):
    _fields_ = [
        ('hash', c_uint32), 
        ('offset', c_uint32),
        ('addr', c_uint32),
        ('size', c_uint32)
    ]
    def dummy(self): # for intelligence auto complete
        self.hash, self.size, self.addr, self.offset

class ftextpack_info_t(Structure):
    _fields_ = [
        ('org', ftextpack_textinfo_t),
        ('now', ftextpack_textinfo_t)
    ]
    def dummy(self):
        self.org, self.now

class ftextpack_index_t(Structure):
    _fields_ = [
        ('magic', c_char * 4), 
        ('count', c_uint32), 
        ('offset', c_uint32),
        ('reserved', c_uint32),
        ('info', ftextpack_info_t * 1)
    ]
    def dummy(self):
        self.magic, self.count, self.offset, self.reserved, self.info

def ftextpack(ftextpath, orgpath, outpath="data.fp01", 
        encoding="utf8", tblobj=None, *, sortby="hash", 
        replace_map=None, override_fail=None, 
        pack_org=False, pack_nodup=False, pack_compact=False,
        f_extension: Callable[[str, Any], str]= 
        lambda x, args: eval(x), fargs_extension=None):
    
    def encode_text(text: str) -> bytes:
        text = text.replace(r'[\n]', '\n')
        text = text.replace(r'[\r]', '\r')
        if replace_map is not None:
            for k, v in replace_map.items():
                text = text.replace(k, v)

        tmpio = BytesIO()
        if text.find("{{") == -1:
            if tbl: tmpio.write(encode_tbl(text, tbl, override_fail))
            else: tmpio.write(text.encode(encoding, errormode))
        else:
            start = 0
            while start + 2 < len(text):
                end = text.find('{{', start)
                if end < 0: break
                if tbl: tmpio.write(encode_tbl(text[start: end], tbl, override_fail))
                else: tmpio.write(text[start: end].encode(encoding, errormode))
                start = end + 2
                end = text.find('}}', start)
                if end < 0: 
                    raise ValueError(f"pattern not closed at {text}")
                _bytes = f_extension(text[start:end], fargs_extension)
                tmpio.write(_bytes)
                start = end + 2
        tmpio.write(b'\x00')
        return tmpio.getbuffer()

    def load_orgtext(ftext, orgdata) -> ftextpack_textinfo_t:
        addr, size, text = ftext['addr'], ftext['size'], ftext['text']
        textbytes = orgdata[addr: addr+size]
        textcrc = zlib.crc32(textbytes)
        textoff = 0
        
        if textcrc in crcmap:
            if pack_nodup:
                print(f"drop duptext {textcrc:x}: {addr:x}|{size:x}|{text}") 
                return None
        crcmap.update({textcrc: ftext})

        if pack_org: 
            textoff = bufio.tell()
            bufio.write(textbytes)
        textinfo = ftextpack_textinfo_t.from_buffer_copy(
            struct.pack("4I", textcrc, textoff, addr, size))
        return textinfo

    def load_nowtext(ftext) -> ftextpack_textinfo_t:
        addr, size, text = ftext['addr'], ftext['size'], ftext['text']
        textoff = bufio.tell()
        textbytes = encode_text(text)
        bufio.write(textbytes)
        textinfo = ftextpack_textinfo_t.from_buffer_copy(
            struct.pack("4I", 0, textoff, addr, len(textbytes)))
        return textinfo

    def load_file(ftextpath, orgpath):
        ftexts1, ftexts2= load_ftext(ftextpath)
        print(f"load {ftextpath} with {len(ftexts1)} texts")
        assert(len(ftexts1) == len(ftexts2))
    
        with open(orgpath, 'rb') as fp: orgdata = fp.read()
        for j, (f1, f2) in enumerate(zip(ftexts1, ftexts2)):
            org = load_orgtext(f1, orgdata)
            if not org: continue
            now = load_nowtext(f2)
            info = ftextpack_info_t()
            info.org = org; info.now = now
            infos.append(info)
    
    # prepare enviroment
    bufio = BytesIO()
    crcmap = dict() # {crc: ftext}
    infos: List[ftextpack_info_t] = []
    tbl = load_tbl(tblobj) if tblobj and tblobj!="" else None
    if override_fail=="": 
        override_fail = None
        errormode = 'strict'
    else: errormode = 'ignore'
    
    # load files
    if os.path.isfile(ftextpath): ftextpaths = [ftextpath]
    else:  ftextpaths = glob(os.path.join(ftextpath, "*.txt"))
    if os.path.isfile(orgpath): orgpaths = [orgpath]
    else: orgpaths = list(map(lambda x: 
        os.path.join(orgpath, os.path.splitext(os.path.basename(x))[0]), ftextpaths))
    [load_file(f1, f2) for (f1, f2) in zip(ftextpaths, orgpaths)]

    # sort info
    if sortby=="hash": infos.sort(key = lambda x: x.org.hash)
    elif sortby == "addr": infos.sort(key = lambda x: (x.org.addr<<32) + x.org.size)
    else: raise ValueError(f"unknow sorby type {sortby}")
    
    # make header and write to file
    n = len(infos)
    index = ftextpack_index_t()
    index.magic = b'fp01'
    index.count = n
    if pack_compact:
        index.offset = sizeof(ftextpack_index_t) - sizeof(ftextpack_info_t) + n*sizeof(ftextpack_textinfo_t)
    else:
        index.offset = sizeof(ftextpack_index_t) + (n-1)*sizeof(ftextpack_info_t)
    index.reserved = 0
    with open(outpath, 'wb+') as fp:
        fp.write(index)
        fp.seek(-sizeof(ftextpack_info_t), 1)
        for info in infos:
            if pack_compact:
                fp.write(struct.pack("<4I", 
                    info.org.hash, info.now.offset, info.org.addr, info.now.size))
            else: fp.write(info)
        fp.write(bufio.getbuffer())

def debug():
    pass

def cli(cmdstr=None):
    parser = argparse.ArgumentParser(description=g_description)
    parser.add_argument("ftextpath", type=str, help="ftext file or dir")
    parser.add_argument("orgpath", type=str, help="org file or dir")
    parser.add_argument("-o", "--outpath", type=str, default="data.fp01")
    parser.add_argument("-e", "--encoding", type=str, default='utf8', help="use encoding for packing text")
    parser.add_argument("--tbl", type=str, default="", help="use custome tbl for packing text")
    parser.add_argument("--sortby", type=str, default="hash", choices=(["hash", "addr"]), help="sorted text after packing")
    parser.add_argument("-r", "--replace",  action='append', type=str, nargs=2, metavar=('src', 'dst'), 
                        help="replace the text before encoding")
    parser.add_argument('--override_fail', type=int, default=[], nargs='+', metavar="encbyte", 
                        help="overide the encoding error with char")
    parser.add_argument("--pack_org", action='store_true', help="pack origin data for reference")
    parser.add_argument('--pack_compact', action='store_true', help='use compact structure for packing')
    parser.add_argument('--pack_nodup', action='store_true', help="don't pack dup text on pack")

    if cmdstr is None: args = parser.parse_args()
    else: args = parser.parse_args(cmdstr.split(' '))

    replace_map = dict()
    for t in args.replace: replace_map[t[0]] = t[1]
    override_fail = None if len(args.override_fail)==0 else args.override_fail

    ftextpack(args.ftextpath, args.orgpath, args.outpath, 
        encoding=args.encoding, tblobj=args.tbl, 
        sortby=args.sortby, 
        replace_map=replace_map, 
        override_fail=override_fail,
        pack_org=args.pack_org, 
        pack_nodup=args.pack_nodup,
        pack_compact=args.pack_compact)

if __name__ == '__main__':
    # debug()
    cli()

"""
history:
v0.1, initial version with data.fp01
v0.1.1, add allow_compat for smaller memory use
"""
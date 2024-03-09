# -*- coding: utf-8 -*-
__description__ = """
A flexble format with low memory implementation
    v0.2.1, developed by devseed

    use ftextpack.h to load dynamicly    
"""

import os
import struct
import argparse
import logging
import zlib
from ctypes import *
from io import BytesIO
from glob import glob
from dataclasses import dataclass, field
from typing import Callable, List

try:
    from libutil import writebytes, filter_loadfiles, ftext_t, load_batch, load_ftext, load_tbl
    from libtext import encode_extend
except ImportError:
    exec("from libutil_v600 import writebytes, filter_loadfiles, ftext_t, load_batch, load_ftext, load_tbl")
    exec("from libtext_v610 import encode_extend")

__version__ = 210

# ftextpack functions
class ftextpack_textinfo_t(Structure):
    _fields_ = [
        ('hash', c_uint32), 
        ('offset', c_uint32),
        ('addr', c_uint32),
        ('size', c_uint32)
    ]
    def dummy(self): # for intelligence auto complete
        self.hash, self.size, self.addr, self.offset = 4*[0]

class ftextpack_info_t(Structure):
    _fields_ = [
        ('org', ftextpack_textinfo_t),
        ('now', ftextpack_textinfo_t)
    ]
    def dummy(self):
        self.org: ftextpack_textinfo_t = None
        self.now: ftextpack_textinfo_t = None

class ftextpack_index_t(Structure):
    _fields_ = [
        ('magic', c_char * 4), 
        ('count', c_uint32), 
        ('offset', c_uint32),
        ('reserved', c_uint32),
        ('info', ftextpack_info_t * 1)
    ]
    def dummy(self):
        self.magic, self.count, self.offset, self.reserved, self.info = 5*[0]

@dataclass
class Fpack:
    index: ftextpack_index_t= ftextpack_index_t()
    infos: List[ftextpack_info_t]= field(default_factory=list)
    content: bytes = b""

def pack_ftexts(binobjs, ftextobjs,
        outobj, encoding="utf8", tblobj=None, *, text_noeval=False, 
        text_replace=None, bytes_fallback=None, pack_sort="hash", 
        pack_org=False, pack_nodup=False, pack_compact=False, 
        f_before: Callable[[bytes, ftext_t], str] = None, 
        f_after: Callable[[bytes, memoryview, bytes, ftext_t], bytes] = None) -> Fpack:

    def _load_org(t: ftext_t, srcdata: bytes, crcmap) -> ftextpack_textinfo_t:
        start = 0
        textbytes = srcdata[t.addr: t.addr+t.size]
        tcrc = zlib.crc32(textbytes)
        if tcrc in crcmap and pack_nodup:
            logging.info(f"dropdup [crc=0x{tcrc:x} addr=0x{t.ddr:x} size=0x{t.size:x} text='{t.text}]'") 
            return None
        if pack_org: start = bufio.tell(); bufio.write(textbytes); bufio.write(b'\x00')
        tmp = struct.pack("4I", tcrc, start, t.addr, t.size)
        textinfo = ftextpack_textinfo_t.from_buffer_copy(tmp)
        crcmap.update({tcrc: t})
        return textinfo

    def _load_now(t: ftext_t, srcdata: bytes) -> ftextpack_textinfo_t:
        text = t.text
        start = bufio.tell()
        text = f_before(srcdata, t) if f_before else t.text
        for k, v in text_replace.items(): text = text.replace(k, v)
        encbytes = encode_extend(text, enc, enc_error, text_noeval)
        if f_after: encbytes = f_after(srcdata, None, encbytes, t)
        tmp = struct.pack("4I", 0, start, t.addr, len(encbytes))
        textinfo = ftextpack_textinfo_t.from_buffer_copy(tmp)
        bufio.write(encbytes)
        bufio.write(b'\x00')
        return textinfo
    
    @filter_loadfiles([1])
    def _load_pair(ftextobj, binobj) -> List[ftextpack_info_t]:
        ftexts1, ftexts2 = load_ftext(ftextobj)
        logging.info(f"load {repr(ftextobj)} with {len(ftexts1)} texts")
        assert(len(ftexts1) == len(ftexts2))

        srcdata = memoryview(binobj)
        for j, (t1, t2) in enumerate(zip(ftexts1, ftexts2)):
            org = _load_org(t1, srcdata, crcmap)
            if not org: continue
            now = _load_now(t2, srcdata)
            info = ftextpack_info_t()
            info.org, info.now = org, now
            infos.append(info)

    def save_fpack(fpack: Fpack, outobj, pack_compact=False) -> None:
        fp = outobj if type(outobj)!=str else BytesIO() 
        start = fp.tell()
        index, infos, content =fpack.index, fpack.infos, fpack.content
        fp.write(index)
        fp.seek(-sizeof(ftextpack_info_t), 1)
        for info in infos:
            if pack_compact: 
                tmp = info.org.hash, info.now.offset, info.org.addr, info.now.size
                fp.write(struct.pack("<4I", *tmp))
            else: fp.write(info)
        fp.write(content)
        end = fp.tell()
        if type(outobj) == str: writebytes(outobj, fp.getvalue()); fp.close()
        logging.info(f"save 0x{end-start:x} bytes to {repr(outobj)}")

    # prepare enviroment
    bufio = BytesIO()
    crcmap = dict() # {crc: ftext}
    infos: List[ftextpack_info_t] = []
    tbl = load_tbl(tblobj)
    enc = tbl if tbl else encoding
    enc_error = bytes_fallback if tbl else ("ignore" if bytes_fallback else "strict")
    text_replace = text_replace if text_replace else dict()
    
    # load files
    if type(ftextobjs) == str:
        _pattern = os.path.join(ftextobjs, "*.txt")
        ftextobjs = [ftextobjs] if os.path.isfile(ftextobjs) else glob(_pattern)
    if type(binobjs) == str:
        _fbfunc = lambda x: os.path.join(binobjs, os.path.splitext(os.path.basename(x))[0])
        binobjs = [binobjs] if os.path.isfile(binobjs) else list(map(_fbfunc, ftextobjs))
    for (f1, f2) in zip(ftextobjs, binobjs): _load_pair(f1, f2)

    # sort info
    if pack_sort=="hash": infos.sort(key = lambda x: x.org.hash)
    elif pack_sort == "addr": infos.sort(key = lambda x: (x.org.addr<<32) + x.org.size)
    else: raise ValueError(f"unknow sorby type {pack_sort}")
    
    # make header
    n = len(infos)
    index = ftextpack_index_t()
    index.magic = b'fp01'
    index.count = n
    index.reserved = 0
    size_index = sizeof(ftextpack_index_t)
    size_info = sizeof(ftextpack_info_t)
    size_textinfo = sizeof(ftextpack_textinfo_t)
    if not pack_compact: index.offset = size_index + (n-1)*size_info
    else: index.offset = size_index - size_info + n*size_textinfo

    fpack = Fpack(index, infos, bufio.getbuffer()[:bufio.tell()])
    if outobj: save_fpack(fpack, outobj, pack_compact)
    return fpack

def cli(cmdstr=None):
    def filter_paths(args):
        if args.batch:
            binpaths = load_batch(args.binpath)
            ftextpaths = load_batch(args.ftextpath)
            outpaths = load_batch(args.outpath)
        else:
            binpaths = [args.binpath]
            ftextpaths = [args.ftextpath]
            outpaths = [args.outpath if args.outpath!="" else None]
        n = min(len(binpaths), len(ftextpaths), len(outpaths))
        return binpaths, ftextpaths, outpaths, n
    
    def filter_cfgs(args):
        tbl = load_tbl(args.tbl)
        text_replace = dict((t[0], t[1]) for t in  args.text_replace) if args.text_replace else None
        bytes_fallback = bytes.fromhex(args.bytes_fallback) if args.bytes_fallback else None
        return tbl, text_replace, bytes_fallback

    def cmd_pack(args):
        logging.debug(repr(args))
        binpaths, ftextpaths, outpaths, n = filter_paths(args)
        tbl, text_replace, bytes_fallback = filter_cfgs(args)
        for i, (binpath, ftextpath, outpath) in enumerate(zip(binpaths, ftextpaths, outpaths)):
            if args.batch: logging.info(f"batch {i+1}/{n} [binpath={binpath} ftextpath={ftextpath} outpath={outpath}]")
            pack_ftexts(binpath, ftextpath, outpath, 
                encoding=args.encoding, tblobj=tbl, text_noeval=args.text_noeval, 
                text_replace=text_replace, bytes_fallback=bytes_fallback, 
                pack_sort=args.pack_sort, pack_org=args.pack_org, 
                pack_nodup=args.pack_nodup, pack_compact=args.pack_compact)

    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument("binpath", help="bin file or dir")
    parser.add_argument("ftextpath", help="ftext file or dir")
    parser.add_argument("-o", "--outpath", default="data.fp01")
    parser.add_argument("--batch", action="store_true", 
        help="use batch mode, the binpath, ftextpath, outpath should be the list file")
    parser.add_argument("-e", "--encoding", default='utf-8', help="use encoding for packing text")
    parser.add_argument("-t", "--tbl", default=None, help="use custome tbl for packing text")
    parser.add_argument("-r", "--text_replace", default=None, type=str, 
        action='append', nargs=2, metavar=('src', 'dst'), help="replace the text before encoding")
    parser.add_argument("--log_level", default="info", help="set log level", 
        choices=("none", "critical", "error", "warnning", "info", "debug"))
    parser.add_argument("--text_noeval", action="store_true",  help="disable eval like {{b'\x00'}}")
    parser.add_argument('--bytes_fallback', type=str, default=None, help="bytes after tbl failed")
    parser.add_argument("--pack_sort", default="hash", 
        choices=("hash", "addr"), help="sorted text after packing")
    parser.add_argument("--pack_org", action='store_true', help="pack origin data for reference")
    parser.add_argument('--pack_compact', action='store_true', help='use compact structure for packing')
    parser.add_argument('--pack_nodup', action='store_true', help="don't pack dup text on pack")

    args = parser.parse_args(cmdstr.split(' ') if cmdstr else None)
    loglevel = args.log_level if hasattr(args, "log_level") else "info"
    logging.basicConfig(level=logging.getLevelName(loglevel.upper()), 
                        format="%(levelname)s:%(funcName)s: %(message)s")
    cmd_pack(args)

if __name__ == '__main__':
    cli()

"""
history:
v0.1, initial version with data.fp01
v0.1.1, add allow_compat for smaller memory use
v0.2, remake according to libtext v0.6
v0.2.1, use batch operations to improve performance
"""
 # -*- coding: utf-8 -*-
__description__ = """
A font tool (remake) for tbl and glphy operations
    v0.3, developed by devseed
"""

import os
import math
import copy
import struct
import logging
import argparse
from io import BytesIO
from typing import Callable, Union, Tuple, List, Dict, Set

import numpy as np
from PIL import ImageFont, ImageDraw, Image

__version__ = 300

try:
    from libutil import tile_t, tbl_t, writebytes, writeimage, filter_loadfiles, filter_loadimages, valid_tile, load_tbl, save_tbl
except ImportError:
    exec("from libutil_v600 import tile_t, tbl_t, writebytes, writeimage, filter_loadfiles, filter_loadimages, valid_tile, load_tbl, save_tbl")

# tbl generations
def make_cp932_tbl(range_full=True, text_fallback="♯", out_failed: List[int]=None) -> List[tbl_t]: 
    def _process(high, low):
        tcode = struct.pack('<BB', high, low)
        try:
            tchar = tcode.decode('sjis')
        except  UnicodeDecodeError:
            tchar = text_fallback          
            if out_failed!=None: out_failed.append(len(tbl))
        tbl.append(tbl_t(tcode, tchar))

    tbl = []
    for low in range(0x20, 0x7f): # asci
        tcode = struct.pack('<B', low)
        tbl.append(tbl_t(tcode, tcode.decode("sjis")))
    
    for high in range(0x81, 0xa0): # 0x81-0x9F
        for low in range(0x40, 0xfd):
            if low==0x7f: continue
            _process(high, low)
    
    # 0xE0-0xEF, sometimes 0xE0~-0xEA
    end = 0xf0 if range_full is True else 0xeb
    for high in range(0xe0, end): 
        for low in range(0x40, 0xfd):
            if low==0x7f: continue
            _process(high, low)

    logging.info(f"make tbl cp932 with {len(tbl)} chars")
    return tbl  

def make_cp936_tbl(range_kanji=False) -> List[tbl_t]:
    tbl: List[tbl_t] = []
    if range_kanji is False:
        for low in range(0x20, 0x7f): # asci
            tcode = struct.pack('<B', low)
            tbl.append(tbl_t(tcode, tcode.decode("gb2312")))
        
        for low in range(0xa1, 0xfe): # Punctuation
            tcode = struct.pack('<BB', 0xa1, low)
            tbl.append(tbl_t(tcode, tcode.decode("gb2312")))
        
        for low in range(0xa1, 0xfe): # fullwidth charactor
            tcode = struct.pack('<BB', 0xa3, low)
            tbl.append(tbl_t(tcode, tcode.decode("gb2312")))

        for low in range(0xa1, 0xf4): # hirakana
            tcode = struct.pack('<BB', 0xa4, low)
            tbl.append(tbl_t(tcode, tcode.decode("gb2312")))

        for low in range(0xa1, 0xf7): # katakana 
            tcode = struct.pack('<BB', 0xa5, low)
            tbl.append(tbl_t(tcode, tcode.decode("gb2312")))

    for high in range(0xb0, 0xf8): # Chinese charactor
        for low in range(0xa1, 0xff):
            if high == 0xd7 and 0xfa <= low <= 0xfe: continue
            tcode = struct.pack('<BB', high, low)
            tbl.append(tbl_t(tcode, tcode.decode("gb2312")))

    logging.info(f"make tbl cp936 with {len(tbl)} chars")
    return tbl

# tbl operations
def replace_tchar_tbl(tbl: List[tbl_t], replace: Dict[str, str]) -> List[tbl_t]:
    f = lambda x: tbl_t(x.tcode, replace[x.tchar] if x.tchar in replace else x.tchar) 
    return list(map(f, tbl))

def replace_encoding_tbl(tbl:List[tbl_t], encoding:str) -> List[tbl_t]:
    f = lambda x: tbl_t(x.tchar.encode(encoding), x.tchar) 
    return list(map(f, tbl))

def diff_tchar_tbl(tbl1: List[tbl_t], tbl2: List[tbl_t]) -> Tuple[Set, Set, Set]:
    """
    compare the tchar in tbl1 and tbl2
    :return: t1only, t2only, t1t2common
    """

    t1set = set(t.tchar for t in tbl1)
    t2set = set(t.tchar for t in tbl2)
    return t1set - t2set, t2set - t1set,  t1set & t2set

def align_tbl(tbl: List[tbl_t], gap_map: Dict[int, int] = None, gap_static=True, 
        tbl_padding: tbl_t=tbl_t(b'\xff', '')) -> List[tbl_t]:
    """
    manualy align tbl for glphys 
    by adding offset(+-) in gap_map at some position 
    :param gap_map: {pos: shift}, + for padding, - for skip
    :param gap_static: use static index for gap
    """

    skip = 0
    gap_pos = 0
    gap_map = dict() if gap_map is None else gap_map
    tbl_aligned = []
    for i, t in enumerate(tbl):
        if skip > 0: skip -= 1; continue # while skip not finish yet
        if gap_static: gap_pos = i # use tbl index
        elif gap_pos != -1:  gap_pos = len(tbl_aligned) # use tbl_aligned index
        if gap_pos in gap_map: # current position in gap map
            n = gap_map[gap_pos]
            if  n < 0: skip = -n - 1; gap_pos = -1; continue 
            elif n > 0: 
                for j in range(n): tbl_aligned.append(tbl_padding) # dup by padding
                tbl_aligned.append(t); gap_pos = 0 # reset to enable gap
        else: tbl_aligned.append(t); gap_pos = 0
    return tbl_aligned

def merge_simple_tbl(tbl1: List[tbl_t], tbl2: List[tbl_t], text_fallback="♯") -> List[tbl_t]:
    """
    merge simply as the tcode in tbl1 and the tchar in tbl2
    :return: based on tbl1
    """

    tbl3 = []
    for i, t in enumerate(tbl1):
        tchar = tbl2[i].tchar if i < len(tbl2) else text_fallback 
        tbl3.append(tbl_t(t.tcode, tchar))
    logging.info(f"merged tbl1(length={len(tbl1)}) and tbl2(length={len(tbl2)})")
    return tbl3

def merge_intersect_tbl(tbl1: List[tbl_t], tbl2: List[tbl_t], 
        reserved: Set=None, range_find=range(-1, -1, -1)) -> List[tbl_t]:
    """
    merge with intersection (tbl1.tcode, tbl2.tchar)
    as the common tchar in the same position
    :params reserved: reserved position for not override
    """

    def iter_avail(notuse: Set, r: range):
        for i in r:
            if i in notuse: continue
            yield i 

    r = range_find
    r = range(len(tbl1)-1, r.stop, r.step) if r.start < 0 else r
    reserved = set() if reserved is None else reserved
    if len(tbl1) - len(tbl2) < len(reserved):
        logging.error(f"tbl2 not enough space, {len(tbl1)}-{len(tbl2)}<{len(reserved)}")
        return None

    t1set, t2set, t12set = diff_tchar_tbl(tbl1, tbl2)
    t2map = dict((t.tchar, i)for i, t in enumerate(tbl2))
    logging.info(f"t1set t2set t3set size=({len(t1set)}, {len(t2set)}, {len(t12set)})")
    
    tbl3 = copy.deepcopy(tbl1)
    notuse = reserved | t12set
    index_add = [t2map[tchar] for tchar in t2set]
    g = iter_avail(notuse, r)
    for idx2 in index_add:
        try:
            idx1 = next(g)
            tbl3[idx1] = tbl_t(tbl1[idx1].tcode, tbl2[idx2].tchar)
        except StopIteration:
            logging.error(f"rebuild_tbl error: no replacespace!, i={idx2}")
            return None
    return tbl3

# font operations
def encode_index_palette(img: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """
    palette (n, 4), img (h, w, 4) -> index(h, w)
    """

    DIS = 0x7FFFFFFF * np.ones(img.shape[:2], np.uint32)
    IDX = np.zeros(img.shape[:2], np.uint32)
    for i in range(palette.shape[0]):
        TDIS = np.linalg.norm(img - palette[i], 1, axis=-1) # (h, w)
        IDX[...] = i *(TDIS < DIS) + IDX * (TDIS >= DIS)
        DIS[...] = TDIS *(TDIS < DIS) + DIS * (TDIS >= DIS)
    return IDX

def decode_index_palette(index: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """
    palette (n, 4), index(h, w) -> img(h, w, 4)
    """

    return palette[index, :]

def encode_glphy(tiledata: np.ndarray, tilesize, tilew, tileh, tilebpp, palette: np.ndarray, img: np.ndarray):
    h, w = img.shape[0], img.shape[1]
    datasize = h * w * tilebpp // 8
    if tilebpp >= 24:
        tiledata[:datasize] = img[..., :tilebpp//8].ravel()
    else:
        if palette is not None: IDX = encode_index_palette(img, palette)
        else: IDX = img[..., 3].astype(np.uint16) / 255 * 2**tilebpp
        if tilebpp <= 8:
            n = 8//tilebpp
            RADIX = np.power(2, np.arange(n, dtype=np.uint8)*tilebpp)
            tiledata[:datasize] = np.sum(IDX.reshape((-1, n)) * RADIX, -1)
        elif tilebpp==16:
            tiledata[:datasize] = IDX.ravel()

def decode_glphy(tiledata: np.ndarray, tilesize, tilew, tileh, tilebpp, palette: np.ndarray, img: np.ndarray):  
    w, h = tilew, tileh
    datasize = h * w * tilebpp // 8
    if tilebpp <= 16:
        if tilebpp <= 8:
            n = 8//tilebpp # 2bpp, 4 index extend in 1bytes
            Y, X = np.meshgrid(np.arange(tileh, dtype=np.uint32), 
                               np.arange(tilew, dtype=np.uint32), indexing='ij')
            POS = Y * tilew + X # (h, w)
            SHIFT = (POS % n) * tilebpp
            MASK = ((1<<tilebpp)-1) << SHIFT
            IDX = (tiledata[POS//n] & MASK) >> SHIFT # (h, w)
        elif tilebpp==16:
            IDX = tiledata.view(np.uint16)
        if palette is None:                 
            R = G = B = 255 * np.ones((h, w), dtype=np.uint8)
            A = IDX * 255 // (2**tilebpp -1)
            PIXEL = np.dstack([R, G, B, A])
        else: 
            PIXEL = decode_index_palette(IDX, palette)
        img [:] = PIXEL
    elif tilebpp >= 24:
        n = tilebpp//8
        img[..., :n] = tiledata[:datasize].reshape((h, w, n))

@filter_loadfiles(1)
def make_image_font(tblobj: Union[str, List[tbl_t]], ttfobj: Union[str, bytes],
        tileinfo: tile_t, outpath=None, *, n_row=64, n_render=3, 
        render_size=0, render_shift=(0, 0)) -> np.ndarray:
    """
    :param tblobj: tbl path or tbl object
    :param ttfobj: ttf font path or bytes
    :param tile: (w, h) 
    :param n_row: how many glphy in a row
    :param n_render: render multi times to increase brightness
    :param render_size: font size in each render glphy
    :param render_shift: (x, y) in each render glphy
    :return: img
    """

    valid_tile(tileinfo)
    tbl = load_tbl(tblobj) if type(tblobj) != list else tblobj
    n = len(tbl)
    w = n_row*tileinfo.w
    h = math.ceil(n/n_row)*tileinfo.h
    img = np.zeros((h, w, 4), dtype=np.uint8)
    logging.info(f"render font to image ({w}X{h}), {n} glphys {tileinfo.w}x{tileinfo.h}")
    
    if render_size==0: render_size=min(tileinfo.w, tileinfo.h)
    font = ImageFont.truetype(BytesIO(ttfobj), render_size)
    pil = Image.fromarray(img)
    pil.readonly = False # this to make share the memory
    draw = ImageDraw.Draw(pil)

    for i, t in enumerate(tbl):
        x = render_shift[0] + (i%n_row)*tileinfo.w
        y = render_shift[1] + (i//n_row)*tileinfo.h 
        draw.text((x,y), t.tchar, fill=(255,255,255,255), font=font, align="center")
    if n_render > 1: # alpha blending for overlap
        alpha = img[..., 3].astype(np.float32)/255.0
        for i in range(n_render-1): 
            alpha = alpha + (1-alpha)*alpha
        img[..., 3] = (alpha*255).astype(np.uint8)

    if outpath: writeimage(outpath, img)
    return img

@filter_loadfiles(1)
def make_tile_font(tblobj: Union[str, List[tbl_t]], ttfobj: Union[str, bytes],
        tileinfo: tile_t, outpath=None, *, n_render=3, render_size=0, render_shift=(0, 0), 
        f_encode: Callable=encode_glphy, palette=None) -> np.ndarray:
    """
    :param tblobj: tbl path or tbl object
    :param ttfobj: ttf font path or bytes
    :param tileinfo: (h, w, bpp, size) 
    :param n_row: how many glphy in a row
    :param n_render: render multi times to increase brightness
    :param render_size: font size in each render glphy
    :param render_shift: (x, y) in each render glphy
    :param f_encode: f(tiledata, tilesize, tilew, tileh, tilebpp, palette, img)
    :return: img
    """

    valid_tile(tileinfo)
    tbl = load_tbl(tblobj) if type(tblobj) != list else tblobj
    n = len(tbl)
    logging.info(f"to {n} {tileinfo} glphys" + \
        (f", with palatte {repr(palette.shape)}" if palette is not None else ""))
    if render_size==0: render_size=min(tileinfo.w, tileinfo.h)
    font = ImageFont.truetype(BytesIO(ttfobj), render_size)
    tileimg = np.zeros([tileinfo.h, tileinfo.w, 4], dtype=np.uint8)
    tiledata = np.zeros(n*tileinfo.size, dtype=np.uint8)
    pil = Image.fromarray(tileimg)
    pil.readonly = False
    draw = ImageDraw.Draw(pil)

    for i, t in enumerate(tbl):
        draw.text((render_shift[0],render_shift[1]), 
            t.tchar, fill=(255,255,255,255), font=font, align="center")
        if n_render > 1: # alpha blending for overlap
            alpha = tileimg[..., 3].astype(np.float32)/255.0
            for _ in range(n_render-1): 
                alpha = alpha + (1-alpha)*alpha
            tileimg[..., 3] = (alpha*255).astype(np.uint8)
        f_encode(tiledata[i*tileinfo.size: (i+1)*tileinfo.size], 
                    tileinfo.size, tileinfo.w, tileinfo.h, tileinfo.bpp, palette, tileimg)
        tileimg.fill(0)
    if outpath: writebytes(outpath, tiledata.tobytes())
    return tiledata

def extract_glphy(tileimg, outdir, i, tbl: List[tbl_t]=None) -> str:
    """
    extract a glphy to outdir, with tbl encoded
    warning, better not write to zip file, very slow here
    """

    def join_path(path, name):
        if len(path) > 3 and path[-4:].lower() == ".zip":
            path += ">" + name
        elif ".zip" in path:
            path = path.rstrip("/") + "/" + name
        else: path = os.path.join(path, name)
        return path
        
    def save_jpg(outpath, tileimg):
        A = tileimg[..., 3:].astype(np.float32)/255 
        RGB = tileimg[..., :3].astype(np.float32)/255
        writeimage(outpath, (RGB*A*255).astype(np.uint8), img_format="JPEG")

    if tbl:
        try:
            reject =  {'<', '>', '|', ':', '*', '&', '/', '\\', '"', "'"}
            tchar = tbl[i].tchar
            ucode = ord(tchar) if len(tchar) > 0 else 0
            name = "%05d_u%04X_%s"%(i, ucode, tchar) if tbl else "%05d"%(i)
            name = "".join(list(filter(lambda x: x not in reject, name)))
            if outdir:
                outpath = join_path(outdir, name + ".jpg")
                save_jpg(outpath, tileimg)
        except (IOError) as e:
            name = "%05d_u%04X"%(i, ucode) if tbl else "%05d"%(i)
            if outdir:
                outpath = join_path(outdir, name + ".jpg")
                save_jpg(outpath, tileimg)
    else:
        name = "%05d"%(i)
        outpath = join_path(outdir, name + ".jpg")
        save_jpg(outpath, tileimg)
    logging.debug(f'[i={i} {repr(tbl[i] if tbl else "")} name={name}]')
    return name

@filter_loadimages((1, "RGBA"))
def extract_image_font(tblobj: Union[str, List[tbl_t]], 
        inobj: Union[str, np.ndarray], tileinfo: tile_t, outdir=None) -> List[str]:
    """
    extract the glphys from image to outdir
    :param inobj: rgba image
    """
    
    valid_tile(tileinfo)
    img = inobj
    h, w = img.shape[0], img.shape[1]
    n_row = w//tileinfo.w
    tbl = load_tbl(tblobj) if tblobj!=None else None
    n = len(tbl) if tbl else w//tileinfo.w * h//tileinfo.h
    n = min(n, w//tileinfo.w * h//tileinfo.h)
    logging.info(f"extract {n} {tileinfo} glphys")
    names = n*[None]
    for i in range(n):
        x, y = i%n_row*tileinfo.h, i//n_row*tileinfo.w
        tileimg = img[y: y+tileinfo.h, x: x+tileinfo.w, ...]
        names.append(extract_glphy(tileimg, outdir, i, tbl))

    return names

@filter_loadfiles(1)
def extract_tile_font(tblobj: Union[str, List[tbl_t]], 
        inobj: Union[str, np.ndarray], tileinfo: tile_t, outdir=None, palette=None) -> List[str]:
    """
    extract the glphys from tiles to outdir
    :param inobj: tiledata
    """

    valid_tile(tileinfo)
    tbl = load_tbl(tblobj) if tblobj!=None else None
    tiledata = np.frombuffer(inobj, dtype=np.uint8)
    n = len(tbl) if tbl else len(inobj)//tileinfo.size
    n = min(n, len(inobj)//tileinfo.size)
    logging.info(f"{n} {tileinfo} glphys" + \
        (f", with palatte {repr(palette.shape)}" if palette is not None else ""))
    names = n*[None]
    tileimg = np.zeros([tileinfo.h, tileinfo.w, 4], dtype=np.uint8)
    for i in range(n):
        decode_glphy(tiledata[i*tileinfo.size: (i+1)*tileinfo.size], 
            tileinfo.size, tileinfo.w, tileinfo.h, tileinfo.bpp, palette, tileimg)
        names.append(extract_glphy(tileimg, outdir, i, tbl))

    return names

def cli(cmdstr=None):
    def cmd_tbl_replace(tbl, tchar_replace, tcode_encoding):
        if tchar_replace: tbl = replace_tchar_tbl(tbl, tchar_replace)
        if tcode_encoding: tbl = replace_encoding_tbl(tbl, tcode_encoding)
        return tbl

    def cmd_tbl_make(args):
        logging.debug(repr(args))
        tchar_replace = dict((t[0], t[1]) for t in  args.tchar_replace) if args.tchar_replace else None
        if args.codepage == "cp932":
            tbl = make_cp932_tbl(range_full=args.range_full, text_fallback=args.text_fallback)
        elif args.codepage == "cp936":
            tbl = make_cp936_tbl(range_kanji=args.range_kanji)
        tbl = cmd_tbl_replace(tbl, tchar_replace, args.tcode_encoding)
        save_tbl(tbl, args.outpath)

    def cmd_tbl_align(args):
        logging.debug(repr(args))
        tchar_replace = dict((t[0], t[1]) for t in  args.tchar_replace) if args.tchar_replace else None
        tbl_padding = tbl_t(bytes.fromhex(args.tbl_padding[0]), args.tbl_padding[1])
        gap_map =  dict((t[0], t[1]) for t in  args.gap) if args.gap else None
        tbl = load_tbl(args.tbl1path)
        tbl = align_tbl(tbl, gap_map=gap_map, gap_static=args.gap_static, tbl_padding=tbl_padding)
        tbl = cmd_tbl_replace(tbl, tchar_replace, args.tcode_encoding)
        save_tbl(tbl, args.outpath)

    def cmd_tbl_merge(args):
        logging.debug(repr(args))
        tchar_replace = dict((t[0], t[1]) for t in  args.tchar_replace) if args.tchar_replace else None
        tbl1, tbl2 = load_tbl(args.tbl1path), load_tbl(args.tbl2path)
        if args.intersect: 
            find_range = range(*args.range_find)
            reserved = set()
            if args.range_reserved:
                for r in args.range_reserved:
                    reserved |= set(i for i in range(r[0], r[1]))
            tbl3 = merge_intersect_tbl(tbl1, tbl2, reserved=reserved, range_find=find_range)
        else: tbl3 = merge_simple_tbl(tbl1, tbl2, args.text_fallback)
        cmd_tbl_replace(tbl3, tchar_replace, args.tcode_encoding)
        save_tbl(tbl3, args.outpath)

    def cmd_font_make(args):
        logging.debug(repr(args))
        tileinfo = tile_t(args.tilew, args.tileh, args.tilebpp, args.tilesize)
        if args.format == "image":
            make_image_font(args.tbl, args.ttfpath, tileinfo, outpath=args.outpath, 
                n_row=args.n_row, n_render=args.n_render, 
                render_size=args.render_size, render_shift=args.render_shift)
        elif args.format == "tile":
            palette = bytes.fromhex(args.palette) if args.palette else None
            if palette: palette = np.frombuffer(palette, dtype=np.uint8).reshape((-1, 4))
            make_tile_font(args.tbl, args.ttfpath, tileinfo, args.outpath, 
                n_render=args.n_render, render_size=args.render_size, 
                render_shift=args.render_shift, palette=palette)

    def cmd_font_extract(args):
        logging.debug(repr(args))
        tileinfo = tile_t(args.tilew, args.tileh, args.tilebpp, args.tilesize)
        if args.format == "image":
            extract_image_font(args.tbl, args.fontpath, tileinfo, outdir=args.outpath)
        elif args.format == "tile":
            palette = bytes.fromhex(args.palette) if args.palette else None
            if palette: palette = np.frombuffer(palette, dtype=np.uint8).reshape((-1, 4))
            extract_tile_font(args.tbl, args.fontpath, tileinfo, outdir=args.outpath, palette=palette)

    p = argparse.ArgumentParser(description=__description__)
    p2 = p.add_subparsers(title="operations")
    p_tbl_make = p2.add_parser("tbl_make", help="make the tbl according encoding")
    p_tbl_align = p2.add_parser("tbl_align", help="align the tbl by some gap shift")
    p_tbl_merge = p2.add_parser("tbl_merge", help="merge the tbl1 tcode and tbl2 tchar")
    p_font_make = p2.add_parser("font_make", help="make font according to tbl")
    p_font_extract = p2.add_parser("font_extract", help="extract font to test align with tbl")
    for t in [p_tbl_make, p_tbl_align, p_tbl_merge, p_font_make, p_font_extract]:
        t.add_argument("-o", "--outpath", default="out")
        t.add_argument("--log_level", default="info", help="set log level", 
            choices=("none", "critical", "error", "warnning", "info", "debug"))
        
    # tbl operations
    for t in [p_tbl_make, p_tbl_align, p_tbl_merge]:
        t.add_argument("--text_fallback", default="♯", help="fallback for decode failed")
        t.add_argument("--tchar_replace", type=str, default=None, 
            metavar=('src', 'dst'), nargs=2, action='append', help="replace the tchar in tbl")
        t.add_argument("--tcode_encoding", default=None, help="re encoding the tcode in tbl")
    p_tbl_make.set_defaults(handler=cmd_tbl_make)
    p_tbl_make.add_argument("codepage", choices=["cp932", "cp936"])
    p_tbl_make.add_argument("--range_full", action="store_true", help="only for cp932")
    p_tbl_make.add_argument("--range_kanji", action="store_true", help="only for cp936")
    p_tbl_align.set_defaults(handler=cmd_tbl_align)
    p_tbl_align.add_argument("tbl1path")
    p_tbl_align.add_argument("--gap", type=int, default=None, 
        metavar=("pos", "skip"), nargs=2, action='append', help="add skip or padding value to align tbl")
    p_tbl_align.add_argument("--gap_static", action="store_true", help="the gap map is based on tbl1")
    p_tbl_align.add_argument("--tbl_padding", type=str, default=('ff', ''), 
        metavar=("tcode", "tchar"), nargs=2, help="paddings for tbl")
    p_tbl_merge.set_defaults(handler=cmd_tbl_merge)
    p_tbl_merge.add_argument("tbl1path")
    p_tbl_merge.add_argument("tbl2path")
    p_tbl_merge.add_argument("--intersect", action="store_true", help="use intersect operation on merge")
    p_tbl_merge.add_argument("--range_reserved", type=int, nargs=2, action='append', 
        metavar=("start", "end"), default=None, help="for intersect, not used range")
    p_tbl_merge.add_argument("--range_find", type=int, nargs=3, default=(-1, -1, -1),
        metavar=("start", "end", "step"), help="for intersect, find interation range")

    # font operations
    for t in [p_font_make, p_font_extract]:
        t.add_argument("--tbl", default=None, help="tbl for making or extracting glphies")
        t.add_argument("--format", required=True, choices=["image", "tile"], help="output format")
        t.add_argument("--palette", type=str, default=None)
        t.add_argument("--tilew", type=int, required=True)
        t.add_argument("--tileh", type=int, default=0)
        t.add_argument("--tilebpp", type=int, default=8)
        t.add_argument("--tilesize",type=int , default=0)
    p_font_make.set_defaults(handler=cmd_font_make)
    p_font_make.add_argument("ttfpath")
    p_font_make.add_argument("--n_row", default=64, help="glphys count in a row")
    p_font_make.add_argument("--n_render", default=3, help="render overlap count")
    p_font_make.add_argument("--render_size", default=0, help="glphy size")
    p_font_make.add_argument("--render_shift", type=int, nargs=2, 
        metavar=("x", "y"), default=(0, 0), help="render shift in a glphy")
    p_font_extract.set_defaults(handler=cmd_font_extract)
    p_font_extract.add_argument("fontpath")

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
v0.1, initial version
v0.1.5, add function save_tbl, fix px48->pt error
v0.1.6, add gray2tilefont, tilefont2gray
v0.1.7. slightly change some function
v0.1.8. add generate_sjis_tbl, merge tbl, find_adding_char
v0.2, add extract_glphys from font image, 
     rebuild_tbl, merge two tbl with the same position of the same char
v0.2.1, align_tbl, manualy align tbl for glphys 
       by the adding offset(+-) at some position  
v0.2.2, replace_char, to replace useless char to new char in tbl
v0.2.3, fix some problem of encoding, img to tile font alpha value
v0.2.4, add typing hint and rename some functions
v0.2.5, add combine_tbls, update_tbls function for tbl pages
v0.3, remake according to libtext v0.6, add cli support
"""
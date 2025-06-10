# -*- coding: utf-8 -*-
__version__ = "0.3.1"
__description__ = f"""
A image tool (remake) for image encoding or decoding, 
all the intermediate format is rgba, index in alpha channel
    v{__version__}, develope by devseed
"""

import math
import logging
import argparse
from queue import Queue
from typing import Union

import numba
import numpy as np
from numba import njit, prange, void, uint8, int32
readonly = lambda dtype, dim: numba.types.Array(dtype, dim, "C", True)

try:
    from libutil import tile_t, writebytes, writeimage, filter_loadfiles, filter_loadimages, load_batch, valid_tile
except ImportError:
    exec("from libutil_v0_6 import tile_t, writebytes, writeimage, filter_loadfiles, filter_loadimages, load_batch, valid_tile")

# methods for generate patterns
def make_swizzle_pattern(tileorder) -> np.ndarray:
    """
    make nxn swizzle, for example n=2, tilen=2, resn=4
        0	1	4	5
        2	3	6	7
        8	9	12	13
        10	11	14	15
        the square side is 2^n
    """

    w = h = 2**tileorder
    res = np.zeros([h, w], dtype=np.int32)
    res[h - 1, w - 1] = h*w - 1
    _que = Queue()
    _que.put((0, 0, w - 1, h - 1))
    while not _que.empty():
        x0, y0, x1, y1 = _que.get()
        dx = int((x1+1-x0) // 2)
        dy = int((y1+1-y0) // 2)
        d = int((y1+1-y0)*(x1+1-x0)//4)
        idx = res[y1][x1]
        res[y1][x0+dx-1] = idx - d
        res[y0+dy-1][x1] = idx - 2*d
        res[y0+dy-1][x0+dx-1] = idx - 3*d
        if d > 1:
            _que.put((x0+dx, y0+dy, x1, y1))
            _que.put((x0, y0+dy, x0+dx-1, y1))
            _que.put((x0+dx, y0, x1, y0+dy-1))
            _que.put((x0, y0, x0+dx-1, y0+dy-1))
    return res

@njit([(int32[:, :])(int32, int32, int32, int32)], parallel=True)
def make_tile_pattern(tilew, tileh, ntiletotal=4, ntilerow=2) -> np.ndarray:
    """
`   make tilehxtilew swizzle, for example 3 tile (2, 4),
        0	1	2	3  8  9  10 11 
        4	5	6	7  12 13 14 15
        16	17	18	19 -1 -1 -1 -1 
        20	21	22	23 -1 -1 -1 -1
        the square side is 2^n`
    """

    w, h = ntilerow*tilew, (ntiletotal + ntilerow - 1)// ntilerow * tileh
    res = -np.ones((h, w), dtype=np.int32)
    for tileidx in prange(ntiletotal):
        for tiley in prange(tileh):
            for tilex in prange(tilew):
                stride_tile = w // tilew                  
                x = (tileidx % stride_tile) * tilew + tilex
                y = (tileidx // stride_tile) * tileh + tiley
                res[y, x] = tileidx * tilew * tileh + tiley * tilew + tilex
    return res

def make_linear_palette(bpp):
    n = 2**bpp
    tmp = np.linspace(0, 0xff, n, dtype=np.uint8).transpose()
    return np.column_stack([tmp, tmp, tmp, tmp])

# method for image decode, encode methods, explicit declar makes numba faster
@njit([uint8(readonly(uint8, 2), readonly(uint8, 1))])
def find_palette(palette, pixel):
    """
    find the most close palette index of pixel
    :return: index in palette
    """
    
    idx, dmin = uint8(0),  0x7FFFFFFF
    tmp = np.zeros_like(pixel, dtype=np.int32)
    for i in range(palette.shape[0]):
        d = 0
        for j in range(tmp.shape[0]): 
            t = pixel[j] - palette[i][j]
            d += np.abs(t) # numba not support np.dot on int
            if d > dmin: break
        if d==0: return i
        if d < dmin: idx, dmin = i, d
    return idx

@njit([(uint8[:, :, :])(readonly(uint8, 3),readonly(uint8, 2))], parallel=True)
def encode_alpha_palette(img: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """
    encode rgba to index with alpha channel
    (h, w, 4) -> (h, w, 4)
    """

    img2 = np.zeros_like(img, dtype=img.dtype)
    for y in prange(img.shape[0]):
        for x in prange(img.shape[1]):
            img2[y][x][3] = find_palette(palette, img[y][x])
    return img2

def decode_alpha_palette(img: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """
    decode index with alpha channel to rbga
    (h, w, 4) -> (h, w, 4)
    """

    return palette[img[:, :, 3]]

def quantize_palette(img: np.ndarray, bpp) -> np.ndarray:
    """
    make palette from img
    """
    from sklearn.cluster import KMeans
    n = 2**bpp
    k = KMeans(n_clusters=n, n_init=10)
    k.fit(img.reshape([img.shape[0]*img.shape[1], img.shape[2]]))
    c = k.cluster_centers_.astype(np.uint8)
    palette = c[np.argsort(np.sum(c, axis=1))]
    return palette

@njit([void(uint8[:], int32, int32, int32, readonly(uint8, 1))])
def encode_pixel(data, bpp, offset, i, pixel):
    """
    encode pixel -> data
    :param ndarray data: pixel buffer
    :param int offset: start addr in data
    :param int i: the i-th pixel
    :param ndarray pixel: current pixel in rgba format
    """

    bytecur = offset + i//(8//bpp)
    if bpp <= 8:
        bitshift = i % (8//bpp) * bpp
        mask = ((1<<bpp)-1) << bitshift
        d = pixel[3]
        data[bytecur] |= (d<<bitshift) & mask
    elif bpp==16:
        data[bytecur: bytecur+2] = pixel[2:]
    elif bpp >= 24:
        n = 4 if bpp > 24 else 3
        data[bytecur: bytecur+n] = pixel[:n]

@njit([void(readonly(uint8, 1), int32, int32, int32, uint8[:])])
def decode_pixel(data, bpp, offset, i, pixel):
    """
    decode data -> pixel
    :param ndarray data: pixel buffer
    :param int offset: start addr in data
    :param int i: the i-th pixel
    :param ndarray pixel: current pixel in rgba format
    """

    bytecur = offset + i//(8//bpp)
    if bpp <= 8:
        bitshift = i % (8//bpp) * bpp
        mask = ((1<<bpp)-1) << bitshift
        d = (data[bytecur] & mask) >> bitshift
        pixel[3] = d
    elif bpp == 16:
        pixel[2:] = data[bytecur: bytecur+2]
    elif bpp >= 24:
        n = 4 if bpp > 24 else 3
        pixel[:n] = data[bytecur: bytecur+n]

@njit([(void)(uint8[:], int32, int32, int32, int32, 
        readonly(uint8, 2), readonly(uint8, 3))], parallel=True)
def encode_tiles(tiledata, tilesize, tilew, tileh, tilebpp, palette, img):
    """
    multi tiles -> implement
    """
    
    h, w, c = img.shape[0], img.shape[1], img.shape[2]
    n = tiledata.shape[0]//tilesize
    for tileidx in prange(n):
        for tiley in range(tileh):
            for tilex in range(tilew): # to avoid raceing in encode <8bpp
                stride_tile = w // tilew                  
                x = (tileidx % stride_tile) * tilew + tilex
                y = (tileidx // stride_tile) * tileh + tiley
                addr = tileidx * tilesize
                pixeli =  tiley * tilew + tilex
                if palette.shape[0] > 1:
                    pixel = np.zeros(4, dtype=np.uint8)
                    d = find_palette(palette, img[y][x])
                    if tilebpp<=8: pixel[3] = d
                    elif tilebpp==16: pixel[2], pixel[3] = d&0xff, d>>8
                else: pixel = img[y][x]
                encode_pixel(tiledata, tilebpp, addr, pixeli, pixel)
    
@njit([(void)(readonly(uint8, 1), int32, int32, int32, int32, 
        readonly(uint8, 2), uint8[:, :, :])], parallel=True)
def decode_tiles(tiledata, tilesize, tilew, tileh, tilebpp, palette, img):
    """
    img -> multi tiles implement
    """
        
    h, w, c = img.shape[0], img.shape[1], img.shape[2]
    n = tiledata.shape[0]//tilesize
    for tileidx in prange(n):
        for tiley in prange(tileh):
            for tilex in prange(tilew):
                stride_tile = w // tilew                  
                x = (tileidx % stride_tile) * tilew + tilex
                y = (tileidx // stride_tile) * tileh + tiley
                addr = tileidx * tilesize
                pixeli =  tiley * tilew + tilex
                pixel = img[y][x]
                decode_pixel(tiledata, tilebpp, addr, pixeli, pixel)
                if palette.shape[0] > 1: 
                    d = pixel[3]
                    if tilebpp==16: d = (d<<8) + pixel[2]
                    pixel[:] = palette[d]

#  wrappers for image convert
@filter_loadimages((0, "RGBA"))
def encode_tile_image(imgobj: Union[str, np.ndarray], tileinfo: tile_t, outpath=None, *, 
        palette: np.ndarray=None, ntiletotal=0) -> np.ndarray:
    """
    encode tile image wrapper
    :param tile: (w, h, bpp, size)
    :param palette: ndarray (n,4)
    :param ntiletotal: the count of whole tiles
    :return: img in rbga format
    """

    # init tile
    img = imgobj
    imgw, imgh = img.shape[1], img.shape[0]
    valid_tile(tileinfo, img.shape)
    n =  imgw // tileinfo.w * imgh // tileinfo.h
    if ntiletotal> 0: n = min(n, ntiletotal)
    if palette is None: palette = np.zeros((1, 4), dtype=np.uint8)
    tiledata = np.zeros(n*tileinfo.size, dtype=np.uint8)
    
    # init image and decode
    logging.info(f"image {img.shape} -> {n} {repr(tileinfo)}")
    encode_tiles(tiledata, tileinfo.size, tileinfo.w, tileinfo.h, tileinfo.bpp, palette, img)
    if outpath: writebytes(outpath, tiledata.tobytes())

    return tiledata

@filter_loadfiles(0)
def decode_tile_image(binobj: Union[str, bytes, np.ndarray], tileinfo: tile_t, outpath=None, *, 
        palette: np.ndarray=None, ntiletotal=0, ntilerow=64) -> np.ndarray:
    """
    decode tile image wrapper
    :param tile: (w, h, bpp, size)
    :param palette: ndarray (n,4)
    :param ntiletotal: the count of whole tiles
    :param ntilerow: the count of tiles in a row
    :return: img in rbga format
    """

    # init tile
    valid_tile(tileinfo)
    n = len(binobj) // tileinfo.size
    if ntiletotal> 0: n = min(n, ntiletotal)
    if palette is None: palette = np.zeros((1, 4), dtype=np.uint8)
    if type(binobj) == np.ndarray: tiledata = binobj[:n*tileinfo.size]
    else: tiledata = np.frombuffer(binobj, dtype=np.uint8, count=n*tileinfo.size)
    
    # init image and decode
    imgw, imgh = tileinfo.w * ntilerow, tileinfo.h * math.ceil(n/ntilerow)
    img = np.zeros([imgh, imgw, 4], dtype='uint8')
    logging.info(f"{n} {repr(tileinfo)} -> image {img.shape}")
    decode_tiles(tiledata, tileinfo.size, tileinfo.w, tileinfo.h, tileinfo.bpp, palette, img)
    if outpath: writeimage(outpath, img, "RGBA", "png")

    return img

def cli(cmdstr=None):
    def filter_paths(args):
        if args.batch:
            inpaths = load_batch(args.inpath)
            outpaths = load_batch(args.outpath)
        else: inpaths, outpaths = [args.inpath], [args.outpath]
        n = min(len(inpaths), len(outpaths))
        return inpaths, outpaths, n
    
    def filter_cfgs(args):
        tileinfo = tile_t(args.tilew, args.tileh,args.tilebpp, args.tilesize)
        palette = bytes.fromhex(args.palette) if args.palette else None
        if palette: palette = np.frombuffer(palette, dtype=np.uint8).reshape((-1, 4))
        return tileinfo, palette

    def cmd_decode(args):
        logging.debug(repr(args))
        inpaths, outpaths, n = filter_paths(args)
        tileinfo, palette = filter_cfgs(args)
        for i, (inpath, outpath) in enumerate(zip(inpaths, outpaths)):
            if args.batch: logging.info(f"batch {i+1}/{n} [inpath={inpath} outpath={outpath}]")
            if args.format == "tile":
                decode_tile_image(inpath, tileinfo, outpath, 
                    palette=palette, ntiletotal=args.ntiletotal, ntilerow=args.ntilerow)

    def cmd_encode(args):
        logging.debug(repr(args))
        inpaths, outpaths, n = filter_paths(args)
        tileinfo, palette = filter_cfgs(args)
        for i, (inpath, outpath) in enumerate(zip(inpaths, outpaths)):
            if args.batch: logging.info(f"batch {i+1}/{n} [inpath={inpath} outpath={outpath}]")
            if args.format == "tile":
                encode_tile_image(inpath, tileinfo, outpath, 
                    palette=palette, ntiletotal=args.ntiletotal)

    p = argparse.ArgumentParser(description=__description__)
    p2 = p.add_subparsers(title="operations")
    p_encode = p2.add_parser("encode", help="encode image to bin")
    p_decode = p2.add_parser("decode", help="decode bin to image")
    for t in [p_encode, p_decode]:
        t.add_argument("-o", "--outpath", default="out")
        t.add_argument("--log_level", default="info", help="set log level", 
            choices=("none", "critical", "error", "warning", "info", "debug"))
        t.add_argument("--batch", action="store_true", help="batch mode on inpath, outpath")
        t.add_argument("--format", default="tile", choices=["tile"], help="output format")
        t.add_argument("--palette", type=str, default=None)
        t.add_argument("--tilew", type=int, default=0)
        t.add_argument("--tileh", type=int, default=0)
        t.add_argument("--tilebpp", type=int, default=0)
        t.add_argument("--tilesize", type=int , default=0)
        t.add_argument("--ntiletotal", type=int , default=0)
    p_encode.set_defaults(handler=cmd_encode)
    p_encode.add_argument("inpath")
    p_decode.set_defaults(handler=cmd_decode)
    p_decode.add_argument("inpath")
    p_decode.add_argument("--ntilerow",type=int , default=64)

    args = p.parse_args(cmdstr.split(' ') if cmdstr else None)
    loglevel = args.log_level if hasattr(args, "log_level") else "info"
    logging.basicConfig(level=logging.getLevelName(loglevel.upper()), 
                    format="%(levelname)s:%(funcName)s: %(message)s")
    if hasattr(args, "handler"): args.handler(args)
    else: p.print_help()

if __name__ == '__main__':
    cli()

"""
history:
v0.1, initial version with RGBA8888， RGB332 convert
v0.1.1, added BGR mode
v0.2, add swizzle method
v0.2.1, change cv2 to PIL.image
v0.3, remake with libutil v0.6, accelerate by numba parallel
v0.3.1, add batch mode to optimize performance
"""
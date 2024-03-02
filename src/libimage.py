"""
A image tool (remake) for image encoding or decoding, 
all the intermediate format is rgba, index in alpha channel
    v0.3, develope by devseed
"""

import math
import logging
from queue import Queue
from typing import Tuple

import numba
import numpy as np
from numba import njit, prange, void, uint8, int32
readonly = lambda dtype, dim: numba.types.Array(dtype, dim, "C", True)

try:
    from libutil import filter_loadfiles, filter_loadimages
except ImportError:
    exec("from libutil_v600 import filter_loadfiles, filter_loadimages")

__version__ = 300

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
def make_tile_pattern(tilew, tileh, n_tile=4, n_row=2) -> np.ndarray:
    """
`   make tilehxtilew swizzle, for example 3 tile (2, 4),
        0	1	2	3  8  9  10 11 
        4	5	6	7  12 13 14 15
        16	17	18	19 -1 -1 -1 -1 
        20	21	22	23 -1 -1 -1 -1
        the square side is 2^n`
    """

    w, h = n_row*tilew, (n_tile + n_row - 1)// n_row * tileh
    res = -np.ones((h, w), dtype=np.int32)
    for tileidx in prange(n_tile):
        for tiley in prange(tileh):
            for tilex in prange(tilew):
                stride_tile = w // tilew                  
                x = (tileidx % stride_tile) * tilew + tilex
                y = (tileidx // stride_tile) * tileh + tiley
                res[y, x] = tileidx * tilew * tileh + tiley * tilew + tilex
    return res

def make_linear_palatte(bpp):
    n = 2**bpp
    tmp = np.linspace(0, 0xff, n, dtype=np.uint8).transpose()
    return np.column_stack([tmp, tmp, tmp, tmp])

# method for image decode, encode methods, explicit declar makes numba faster
@njit([uint8(readonly(uint8, 2), readonly(uint8, 1))])
def find_palatte(palatte, pixel):
    """
    find the most close palatte index of pixel
    :return: index in palatte
    """
    
    idx, dmin = uint8(0),  0x7FFFFFFF
    tmp = np.zeros_like(pixel, dtype=np.int32)
    for i in range(palatte.shape[0]):
        d = 0
        for j in range(tmp.shape[0]): 
            t = pixel[j] - palatte[i][j]
            d += np.abs(t) # numba not support np.dot on int
            if d > dmin: break
        if d==0: return i
        if d < dmin: idx, dmin = i, d
    return idx

@njit([(uint8[:, :, :])(readonly(uint8, 3),readonly(uint8, 2))], parallel=True)
def encode_palatte(img: np.ndarray, palatte: np.ndarray)->np.ndarray:
    """
    encode rgba to index with alpha channel
    """

    img2 = np.zeros_like(img, dtype=img.dtype)
    for y in prange(img.shape[0]):
        for x in prange(img.shape[1]):
            img2[y][x][3] = find_palatte(palatte, img[y][x])
    return img2

def decode_palatte(img: np.ndarray, palatte: np.ndarray)->np.ndarray:
    """
    decode index with alpha channel to rbga
    """

    return palatte[img[:, :, 3]]

def quantize_palatte(img: np.ndarray, bpp) -> np.ndarray:
    """
    make palatte from img
    """
    from sklearn.cluster import KMeans
    n = 2**bpp
    k = KMeans(n_clusters=n, n_init=10)
    k.fit(img.reshape([img.shape[0]*img.shape[1], img.shape[2]]))
    c = k.cluster_centers_.astype(np.uint8)
    palatte = c[np.argsort(np.sum(c, axis=1))]
    return palatte

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
        mask = ((bpp<<1)-1) << bitshift
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
        mask = ((bpp<<1)-1) << bitshift
        d = (data[bytecur] & mask) >> bitshift
        pixel[3] = d
    elif bpp == 16:
        pixel[2:] = data[bytecur: bytecur+2]
    elif bpp >= 24:
        n = 4 if bpp > 24 else 3
        pixel[:n] = data[bytecur: bytecur+n]

@njit([(void)(uint8[:], int32, int32, int32, int32, 
        readonly(uint8, 2), readonly(uint8, 3))], parallel=True)
def encode_tiles(tiledata, tilesize, tilew, tileh, tilebpp, palatte, img):
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
                if palatte.shape[0] > 1:
                    pixel = np.zeros(4, dtype=np.uint8)
                    d = find_palatte(palatte, img[y][x])
                    if tilebpp<=8: pixel[3] = d
                    elif tilebpp==16: pixel[2], pixel[3] = d&0xff, d>>8
                else: pixel = img[y][x]
                encode_pixel(tiledata, tilebpp, addr, pixeli, pixel)
    
@njit([(void)(readonly(uint8, 1), int32, int32, int32, int32, 
        readonly(uint8, 2), uint8[:, :, :])], parallel=True)
def decode_tiles(tiledata, tilesize, tilew, tileh, tilebpp, palatte, img):
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
                if palatte.shape[0] > 1: 
                    d = pixel[3]
                    if tilebpp==16: d = (d<<8) + pixel[2]
                    pixel[:] = palatte[d]

#  wrappers for image convert
def encode_tile_image(img: np.ndarray, tile_info: Tuple[int, int, int, int], *, 
        palatte: np.ndarray=None, n_tile=None) -> np.ndarray:
    """
    encode tile image wrapper
    :param tile_info: (h, w, bpp, size)
    :param tile_palatte: ndarray (n,4)
    :param n_tile: the count of whole tiles
    :return: img in rbga format
    """

    # init tile
    imgw, imgh = img.shape[1], img.shape[0]
    tileh, tilew, tilebpp, tilesize = tile_info
    n =  imgw // tilew * imgh // tileh
    if n_tile> 0: n = min(n, n_tile)
    if not tilesize: tilesize = (tileh * tilew * tilebpp + 7)// 8
    if palatte is None: palatte = np.zeros((1, 4), dtype=np.uint8)
    tiledata = np.zeros(n*tilesize, dtype=np.uint8)
    
    # init image and decode
    logging.info(f"image {img.shape} -> {n} tile {tilew}x{tileh} {tilebpp}bpp")
    encode_tiles(tiledata, tilesize, tilew, tileh, tilebpp, palatte, img)

    return tiledata

def decode_tile_image(binobj: bytes, tile_info: Tuple[int, int, int, int], *, 
        palatte: np.ndarray=None, n_tile=None, n_row=64) -> np.ndarray:
    """
    decode tile image wrapper
    :param tile_info: (h, w, bpp, size)
    :param tile_palatte: ndarray (n,4)
    :param n_row: the count of tiles in a row
    :param n_tile: the count of whole tiles
    :return: img in rbga format
    """

    # init tile
    tileh, tilew, tilebpp, tilesize = tile_info
    n =  math.floor(len(binobj)*8/tilebpp/tileh/tilew)
    if n_tile> 0: n = min(n, n_tile)
    if not tilesize: tilesize = (tileh * tilew * tilebpp + 7)// 8
    if palatte is None: palatte = np.zeros((1, 4), dtype=np.uint8)
    if type(binobj) == np.ndarray: tiledata = binobj[:n*tilesize]
    else: tiledata = np.frombuffer(binobj, dtype=np.uint8, count=n*tilesize)
    
    # init image and decode
    imgw, imgh = tilew * n_row, tileh * math.ceil(n/n_row)
    img = np.zeros([imgh, imgw, 4], dtype='uint8')
    logging.info(f"{n} tile {tilew}x{tileh} {tilebpp}bpp -> image {img.shape}")
    decode_tiles(tiledata, tilesize, tilew, tileh, tilebpp, palatte, img)

    return img

def cli(cmdstr=None):
    pass

if __name__ == '__main__':
    cli()

"""
history:
v0.1, initial version with RGBA8888， RGB332 convert
v0.1.1, added BGR mode
v0.2, add swizzle method
v0.2.1, change cv2 to PIL.image
v0.3, remake with libutil v0.6, accelerate by numba parallel
"""
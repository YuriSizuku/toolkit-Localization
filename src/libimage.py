"""
something about texture and picture convert
    v0.2.1, develope by devseed
"""

import math
import struct
import numpy as np
import argparse
from queue import Queue
from PIL import Image, ImageOps

LIBTEXTURE = 210

texture_size = {"RGBA8888":4, "RGB5A1": 2, "RGB332":1, "RGBA2222":1}

def swizzle_regular(n, start=0, resmat=None):
    """
    for generating Swizzling square
        0	1	4	5
        2	3	6	7
        8	9	12	13
        10	11	14	15
        the square side is 2^n
    """
    w = h = 2**n
    if resmat is None:
        resmat = np.zeros([h, w], dtype=np.int)
    else:
        resmat = resmat.reshape([h, w])
    resmat[h - 1, w - 1] = h*w - 1 + start
    _que = Queue()
    _que.put((0, 0, w - 1, h - 1))
    while not _que.empty():
        x0, y0, x1, y1 = _que.get()
        dx = np.int((x1+1-x0) // 2)
        dy = np.int((y1+1-y0) // 2)
        d = np.int((y1+1-y0)*(x1+1-x0)//4)
        idx = resmat[y1][x1]
        resmat[y1][x0+dx-1] = idx - d
        resmat[y0+dy-1][x1] = idx - 2*d
        resmat[y0+dy-1][x0+dx-1] = idx - 3*d
        if d > 1:
            _que.put((x0+dx, y0+dy, x1, y1))
            _que.put((x0, y0+dy, x0+dx-1, y1))
            _que.put((x0+dx, y0, x1, y0+dy-1))
            _que.put((x0, y0, x0+dx-1, y0+dy-1))
    return resmat


def swizzle_tile(imgw, imgh, tilew=1, tileh=1, start=0, resmat=None):
    """
        for generating Swizzling mat with tile
    """
    tileyn = np.int(np.ceil(imgh/tileh))
    tilexn = np.int(np.ceil(imgw/tilew))
    if resmat is None:
        resmat = np.zeros(tileyn*tilexn, dtype=np.int)
    else:
        resmat = resmat.reshape(tileyn*tilexn)
    d1 = min(tileyn, tilexn)
    d2 = max(tileyn, tilexn)
    n = np.int(np.ceil(np.log2(d1)))
    for pos in range(0, d1*d2, d1*d1):
        swizzle_regular(n, start + pos, 
            resmat[pos: pos + d1*d1])
    resmat = resmat.reshape([tileyn, tilexn])
    return resmat

def swillze_fill(swimat, tileunitmat, stride=1, resmat=None):
    """
        fill the tileunitmat into the swimat
    """
    swiw = swimat.shape[1]
    swih = swimat.shape[0]
    tilew = tileunitmat.shape[1]
    tileh = tileunitmat.shape[0]
    tilesize = tilew * tileh * stride
    h = swih * tileh
    w = swiw * tilew
    if resmat is None:
        resmat = np.zeros([h, w], dtype=np.int)

    for i in range(swiw):
        for j in range(swih):
            idx = swimat[j, i]
            resmat[j*tileh:(j+1)*tileh,
                i*tilew:(i+1)*tilew] = tileunitmat + idx*tilesize
    return resmat

def raw2gray(data, width):
    height = math.ceil(len(data) /  width)
    gray = np.zeros((height, width), dtype=np.uint8)
    print(width, height)
    for row in range(height):
        for col in range(width):         
            start = row*width + col       
            if start > len(data) -1:
                print(row, col, start, " out of range")
                break
            gray[row][col] = struct.unpack("<B", data[start:start+1])[0] 
    return gray

def gray2raw(gray):
    height, width = gray.shape
    data = bytearray(height*width)
    print(width, height, len(data))
    for row in range(height):
        for col in range(width):  
            start = row*width + col
            data[start:start+1] = struct.pack("<B", gray[row][col])
    return data

def raw2bgra(data, width, format="RGBA8888", *,compress_format="",is_bgr=False):
    pixel_size = texture_size[format]
    height = math.ceil(len(data) / (pixel_size * width))
    bgra = np.zeros((height, width, 4), dtype=np.uint8)
    print(width, height)
    for row in range(height):
        for col in range(width):                
            flag = 0
            start = (row*width + col) * pixel_size

            if format == "RGBA8888":
                if start > len(data) -4: 
                    flag = 1
                    print(row, col, start, " out of range")
                    break
                r, g, b, a = struct.unpack("<BBBB", data[start:start+4])
            
            elif format == "RGB332":
                if start > len(data) -1:
                    flag = 1
                    print(row, col, start, " out of range")
                    break
                a = 255
                d = struct.unpack("<B", data[start:start+1])[0] 
                r = round((d >> 5) * 255 / 7)
                g = round(((d >> 2) & 0b00000111) * 255 / 7)
                b = round((d & 0b00000011) * 255 / 3)

            elif format == "RGBA2222":
                if start > len(data) -1:
                    flag = 1
                    print(row, col, start, " out of range")
                    break
                d = struct.unpack("<B", data[start:start+1])[0] 
                r = round((d >> 6) * 255 / 3)
                g = round(((d >> 4) & 0b00000011) * 255 / 3)
                b = round(((d >> 2) & 0b00000011) * 255 / 3)
                a = round((d & 0b00000011) * 255 / 3)

            else: 
                print(format + " is invalid !")
                return None

            if is_bgr:
                t = r
                r = b
                b = t
            bgra[row][col] = np.array([b, g, r, a], dtype=np.uint8)
        
        if flag: break
    return bgra

def bgra2raw(bgra, format="RGBA8888", *, compress_format="", is_bgr=False):
    pixel_size = texture_size[format]
    height, width, channal = bgra.shape
    data = bytearray(height*width*pixel_size)
    print(width, height, len(data))
    for row in range(height):
        for col in range(width):       
            if channal == 4:
                b, g, r, a = bgra[row][col].tolist()
            else :
                b, g, r = bgra[row][col].tolist()
                a = 255
            if is_bgr:
                t = r
                r = b
                b = t
            start = (row*width + col) * pixel_size

            if format == "RGBA8888":
                data[start:start+4] = struct.pack("<BBBB", r, g, b, a)

            elif format == "RGB332":
                d = round(b * 3 /255) + (round(g * 7 /255)<<2) + (round(r * 7 /255)<<5)
                data[start:start+1] = struct.pack("<B", d)
            
            elif format == "RGBA2222":
                d = round(a * 3 /255) + (round(b * 3 /255)<<2) +  (round(g * 3 /255)<<4) + (round(r * 3 /255)<<6)
                data[start:start+1] = struct.pack("<B", d)
            
            else: 
                print(format + " is invalid !")
                return None
    return data

def texture2picture(inpath, width, outpath="out.png", format="RGBA8888", *,compress_format="", is_bgr=False, f_before=None):
    with open(inpath, "rb") as fp:
        print(inpath + " opened!")
        data = fp.read()
        if f_before: data = f_before(data)
        if format == "GRAY":
            gray = raw2gray(data, width)
            Image.fromarray(gray).save(outpath)
        else:
            bgra = raw2bgra(data, width, format=format,             
                compress_format=compress_format, is_bgr = is_bgr)
            Image.fromarray(bgra[:,:,[2,1,0,3]]).save(outpath)
        print(outpath + "picture extracted!")

def picture2texture(inpath, outpath=r".\out.bin", format="RGBA8888", *, compress_format="", is_bgr=False, f_after=None):
    if format == "GRAY":
        gray = np.array(ImageOps.grayscale(Image.open(inpath)))
        print(inpath + " loaded!")
        data = gray2raw(gray)
    else:
        bgra = np.array(Image.open(inpath))[:,:, [2,1,0,3]]
        print(inpath + " loaded!")
        data = bgra2raw(bgra, format, compress_format=compress_format, is_bgr=is_bgr)
    if f_after: data = f_after(data)
    with open(outpath, "wb") as fp:
        fp.write(data)
        print(outpath + "texture generated!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="texture tool v0.2.1, developed by devseed")
    parser.add_argument('-b', '--build', action="store_true")
    parser.add_argument("-f", "--format", type=str, default="RGBA8888")
    parser.add_argument("-c", "--compress", type=str, default="")
    parser.add_argument("-o", "--outpath", type=str, default=r".\out.png")
    parser.add_argument("-w", "--width", type=int, default=2048)
    parser.add_argument('--bgr', action="store_true")
    parser.add_argument("inpath")
    args = parser.parse_args()
    if args.build:
        picture2texture(args.inpath, outpath=args.outpath, format=args.format, compress_format=args.compress, is_bgr=args.bgr)
    else:
        texture2picture(args.inpath, args.width, outpath=args.outpath, format=args.format, compress_format=args.compress, is_bgr=args.bgr)

"""
history:
v0.1 initial version with RGBA8888， RGB332 convert
v0.1.1 added BGR mode
v0.2 add swizzle method
v0.2.1 change cv2 to PIL.image
"""
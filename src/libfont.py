 # -*- coding: utf-8 -*-
"""
A font tool (remake) for tbl and processing fonts
    v0.3, developed by devseed
"""

import math
import copy
import struct
import logging
from io import BytesIO
from typing import Union, Tuple, List, Dict, Set

import numpy as np
from PIL import ImageFont, ImageDraw, Image

__version__ = 300

try:
    from libutil import tbl_t, load_tbl, loadfiles
except ImportError:
    exec("from libutil_v600 import tbl_t, load_tbl loadfiles")

# tbl generations
def make_cp932_tbl(full=True, out_failed: List[int]=None, text_fallback="♯") -> List[tbl_t]:
    
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
    end = 0xf0 if full is True else 0xeb
    for high in range(0xe0, end): 
        for low in range(0x40, 0xfd):
            if low==0x7f: continue
            _process(high, low)

    logging.info(f"make tbl cp932 with {len(tbl)} chars")
    return tbl  

def make_cp936_tbl(only_kanji=False) -> List[tbl_t]:
    tbl: List[tbl_t] = []
    if only_kanji is False:
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

# tbl manipulate
def replace_tchar_tbl(tbl: List[tbl_t], replace: Dict[str, str]) -> List[tbl_t]:
    f = lambda x: tbl_t(x.tcode, replace[x.tchar] if x.tchar in replace else x.tchar) 
    return list(f, tbl) 

def replace_encoding_tbl(tbl:List[tbl_t], encoding:str) -> List[tbl_t]:
    f = lambda x: tbl_t(x.tchar.encode(encoding), x.tchar) 
    return list(f, tbl) 

def diff_tchar_tbl(tbl1: List[tbl_t], tbl2: List[tbl_t]) -> Tuple[Set, Set, Set]:
    """
    compare the tchar in tbl1 and tbl2
    :return: t1only, t2only, t1t2common
    """

    t1set = set(t.tchar for t in tbl1)
    t2set = set(t.tchar for t in tbl2)
    return t1set - t2set, t2set - t1set,  t1set & t2set

def align_tbl(tbl: List[tbl_t], gap_map: Dict[int, int] = None, gap_static=True, 
        ftext_padding: tbl_t=tbl_t(b'\xff', '')) -> List[tbl_t]:
    """
    manualy align tbl for glphys 
    by adding offset(+-) in gap_map at some position 
    :param gap_map: for adding offset in tbl, + for padding, - for skip
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
                for j in range(n): tbl_aligned.append(ftext_padding) # dup by padding
                tbl_aligned.append(t); gap_pos = 0 # reset to enable gap
        else: tbl_aligned.append(t); gap_pos = 0
    return tbl_aligned

def merge_tbl(tbl1: List[tbl_t], tbl2: List[tbl_t], text_fallback="♯") -> List[tbl_t]:
    """
    merge the tcode in tbl1 and the tchar in tbl2
    :return: based on tbl1
    """

    tbl3 = []
    for i, t in enumerate(tbl1):
        tchar = tbl2[i].tchar if i < len(tbl2) else text_fallback 
        tbl3.append(tbl_t(t.tcode, tchar))
    logging.info(f"merged tbl1(length={len(tbl1)}) and tbl2(length=f{len(tbl2)})")
    return tbl3

def rebuild_tbl(tbl1: List[tbl_t], tbl2: List[tbl_t], 
        reserved: Set=None, find_range=range(-1, -1, -1)) -> List[tbl_t]:
    """
    rebuild with (tbl1.tcode, tbl2.tchar) as common tchar in same position
    :params reserved: reserved position for not override
    """

    def iter_avail(notuse: Set, r: range):
        for i in r:
            if i in notuse: continue
            yield i 

    r = find_range
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

# font manipulate
@loadfiles(1)
def render_font(tblobj: Union[str, bytes], ttfobj: Union[str, bytes],
        glphy_shape: Tuple, n_row=64, outpath=None, *, 
        padding=(0,0,0,0), shift=(0, 0), pt=0) -> Image:
    """
    :param tblpath: tblpath or tbl list
    :param padding: (up, down, left, right)
    :param shift: (x, y)
    :return: pil.Image
    """
    
    tbl = load_tbl(tblobj)
    n = len(tbl)
    glphyw, glphyh = glphy_shape
    w = padding[2] + n_row*glphyw + padding[3]
    h = padding[0] + math.ceil(n/n_row)*glphyh + padding[1]
    img = np.zeros((h, w, 4), dtype=np.uint8)
    logging.info(f"render font to image {w}X{h}, with {n} glphys")
    
    ptpxmap = {8:6, 9:7, 16:12, 18:14, 24:18, 32:24, 48:36}
    if pt==0: pt=ptpxmap[glphyh]
    font = ImageFont.truetype(BytesIO(ttfobj), pt)
    imgpil = Image.fromarray(img)
    draw = ImageDraw.Draw(imgpil)

    for i, t in enumerate(tbl):
        x = padding[2] + shift[0] + (i%n_row)*glphyw
        y = padding[0] + shift[1] + (i//n_row)*glphyh 
        draw.text((x,y), t.tchar, fill=(255,255,255,255), font=font, align="center")
    if outpath: imgpil.save(outpath)
    return imgpil

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
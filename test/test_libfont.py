import sys
import logging
import unittest
import numpy as np

from common import *
from libutil import tbl_t, tile_t, save_tbl
import libfont

class TestGenerateTbl(unittest.TestCase):
    def test_example_tbl932(self):
        out_failed = []
        text_fallback = "♯"
        tbl = libfont.make_cp932_tbl(out_failed=out_failed, text_fallback=text_fallback)
        self.assertGreater(len(tbl), 7000)
        for idx in out_failed:
            self.assertEqual(tbl[idx].tchar, text_fallback)

    def test_example_tbl936(self):
        tbl = libfont.make_cp936_tbl()
        self.assertGreater(len(tbl), 7000)

class TestManipulateTbl(unittest.TestCase):
    def test_example_difftbl(self):
        tbl1 = [tbl_t(str(i).encode(), str(i)) for i in range(10)]
        tbl2 = [tbl_t(str(i).encode(), str(i)) for i in range(5, 15)]
        t1, t2, t12 = libfont.diff_tchar_tbl(tbl1, tbl2)
        self.assertEqual(len(t1|t12), len(tbl1))
        self.assertEqual(len(t2|t12), len(tbl2))

    def test_example_aligntbl(self):
        p = tbl_t(b"*", "*")
        tbl = [tbl_t(str(i).encode(), str(i)) for i in range(10)]
        tbl2 = libfont.align_tbl(tbl)
        self.assertEqual(len(tbl2), len(tbl))
        
        tbl2 = libfont.align_tbl(tbl, gap_map={1:1}, tbl_padding=p)
        self.assertEqual(tbl2[1].tchar, p.tchar)
        self.assertEqual(len(tbl2), len(tbl) + 1)
        
        tbl2 = libfont.align_tbl(tbl, gap_map={0:-2}, tbl_padding=p)
        self.assertEqual(tbl2[2].tchar, tbl[4].tchar)
        self.assertEqual(len(tbl2), len(tbl) - 2)
        
        # tbl1 0 1 2 3 4 5 6 7 8 9
        # tbl2 * * 0 1 * * 2 3 8 9  
        gap_map = {0:2, 2:2, 4:-4} 
        tbl2 = libfont.align_tbl(tbl, gap_map=gap_map, gap_static=True, tbl_padding=p)
        self.assertEqual(tbl2[2].tchar, tbl[0].tchar)
        self.assertEqual(tbl2[4].tchar, p.tchar)
        self.assertEqual(len(tbl2), len(tbl))

        # tbl1 0 1 2 3 4 5 6 7 8 9
        # tbl2 * * 0 * * 1 6 7 8 9
        gap_map = {0:2, 3:2, 6:-4} 
        tbl2 = libfont.align_tbl(tbl, gap_map=gap_map, gap_static=False, tbl_padding=p)
        self.assertEqual(tbl2[2].tchar, tbl[0].tchar)
        self.assertEqual(tbl2[5].tchar, tbl[1].tchar)
        self.assertEqual(len(tbl2), len(tbl))

    def test_example_mergetbl(self):
        charset = ["わ", "た", "し"]
        tbl1 = [tbl_t(s.encode('sjis'), s) for s in charset]
        tbl2 = [tbl_t(s.encode('sjis'), s) for s in charset[::-1]]
        tbl3 = libfont.merge_simple_tbl(tbl1, tbl2)
        for i, t in enumerate(tbl3):
            self.assertEqual(t.tcode, tbl1[i].tcode)
            self.assertEqual(t.tchar, tbl2[i].tchar)

    def test_example_intersecttbl(self):
        tbl1 = libfont.make_cp932_tbl()
        tbl2 = libfont.make_cp936_tbl(range_kanji=False)
        tbl3 = libfont.merge_intersect_tbl(tbl1, tbl2)
        tbl1_tcharmap = dict((t.tchar, i) for i, t in enumerate(tbl1))
        tbl2_tcharmap = dict((t.tchar, i) for i, t in enumerate(tbl2))
        tbl3_tcharmap = dict((t.tchar, i) for i, t in enumerate(tbl3))
        self.assertIn("你", tbl3_tcharmap)
        self.assertEqual(tbl1_tcharmap["私"], tbl3_tcharmap["私"])
        lines = save_tbl(tbl3)
        self.assertEqual(len(lines), len(tbl1))

class TesttMakeFont(unittest.TestCase):
    def test_example_glphy4(self):
        tileinfo = tile_t(10, 10, 4, 10*10//2)
        tmp = np.linspace(0, 0xff, 2**tileinfo.bpp, dtype=np.uint8).transpose()
        palatte = np.column_stack([tmp, tmp, tmp, tmp])
        
        # test palatte decode encode
        idx1 = np.zeros([tileinfo.h, tileinfo.w], dtype=np.uint8)
        for y in range(idx1.shape[0]):
            for x in range(idx1.shape[1]):
                idx1[y][x] = (y + x) % 16
        img1 = libfont.decode_index_palette(idx1, palatte)
        idx2 = libfont.encode_index_palette(img1, palatte)
        self.assertTrue(np.array_equal(idx1, idx2))
        
        # test glphy decode encode
        img2 = np.zeros_like(img1)
        tiledata = np.zeros(idx1.shape[0] * idx1.shape[1] * tileinfo.bpp // 8, dtype=np.uint8)
        libfont.encode_glphy(tiledata, tileinfo.size, tileinfo.w, tileinfo.h, tileinfo.bpp, palatte, img1)
        self.assertGreater(tiledata.max(), 0)
        for i in range(tiledata.shape[0]):
            v = idx1.ravel()
            d = v[2*i] + (v[2*i+1]<<tileinfo.bpp)
            self.assertEqual(tiledata[i], d)
        libfont.decode_glphy(tiledata, tileinfo.size, tileinfo.w, tileinfo.h, tileinfo.bpp, palatte, img2, cache=False)
        self.assertTrue(np.array_equal(img1, img2))

    def test_example_makeimagefont(self):
        if sys.platform != "win32": return
        outpath = None
        img = libfont.make_image_font(paths_tbl["COM001"], r"C:\Windows\Fonts\simhei.ttf", 
                tileinfo=tile_t(24, 24), outpath=outpath, render_size=24)
        self.assertGreater(img.max(), 0)
        self.assertEqual(img.min(), 0)

    def test_example_maketilefont(self):
        if sys.platform != "win32": return
        outpath = None
        tiledata = libfont.make_tile_font(paths_tbl["COM001"], r"C:\Windows\Fonts\simhei.ttf", 
                tileinfo=tile_t(24, 24, 4), outpath=outpath, render_size=24)
        self.assertGreater(tiledata.max(), 0)
        self.assertEqual(tiledata.min(), 0)

class TestExtractFont(unittest.TestCase):
    def test_it_extracttilefont(sellf):
        libfont.extract_tile_font(paths_tbl["COM001"], paths_bin["it"], 
            tile_t(20, 18, 2, 20*18//4+2), outpath=None)
        
    def test_com001_extractimagefont(self):
        if sys.platform != "win32": return
        img = libfont.make_image_font(paths_tbl["COM001"], r"C:\Windows\Fonts\simhei.ttf", 
                tileinfo=tile_t(24, 24), render_size=24, render_overlap=1)
        outdir = None if True else "project/pysrc_all/build/com001"
        libfont.extract_image_font(paths_tbl["COM001"], img, tile_t(24, 24), outpath=outdir)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(funcName)s: %(message)s")
    unittest.main()
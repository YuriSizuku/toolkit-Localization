import time
import logging
import unittest
import numpy as np
from PIL import Image

from common import *
from libutil import tbl_t, save_tbl
import libfont
import libimage

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
        
        tbl2 = libfont.align_tbl(tbl, gap_map={1:1}, ftext_padding=p)
        self.assertEqual(tbl2[1].tchar, p.tchar)
        self.assertEqual(len(tbl2), len(tbl) + 1)
        
        tbl2 = libfont.align_tbl(tbl, gap_map={0:-2}, ftext_padding=p)
        self.assertEqual(tbl2[2].tchar, tbl[4].tchar)
        self.assertEqual(len(tbl2), len(tbl) - 2)
        
        # tbl1 0 1 2 3 4 5 6 7 8 9
        # tbl2 * * 0 1 * * 2 3 8 9  
        gap_map = {0:2, 2:2, 4:-4} 
        tbl2 = libfont.align_tbl(tbl, gap_map=gap_map, gap_static=True, ftext_padding=p)
        self.assertEqual(tbl2[2].tchar, tbl[0].tchar)
        self.assertEqual(tbl2[4].tchar, p.tchar)
        self.assertEqual(len(tbl2), len(tbl))

        # tbl1 0 1 2 3 4 5 6 7 8 9
        # tbl2 * * 0 * * 1 6 7 8 9
        gap_map = {0:2, 3:2, 6:-4} 
        tbl2 = libfont.align_tbl(tbl, gap_map=gap_map, gap_static=False, ftext_padding=p)
        self.assertEqual(tbl2[2].tchar, tbl[0].tchar)
        self.assertEqual(tbl2[5].tchar, tbl[1].tchar)
        self.assertEqual(len(tbl2), len(tbl))

    def test_example_mergetbl(self):
        charset = ["わ", "た", "し"]
        tbl1 = [tbl_t(s.encode('sjis'), s) for s in charset]
        tbl2 = [tbl_t(s.encode('sjis'), s) for s in charset[::-1]]
        tbl3 = libfont.merge_tbl(tbl1, tbl2)
        for i, t in enumerate(tbl3):
            self.assertEqual(t.tcode, tbl1[i].tcode)
            self.assertEqual(t.tchar, tbl2[i].tchar)

    def test_example_rebuildtbl(self):
        tbl1 = libfont.make_cp932_tbl()
        tbl2 = libfont.make_cp936_tbl(only_kanji=False)
        tbl3 = libfont.rebuild_tbl(tbl1, tbl2)
        tbl1_tcharmap = dict((t.tchar, i) for i, t in enumerate(tbl1))
        tbl2_tcharmap = dict((t.tchar, i) for i, t in enumerate(tbl2))
        tbl3_tcharmap = dict((t.tchar, i) for i, t in enumerate(tbl3))
        self.assertIn("你", tbl3_tcharmap)
        self.assertEqual(tbl1_tcharmap["私"], tbl3_tcharmap["私"])
        lines = save_tbl(tbl3)
        self.assertEqual(len(lines), len(tbl1))

class TesttManipulateFont(unittest.TestCase):
    def test_example_renderfont(self):
        imgpil = libfont.render_font(paths_tbl["COM001"], 
                    r"C:\Windows\Fonts\simhei.ttf", glphy_shape=(24, 24), pt=24)
        self.assertIsNotNone(imgpil)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(funcName)s: %(message)s")
    unittest.main()
import codecs
import logging
import unittest

from common import *
import libutil

class TestTbl(unittest.TestCase):
    def test_file_com001(self):
        with codecs.open(paths_tbl["COM001"], 'r', 'utf-8') as fp: 
            lines1 = fp.readlines()
        tbl = libutil.load_tbl(lines1)
        lines2 = libutil.save_tbl(tbl)
        assert_lines(self, lines1, lines2)

class TestFtext(unittest.TestCase):
    def test_file_com001(self):
        with codecs.open(paths_ftext["COM001"], 'r', 'utf-8') as fp: 
            lines1 = fp.readlines()
        ftexs1, ftexs2 = libutil.load_ftext(lines1)
        self.assertEqual(len(ftexs1), len(ftexs2))
        lines2 = libutil.save_ftext(ftexs1, ftexs2)
        assert_lines(self, lines1, lines2)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(funcName)s: %(message)s")
    unittest.main()
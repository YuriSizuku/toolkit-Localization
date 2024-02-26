import os
import sys
import codecs
import logging
import unittest
from copy import deepcopy

sys.path.append(os.path.join(os.path.dirname(__file__), r"src"))
sys.path.append(os.path.join(os.path.dirname(__file__), r"../src"))
import libtext as bintext
import libutil as util

paths_bin = {'COM001': "test/sample/COM001"}
paths_tbl = {'COM001': "test/sample/COM001.tbl"}
paths_ftext = {'COM001': "test/sample/COM001.txt"} 

def assert_lines(self, lines1, lines2, ignore_len=2):
    lines1 = list(filter(lambda x: len(x) > ignore_len, lines1))
    lines2 = list(filter(lambda x: len(x) > ignore_len, lines2))
    self.assertEqual(len(lines1), len(lines2))
    for l1, l2 in zip(lines1, lines2):
        self.assertEqual(l1.rstrip('\r').rstrip('\n'), l2.rstrip('\r').rstrip('\n'))

class TestTbl(unittest.TestCase):
    def test_com001(self):
        # test different ways to load tbl
        with codecs.open(paths_tbl["COM001"], 'r', 'utf-8') as fp: 
            lines1 = fp.readlines()
        tbl = util.load_tbl(lines1)
        lines2 = util.dump_tbl(tbl)
        assert_lines(self, lines1, lines2)

        # test encode_tbl, decode_tbl
        text1 = "湧き出る温泉と豊かな自然に包まれた風光明媚な地で, 你"
        data = bintext.encode_tbl(text1, tbl, "#".encode())
        data2 = bintext.encode_tbl(text1, tbl, "#".encode())
        addrs, sizes = bintext.detect_text_tbl(data2, tbl)
        self.assertEqual(len(addrs), len(sizes))
        self.assertEqual(addrs[0] + sizes[0], len(data2))
        self.assertEqual(data, data2) # test encode cache
        text2 = bintext.decode_tbl(data, tbl)
        self.assertEqual(text1.replace("你", "#"), text2)

class TestFtext(unittest.TestCase):
    def test_com001(self):
        # test load and dump ftext
        with codecs.open(paths_ftext["COM001"], 'r', 'utf-8') as fp: 
            lines1 = fp.readlines()
        ftexs1, ftexs2 = util.load_ftext(lines1)
        self.assertEqual(len(ftexs1), len(ftexs2))
        lines2 = util.dump_ftext(ftexs1, ftexs2)
        assert_lines(self, lines1, lines2)

class TestExtract(unittest.TestCase):
    def test_com001(self):
        # test extract_ftexts by sjis and tbl
        lines_sjis = bintext.extract_ftexts(paths_bin["COM001"], encoding='sjis')
        lines_tbl = bintext.extract_ftexts(paths_bin["COM001"], tblobj=paths_tbl["COM001"])
        assert_lines(self, lines_sjis, lines_tbl)

    def test_sentense(self):
        dummys = [b'\x01\xff\x03', b'\x15', b'\xff\xff']
        text = "湧き出る温泉と豊かな自然に包まれた風光明媚な地で"

        # test extract by difference encoding
        data_utf8 = b''.join([dummys[i] + text.encode('utf8') for i in range(len(dummys))])
        data_sjis = b''.join([dummys[i] + text.encode('sjis') for i in range(len(dummys))])
        data_gbk = b''.join([dummys[i] + text.encode('gbk') for i in range(len(dummys))])
        lines_utf8 = bintext.extract_ftexts(data_utf8, encoding='utf-8')
        lines_sjis = bintext.extract_ftexts(data_sjis, encoding='sjis')
        lines_gbk =  bintext.extract_ftexts(data_gbk, encoding='gbk')
        ftexts_utf8, _ = bintext.load_ftext(lines_utf8)
        ftexts_sjis, _ = bintext.load_ftext(lines_sjis)
        ftexts_gbk, _ = bintext.load_ftext(lines_gbk)

        self.assertEqual(len(ftexts_utf8), len(dummys))
        for t in ftexts_utf8: self.assertEqual(t.text, text)
        self.assertEqual(len(ftexts_sjis), len(dummys))
        for t in ftexts_sjis: self.assertEqual(t.text, text)
        self.assertEqual(len(ftexts_gbk), len(dummys))
        for t in ftexts_gbk: self.assertEqual(t.text, text)

class TestInsert(unittest.TestCase):
    def test_com001(self):
        with open(paths_bin["COM001"], 'rb') as fp: srcdata = fp.read()
        ftexts = bintext.load_ftext(paths_ftext["COM001"])[1]

        # test basic insert
        data_sjis = bintext.insert_ftexts(srcdata, (None, ftexts), 
                        encoding='sjis', referobj=paths_bin["COM001"])
        data_tbl = bintext.insert_ftexts(paths_bin["COM001"], 
                        paths_ftext["COM001"], tblobj=paths_tbl["COM001"])
        self.assertEqual(data_sjis, data_tbl)

        # test enc_longer, enc_align
        text_added = "text_added試験"
        ftexts_longer = deepcopy(ftexts)
        ftexts_longer[1].text += text_added
        data_longer = bintext.insert_ftexts(paths_bin["COM001"], 
            (None, ftexts_longer), encoding='sjis', insert_longer=True)
        n = len(text_added.encode('sjis'))
        self.assertEqual(len(data_longer) , len(srcdata) + n)
        start, end = ftexts[-2].addr, ftexts[-2].addr + ftexts[-2].size 
        self.assertEqual(srcdata[start: end] , data_longer[start + n: end + n])
        align = 16
        n2 = max(n, align)
        data_longer = bintext.insert_ftexts(paths_bin["COM001"], 
            (None, ftexts_longer), encoding='sjis', insert_longer=True, insert_align=align)
        self.assertEqual(len(data_longer) , len(srcdata) + n2)
        self.assertEqual(srcdata[start: end] , data_longer[start + n2: end + n2])

        # test enc_shorter, bytes_padding
        ftexts_shorter = deepcopy(ftexts)
        ftexts_shorter[1].text = ftexts_shorter[1].text[:-4]
        n =  len(ftexts_shorter[1].text.encode('sjis')) - ftexts_shorter[1].size
        data_shorter = bintext.insert_ftexts(srcdata, 
            (None, ftexts_shorter), encoding='sjis', bytes_padding=b'\x80\x80')
        self.assertEqual(len(data_shorter) , len(srcdata))
        end = ftexts[1].addr + ftexts[1].size        
        self.assertEqual(bytes(data_shorter[end +n: end]) , (-n//2)*b'\x80\x80')
        data_shorter = bintext.insert_ftexts(srcdata, (None, ftexts_shorter), 
            encoding='sjis', insert_longer=True, insert_shorter=True)
        self.assertEqual(len(data_shorter) , len(srcdata) + n)
        start, end = ftexts[-2].addr, ftexts[-2].addr + ftexts[-2].size 
        self.assertEqual(srcdata[start: end] , data_shorter[start + n: end + n])

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(funcName)s: %(message)s")
    unittest.main()
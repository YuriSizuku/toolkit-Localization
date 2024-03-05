import logging
import unittest
from copy import deepcopy

from common import *
import libtext

class TestConvert(unittest.TestCase):
    def test_example_str(self):
        tbl = libtext.load_tbl(paths_tbl["COM001"])
        text = "湧き出る温泉と豊かな自然に包まれた風光明媚な地で, 你"
        data = libtext.encode_tbl(text, tbl, "#".encode())
        data2 = libtext.encode_tbl(text, tbl, "#".encode())
        self.assertEqual(data, data2) # test encode cache
        addrs, sizes = libtext.detect_text_sjis(data2)
        self.assertEqual(len(addrs), len(sizes))
        self.assertEqual(addrs[0] + sizes[0], len(data2))

        text2 = libtext.decode_tbl(data, tbl)
        self.assertEqual(text.replace("你", "#"), text2)

class TestExtract(unittest.TestCase):
    def test_file_com001(self):
        # test extract_ftexts by sjis and tbl
        ftexts_sjis = libtext.extract_ftexts(paths_bin["COM001"], encoding='sjis')
        ftexts_tbl = libtext.extract_ftexts(paths_bin["COM001"], tblobj=paths_tbl["COM001"])
        self.assertEqual(len(ftexts_sjis), len(ftexts_tbl))
        for i, (t1, t2) in enumerate(zip(ftexts_sjis, ftexts_tbl)):
            self.assertEqual(t1.addr, t2.addr)
            self.assertEqual(t1.size, t2.size)
            self.assertEqual(t1.text, t2.text)

    def test_example_str(self):
        dummys = [b'\x01\xff\x03', b'\x15', b'\xff\xff']
        text = "湧き出る温泉と豊かな自然に包まれた風光明媚な地で"

        # test extract by difference encoding
        data_utf8 = b''.join([dummys[i] + text.encode('utf8') for i in range(len(dummys))])
        data_sjis = b''.join([dummys[i] + text.encode('sjis') for i in range(len(dummys))])
        data_gbk = b''.join([dummys[i] + text.encode('gbk') for i in range(len(dummys))])
        ftexts_utf8 = libtext.extract_ftexts(data_utf8, encoding='utf-8')
        ftexts_sjis = libtext.extract_ftexts(data_sjis, encoding='sjis')
        ftexts_gbk =  libtext.extract_ftexts(data_gbk, encoding='gbk')

        self.assertEqual(len(ftexts_utf8), len(dummys))
        for t in ftexts_utf8: self.assertEqual(t.text, text)
        self.assertEqual(len(ftexts_sjis), len(dummys))
        for t in ftexts_sjis: self.assertEqual(t.text, text)
        self.assertEqual(len(ftexts_gbk), len(dummys))
        for t in ftexts_gbk: self.assertEqual(t.text, text)

class TestInsert(unittest.TestCase):
    def test_com001(self):
        with open(paths_bin["COM001"], 'rb') as fp: srcdata = fp.read()
        ftexts = libtext.load_ftext(paths_ftext["COM001"])[1]

        # test basic insert
        data_sjis = libtext.insert_ftexts(srcdata, (None, ftexts), 
                        encoding='sjis', referobj=paths_bin["COM001"])
        data_tbl = libtext.insert_ftexts(paths_bin["COM001"], 
                        paths_ftext["COM001"], tblobj=paths_tbl["COM001"])
        self.assertEqual(data_sjis, data_tbl)

        # test enc_longer, enc_align
        text_added = "text_added試験"
        ftexts_longer = deepcopy(ftexts)
        ftexts_longer[1].text += text_added
        data_longer = libtext.insert_ftexts(paths_bin["COM001"], 
            (None, ftexts_longer), encoding='sjis', insert_longer=True)
        n = len(text_added.encode('sjis'))
        self.assertEqual(len(data_longer) , len(srcdata) + n)
        start, end = ftexts[-2].addr, ftexts[-2].addr + ftexts[-2].size 
        self.assertEqual(srcdata[start: end] , data_longer[start + n: end + n])
        align = 16
        n2 = max(n, align)
        data_longer = libtext.insert_ftexts(paths_bin["COM001"], 
            (None, ftexts_longer), encoding='sjis', insert_longer=True, insert_align=align)
        self.assertEqual(len(data_longer) , len(srcdata) + n2)
        self.assertEqual(srcdata[start: end] , data_longer[start + n2: end + n2])

        # test enc_shorter, bytes_padding
        ftexts_shorter = deepcopy(ftexts)
        ftexts_shorter[1].text = ftexts_shorter[1].text[:-4]
        n =  len(ftexts_shorter[1].text.encode('sjis')) - ftexts_shorter[1].size
        data_shorter = libtext.insert_ftexts(srcdata, 
            (None, ftexts_shorter), encoding='sjis', bytes_padding=b'\x80\x80')
        self.assertEqual(len(data_shorter) , len(srcdata))
        end = ftexts[1].addr + ftexts[1].size        
        self.assertEqual(bytes(data_shorter[end +n: end]) , (-n//2)*b'\x80\x80')
        data_shorter = libtext.insert_ftexts(srcdata, (None, ftexts_shorter), 
            encoding='sjis', insert_longer=True, insert_shorter=True)
        self.assertEqual(len(data_shorter) , len(srcdata) + n)
        start, end = ftexts[-2].addr, ftexts[-2].addr + ftexts[-2].size 
        self.assertEqual(srcdata[start: end] , data_shorter[start + n: end + n])

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(funcName)s: %(message)s")
    unittest.main()
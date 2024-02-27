import logging
import unittest
import zlib
from io import BytesIO

from common import *
import libutil as util
import ftextpack

class TestFpack(unittest.TestCase):
    def test_com001(self):
        bufio = BytesIO()
        with open(paths_bin["COM001"], 'rb') as fp: srcdata = fp.read()
        ftexts1, ftexts2 = util.load_ftext(paths_ftext["COM001"])
        ftexts1_map = dict((zlib.crc32(srcdata[t.addr: t.addr + t.size]), t) for t in ftexts1)
        
        # test pack_org
        bufstart = bufio.tell()
        fpack1 = ftextpack.pack_ftexts(paths_bin["COM001"], 
                    [(ftexts1, ftexts2)], bufio, encoding="sjis", pack_org=True)
        offset = fpack1.index.offset
        buf = bufio.getbuffer()[bufstart:]
        self.assertEqual(len(fpack1.infos), len(ftexts1))
        self.assertEqual(fpack1.content, buf[offset:])
        self.assertEqual(offset, bufio.tell() - bufstart - len(fpack1.content))
        for info in fpack1.infos:
            t = ftexts1_map[info.org.hash]
            self.assertEqual(info.org.addr, t.addr)
            self.assertEqual(info.org.size, t.size)
            start = info.org.offset + offset
            end = start + info.now.size
            self.assertEqual(srcdata[t.addr: t.addr+t.size], buf[start: end])
            start = info.now.offset + offset
            end = start + info.now.size
            self.assertEqual(zlib.crc32(buf[start: end]), info.org.hash)

        # test pack_compact
        del buf
        bufstart = bufio.tell()
        fpack2 = ftextpack.pack_ftexts(paths_bin["COM001"], 
                    [(ftexts1, ftexts2)], bufio, encoding="sjis", pack_compact=True)
        offset = fpack2.index.offset
        buf = bufio.getbuffer()[bufstart:]
        self.assertGreater(len(fpack1.content), len(fpack2.content))
        self.assertEqual(len(fpack2.infos), len(ftexts1))
        self.assertEqual(fpack2.content, buf[offset:])
        self.assertEqual(offset, bufio.tell() - bufstart - len(fpack2.content))
        for info in fpack2.infos:
            t = ftexts1_map[info.org.hash]
            self.assertEqual(info.org.addr, t.addr)
            self.assertEqual(info.org.size, t.size)
            start = info.now.offset + offset
            end = start + info.now.size
            self.assertEqual(zlib.crc32(buf[start: end]), info.org.hash)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(funcName)s: %(message)s")
    unittest.main()
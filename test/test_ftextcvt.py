import logging
import unittest
import tempfile

from common import *
import libutil as util
import ftextcvt

class TestCsv(unittest.TestCase):
    def test_com001(self):
        ftextlines = util.readlines(util.loadbytes(paths_ftext["COM001"]))
        csvlines = ftextcvt.ftext2csv(ftextlines)
        ftextlines2 = ftextcvt.csv2ftext(csvlines)
        assert_lines(self, ftextlines, ftextlines2)

class TestJson(unittest.TestCase):
    def test_com001(self):
        ftextlines = util.readlines(util.loadbytes(paths_ftext["COM001"]))
        jsonlines = ftextcvt.ftext2json(ftextlines)
        ftextlines2 = ftextcvt.json2ftext(b"".join([x.encode('utf-8') for x in jsonlines]))
        assert_lines(self, ftextlines, ftextlines2)

class TestDocx(unittest.TestCase):
    def test_com001(self):
        tmppath = tempfile.NamedTemporaryFile("wb+")
        ftextlines = util.readlines(util.loadbytes(paths_ftext["COM001"]))
        doc = ftextcvt.ftext2docx(ftextlines, tmppath)
        ftextlines2 = ftextcvt.docx2ftext(tmppath)
        assert_lines(self, ftextlines, ftextlines2)

class TestPretty(unittest.TestCase):
    def test_com001(self):
        ftextlines = util.readlines(util.loadbytes(paths_ftext["COM001"]))
        ftextlines2 = ftextcvt.ftext2pretty(ftextlines)
        assert_lines(self, ftextlines, ftextlines2)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(funcName)s: %(message)s")
    unittest.main()
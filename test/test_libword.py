import logging
import unittest
import numpy as np

from common import *
import libword

class TestWordAlgorithms(unittest.TestCase):
    def test_example_calclcs(self):
        self.assertEqual(libword.calc_lcs("abcde", "abcde"), 5)
        self.assertEqual(libword.calc_lcs("abcde", "abce"), 4)
        self.assertEqual(libword.calc_lcs("abce", "abcde"), 4)
        self.assertEqual(libword.calc_lcs("abcde", "dabcf"), 3)

    def test_example_calclcv(self):
        self.assertEqual(libword.calc_lev("abcde", "abcde"), 0)
        self.assertEqual(libword.calc_lev("abcde", "abce"), 1)
        self.assertEqual(libword.calc_lev("abcde", "dabcf"), 3)
        self.assertEqual(libword.calc_lev("dabcf", "abcde"), 3)

class TestWordOperations(unittest.TestCase):
    def test_example_matchline(self):
        lines1 = ["a1a2a3a4", "b1b2b3b4", "c1c2c3c4", "d1d2d3d4"]
        lines2 = ["c1c2z1c3c4", "d1dz22d3d4", "a1a2a3a4", "b1b2b3b4", "z1z2"]
        l1match, l2match = libword.match_line(lines1, lines2)
        self.assertTrue(np.array_equal(l1match, [2,3,0,1]))
        self.assertTrue(np.array_equal(l2match, [2,3,0,1,-1]))

    def test_example_countchar(self):
        lines = ["a1a2a3a4", "b1b2b3b4", "c1c2c3c4", "d1d2d3d4"]
        counter = libword.count_char(lines)
        self.assertEqual(sum(len(l) for l in lines), len(list(counter.elements())))

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(funcName)s: %(message)s")
    unittest.main()
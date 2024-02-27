import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), r"src"))
sys.path.append(os.path.join(os.path.dirname(__file__), r"../src"))

paths_bin = {'COM001': "test/sample/COM001"}
paths_tbl = {'COM001': "test/sample/COM001.tbl"}
paths_ftext = {'COM001': "test/sample/COM001.txt"} 

def assert_lines(self, lines1, lines2, ignore_len=2):
    lines1 = list(filter(lambda x: len(x) > ignore_len, lines1))
    lines2 = list(filter(lambda x: len(x) > ignore_len, lines2))
    self.assertEqual(len(lines1), len(lines2))
    for l1, l2 in zip(lines1, lines2):
        self.assertEqual(l1.rstrip('\r').rstrip('\n'), l2.rstrip('\r').rstrip('\n'))
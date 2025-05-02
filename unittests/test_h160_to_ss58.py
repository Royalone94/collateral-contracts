import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from scripts.h160_to_ss58 import *

class TestH160ToSS58(unittest.TestCase):
    def test_example(self):
        # Example test case
        self.assertEqual(1, 1)

if __name__ == '__main__':
    unittest.main() 
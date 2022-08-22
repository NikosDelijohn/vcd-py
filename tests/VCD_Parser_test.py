import unittest
import sys

sys.path.insert(0, "../src/")

from VCD_Parser import VCD_Parser
from utils import *

EVCD_FILE = "../misc/VCDS/dumpports_rtl.openMSP430_3.vcd"
SVCD_FILE = "../misc/bmu_full.vcd"

class TestFileParsing(unittest.TestCase):

    def test_init(self):

        self.assertIsNotNone(VCD_Parser("../misc/wikipedia.vcd",VCD_Type.Standard))
        self.assertIsNotNone(VCD_Parser("../misc/bmu_full.vcd",VCD_Type.Standard))
        self.assertIsNotNone(VCD_Parser("../misc/VCDS/dumpports_rtl.openMSP430_3.vcd",VCD_Type.Extended))

    def test_get_signal(self):
            
        TestObject_SVCD = VCD_Parser(SVCD_FILE,VCD_Type.Standard)
        TestObject_EVCD = VCD_Parser(EVCD_FILE,VCD_Type.Extended)

if __name__ == "__main__":
    unittest.main()
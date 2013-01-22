import unittest

from machine import Machine
from definition_parser import clean_definition, DefinitionParser

class ParserTest(unittest.TestCase):
    def setUp(self):
        self.dp = DefinitionParser()
    
    def tearDown(self):
        del self.dp
    
    def test_depracated_defs(self):
        d = "low ER intelligence"
        expRes = Machine("ER")
        expRes.partitions.append("low")
        expRes.partitions.append("intelligence")
        realRes = self.dp.parse_def(d)
        self.assertEqual(expRes, realRes)
    
if __name__ == '__main__':  
    ts = unittest.TestSuite()
    tl = unittest.TestLoader()   
    ts.addTest(tl.loadTestsFromTestCase(ParserTest))
    unittest.TextTestRunner(verbosity=2).run(ts)

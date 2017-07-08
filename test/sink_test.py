#!/usr/bin/env python3
import unittest
import tc.braces

class TestBraces(unittest.TestCase):
    def setUp(self):
        self.s = tc.braces.BraceParser()
    def tearDown(self):
        del self.s
    def test_00(self):
        cases = [
            ("", [""])
            ,("abc", ["abc"])
            ,("a,c", ["a,c"])
            ,("{xy}", ["xy"])
            ,("{x,y}", ["x","y"])
            ,("{x,y}v{p,q}", ["xvp", "xvq", "yvp", "yvq"])
            ,("x{y,z}", ["xy", "xz"])
            ,("p{q{r,s},t}", ["pqr","pqs", "pt"])
            ,("{{r,s}{v,w},t}a", ["rva","rwa","sva","swa","ta"])
            ,("j" * 1024, ["j" * 1024])
            ,("x{" + "y"*1024 + "}", [ "x" + "y" * 1024 ])
        ]
        for patstring, eolist in cases:
            with self.subTest(pat=patstring) as t:
                aolist = self.s.expand(patstring)
                # print(patstring,"->",aolist)
                # self.assertEqual(sorted(aolist), sorted(eolist), "same output strings")
                self.assertEqual(aolist, eolist, "same output strings")

##############################################################################
if __name__ == '__main__':
    unittest.main()
##############################################################################
# Local Variables:
# mode: python
# End:

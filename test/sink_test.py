#!/usr/bin/env python3
import os
import unittest
import sys
import tempfile
import time
import tc.sink

class TestAppender(unittest.TestCase):
    def test_ForeignFileAppender_text(self):
        TEXT = 'April is the cruellest month'
        with tempfile.TemporaryDirectory() as tmp_dir:
            destination = os.path.join(tmp_dir, "gfile.txt")
            with tc.sink.ForeignFileAppender(destination, False) as bridge:
                bridge.file().write(TEXT)
            with open(destination, 'r') as ifh:
                content = ifh.read()
            self.assertEqual(content, TEXT)
        
    def test_ForeignFileAppender_binary(self):
        DATA = (25559837).to_bytes(64, sys.byteorder)
        with tempfile.TemporaryDirectory() as tmp_dir:
            destination = os.path.join(tmp_dir, "gfile.dat")
            with tc.sink.ForeignFileAppender(destination, True) as bridge:
                bridge.file().write(DATA)
            with open(destination, 'rb') as ifh:
                content = ifh.read()
            self.assertEqual(content, DATA)


class TestSink(unittest.TestCase):
    def test_make_output_bridge_text(self):
        TEXT = 'April is the cruellest month'
        with tempfile.TemporaryDirectory() as tmp_dir:
            destination = os.path.join(tmp_dir, "gfile.txt")
            print(destination, file=sys.stderr)
            with tc.sink.make_output_bridge(destination, 'w') as ofh:
                ofh.write(TEXT)
            time.sleep(0.25)       # race condition with the child process
            with open(destination, 'r') as ifh:
                content = ifh.read()
            self.assertEqual(content, TEXT)

    def test_make_output_bridge_binary(self):
        DATA = (25559837).to_bytes(64, sys.byteorder)
        with tempfile.TemporaryDirectory() as tmp_dir:
            destination = os.path.join(tmp_dir, "gfile.dat")
            print(destination, file=sys.stderr)
            with tc.sink.make_output_bridge(destination, 'wb') as ofh:
                ofh.write(DATA)
            time.sleep(0.25)       # race condition with the child process
            with open(destination, 'rb') as ifh:
                content = ifh.read()
            self.assertEqual(content, DATA)

##############################################################################
if __name__ == '__main__':
    unittest.main()
##############################################################################
# Local Variables:
# mode: python
# End:

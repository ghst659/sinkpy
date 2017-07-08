#!/usr/bine/env python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import subprocess
import sys

def make_bridge(destination):
    """Create a bridge, returning the write file for the bridge."""
    result = None
    pipe_descriptors = os.pipe()
    dest_fh = open(destination, 'w')
    pid = os.fork()
    if pid == 0:
        os.close(pipe_descriptors[1])
        child_life(pipe_descriptors[0], dest_fh)
    else:
        dest_fh.close()
        os.close(pipe_descriptors[0])
        return os.fdopen(pipe_descriptors[1], 'w')

def child_life(fd_in, dest_fh):
    """The lifecycle of the child process."""
    with dest_fh, os.fdopen(fd_in, 'r') as in_stream:
        for line in in_stream:
            dest_fh.write(line)
            dest_fh.flush()
    os._exit(0)

def main(argv):
    """Send command output to a bridged file."""
    global me; me = os.path.basename(argv[0]) # name of this program
    global mydir; mydir = os.path.dirname(os.path.abspath(__file__))
    ################################
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("-o","--output", required=True, default=None,
                        dest='output', 
                        help="output filename.")
    parser.add_argument("-v","--verbose",
                        dest='verbose', action="store_true",
                        help="run verbosely")
    parser.add_argument("command",
                        metavar="COMMAND", nargs="+",
                        help="command to execute")
    args = parser.parse_args(args=argv[1:])  # will exit on parse error

    with make_bridge(args.output) as bridge:
        completion = subprocess.run(args.command, stdout=bridge)

    return completion.returncode

if __name__ == '__main__':
    sys.exit(main(sys.argv))

##############################################################################
# Local Variables:
# mode: python
# End:

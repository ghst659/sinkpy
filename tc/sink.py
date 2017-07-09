#!/usr/bine/env python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import subprocess
import sys

def make_output_bridge(destination, mode='w'):
    """Create a bridge, returning the write file for the bridge."""
    binary = 'b' in mode
    pipe_descriptors = os.pipe()
    dest_fh = open(destination, mode=mode)
    pid = os.fork()  # raises OSError if fork() fails
    if pid == 0:  # child process
        os.close(pipe_descriptors[1])
        rmode = 'r' + ('b' if binary else '')
        child_output(os.fdopen(pipe_descriptors[0], mode=rmode), dest_fh, binary)
    elif pid > 0:  # parent process
        dest_fh.close()
        os.close(pipe_descriptors[0])
        return os.fdopen(pipe_descriptors[1], mode=mode)
    else:
        raise OSError('failed fork')

def child_output(source_fh, dest_fh, binary):
    """The lifecycle of the child process."""
    with source_fh, dest_fh:
        if binary:
            BUFSIZ = 1
            buf = source_fh.read(BUFSIZ)
            while buf:
                dest_fh.write(buf)
                buf = source_fh.read(BUFSIZ)
        else:
            for line in source_fh:
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
    parser.add_argument("-b","--binary",
                        dest='binary', action="store_true",
                        help="open the bridge as a binary file.")
    parser.add_argument("-v","--verbose",
                        dest='verbose', action="store_true",
                        help="run verbosely")
    parser.add_argument("command",
                        metavar="COMMAND", nargs="+",
                        help="command to execute")
    args = parser.parse_args(args=argv[1:])  # will exit on parse error

    with make_output_bridge(args.output, mode=('w' + ('b' if args.binary else ''))) as bridge:
        completion = subprocess.run(args.command, stdout=bridge)

    return completion.returncode

if __name__ == '__main__':
    sys.exit(main(sys.argv))

##############################################################################
# Local Variables:
# mode: python
# End:

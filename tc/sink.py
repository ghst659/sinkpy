#!/usr/bine/env python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import subprocess
import sys
import threading

class ForeignFileAppender:
    """A context manager to pump data from a file into a foreign filesystem."""

    def __init__(self, foreign_path, binary_mode=False, buffer_size=-1, single_write=False):
        """Initialises the appender."""
        self._path = foreign_path
        self._bmode = 'b' if binary_mode else 't'
        self._bufsiz = buffer_size
        self._single = single_write
        self._thread = None
        self._input = None
        if binary_mode:
            if single_write:
                self._pump = self._pump_binary_single
            else:
                self._pump = self._pump_binary_iter
        else:
            if single_write:
                self._pump = self._pump_text_single
            else:
                self._pump = self._pump_text_iter
        
    def __enter__(self):
        read_mode = 'r' + self._bmode
        write_mode = 'w' + self._bmode
        append_mode = 'a' + self._bmode
        foreign_handle = open(self._path, append_mode)
        pipe_ends = os.pipe()
        input_handle = os.fdopen(pipe_ends[0], read_mode)
        self._input = os.fdopen(pipe_ends[1], write_mode)
        self._thread = threading.Thread(target=self._pump, args=(input_handle, foreign_handle))
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._input.close()
        self._thread.join()
        self._input = None
        self._thread = None

    def _pump_binary_single(self, input_source, output_sink):
        with input_source, output_sink:
            buffers = []
            buffer = input_source.read(self._bufsiz)
            while buffer:
                buffers.append(buffer)
                buffer = input_source.read(self._bufsiz)
            output_sink.write(b''.join(buffers))

    def _pump_binary_iter(self, input_source, output_sink):
        with input_source, output_sink:
            buffer = input_source.read(self._bufsiz)
            while buffer:
                output_sink.write(buffer)
                buffer = input_source.read(self._bufsiz)

    def _pump_text_single(self, input_source, output_sink):
        with input_source, output_sink:
            buffers = []
            for line in input_source:
                buffers.append(line)
            output_sink.write(''.join(buffers))
            output_sink.flush()

    def _pump_text_iter(self, input_source, output_sink):
        with input_source, output_sink:
            for line in input_source:
                output_sink.write(line)
                output_sink.flush()

    def file(self):
        return self._input

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

    # with make_output_bridge(args.output, mode=('w' + ('b' if args.binary else ''))) as bridge:
    #     completion = subprocess.run(args.command, stdout=bridge)

    with ForeignFileAppender(args.output, args.binary) as bridge:
        completion = subprocess.run(args.command, stdout=bridge.file())

    return completion.returncode

if __name__ == '__main__':
    sys.exit(main(sys.argv))

##############################################################################
# Local Variables:
# mode: python
# End:

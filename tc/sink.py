#!/usr/bine/env python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import subprocess
import sys
import threading

##############################################################################
# thread-based

class ForeignFileAppender:
    """A context manager to pump data from a file into a foreign filesystem."""

    def __init__(self, foreign_path, text_mode=False, buffer_size=-1, single_write=False):
        self._path = foreign_path
        self._mode = 't' if text_mode else 'b'
        self._bufsiz = buffer_size
        self._single = single_write
        self._thread = None
        self.intake = None      # public property
        if text_mode:
            if single_write:
                self._pump = self._pump_text_single
            else:
                self._pump = self._pump_text_iter
        else:
            if single_write:
                self._pump = self._pump_binary_single
            else:
                self._pump = self._pump_binary_iter
        
    def __enter__(self):
        read_mode = 'r' + self._mode
        write_mode = 'w' + self._mode
        append_mode = 'a' + self._mode
        foreign_handle = open(self._path, append_mode)
        pipe_ends = os.pipe()
        input_handle = os.fdopen(pipe_ends[0], read_mode)
        self.intake = os.fdopen(pipe_ends[1], write_mode)
        self._thread = threading.Thread(target=self._pump, args=(input_handle, foreign_handle))
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.intake.close()     # terminates self._thread
        self._thread.join()
        self.intake = None
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

##############################################################################
# process-based

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
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("-o","--output", required=True, default=None,
                        dest='output', 
                        help="output filename.")
    parser.add_argument("-b","--binary",
                        dest='binary', action="store_true",
                        help="open the bridge as a binary file.")
    parser.add_argument("command",
                        metavar="COMMAND", nargs="+",
                        help="command to execute")
    args = parser.parse_args(args=argv[1:])  # will exit on parse error

    with ForeignFileAppender(args.output, args.binary) as bridge:
        completion = subprocess.run(args.command, stdout=bridge.intake)

    return completion.returncode

if __name__ == '__main__':
    sys.exit(main(sys.argv))

##############################################################################
# Local Variables:
# mode: python
# End:

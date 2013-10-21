#!/usr/bin/env python
#
# on-off keying
#
# (C) 2013 Antoine Neuenschwander

"""
On-Off Keying
"""

from gnuradio import gr, digital, audio, blocks, eng_notation
from struct import *

def constellation_bask_make():
    "Returns constellation for binary amplitude shift keying"
    return digital.constellation_calcdist([0, 1], [1, 0], 1, 1)


class my_top_block(gr.top_block):
    
    def __init__(self):
        gr.top_block.__init__(self)
        
        # init packet source
        self._pkt_source = blocks.message_source(gr.sizeof_char, 8)
        
        # init modulator
        self._constellation = constellation_bask_make()
        self._modulator = digital.generic_mod(self._constellation,
            differential=False, samples_per_symbol=20, pre_diff_code=False)
        
        # init file sink
        self._file_sink = blocks.file_sink(gr.sizeof_gr_complex, "/tmp/out.dat")
        
        # wire everything up
        self.connect(self._pkt_source, self._modulator)
        self.connect(self._modulator, self._file_sink)
        
    def send_pkt(self, payload='',eof=False):
        if eof:
            msg = gr.message(1)
        else:
            msg = gr.message_from_string(payload)
        return self._pkt_source.msgq().insert_tail(msg)


if __name__ == '__main__':
    try:
        print "initializing"
        tb = my_top_block()
        tb.start()
        payload = ''
        payload += pack('!BBBBBBBB', 1,80,1,0,60,50,1,120)
        print "payload: " + repr(payload)
        tb.send_pkt(payload)
        print ("sent packet")
        tb.send_pkt(eof=True)
        tb.wait()
        print "done"
    except KeyboardInterrupt:
        pass

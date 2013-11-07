#!/usr/bin/env python
#
# on-off keying
#
# (C) 2013 Antoine Neuenschwander

'''
On-Off Keying
'''

from gnuradio import gr, blocks, digital, eng_notation
import numpy

# default values
_def_samples_per_symbol = 2

class bask_mod(gr.hier_block2):
    
    def __init__(self, samples_per_symbol=_def_samples_per_symbol):
        
        gr.hier_block2.__init__(self, 
            "bask_mod",
            gr.io_signature(1, 1, gr.sizeof_char),
            gr.io_signature(1, 1, gr.sizeof_gr_complex))
            
        self._samples_per_symbol = samples_per_symbol
    
        if self._samples_per_symbol < 2:
            raise TypeError, ("samples_per_symbol must be >= 2, is %d" % self._samples_per_symbol)
        
        self._bytes2chunks = \
            blocks.packed_to_unpacked_bb(self.bits_per_symbol(), gr.GR_MSB_FIRST)
        self._map = bask_map()
        self._chunks2symbols = digital.chunks_to_symbols_bc([0, 1])
        self._interp = bask_interp(self._samples_per_symbol)
        
        # connect
        self._blocks = [self, self._bytes2chunks, self._map, self._chunks2symbols, self._interp, self]
        self.connect(*self._blocks)
    
    def bits_per_symbol(self=None):
        return 1


class bask_map(gr.interp_block):
    
    def __init__(self):
        gr.interp_block.__init__(self,
            name="bask_map",
            in_sig=[numpy.uint8],
            out_sig=[numpy.uint8],
            interp=3
        )
    
    def work(self, input_items, output_items):
        for i in range(len(input_items[0])):
            output_items[0][3*i] = 1
            output_items[0][3*i + 1] = input_items[0][i]
            output_items[0][3*i + 2] = 0
        return len(output_items[0])



class bask_interp(gr.interp_block):
    
    def __init__(self, samples_per_symbol=_def_samples_per_symbol):
        gr.interp_block.__init__(self,
            name="bask_interp",
            in_sig=[numpy.complex64],
            out_sig=[numpy.complex64],
            interp=samples_per_symbol
        )
        self._samples_per_symbol = samples_per_symbol

    def work(self, input_items, output_items):
        for i in range(len(input_items[0])):
            j = i*self._samples_per_symbol
            k = j + self._samples_per_symbol
            output_items[0][j:k] = input_items[0][i]
        return len(output_items[0])


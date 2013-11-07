#!/usr/bin/env python
#
# on-off keying
#
# (C) 2013 Antoine Neuenschwander

"""
On-Off Keying
"""

from gnuradio import gr, analog, digital, audio, blocks, eng_notation, uhd
from gnuradio.wxgui import stdgui2, scopesink2, waterfallsink2
from grc_gnuradio import wxgui as grc_wxgui
from bask import bask_mod
import wx
import time
from struct import *
from thread import start_new_thread

def constellation_bask_make():
    "Returns constellation for binary amplitude shift keying"
    return digital.constellation_calcdist((0, 1), (0, 1), 1, 1)


class my_top_block(stdgui2.std_top_block):
    
    def __init__(self, frame, panel, vbox, argv):
        stdgui2.std_top_block.__init__(self, frame, panel, vbox, argv)
        
        ## Variable
        self._samp_rate = 1000000
        self._freq = 433.92e6
        self._unit = 2e-3
        
        # init packet source
        self._pkt_source = blocks.message_source(gr.sizeof_char, 8)
        
        # init modulator
        self._modulator = bask_mod(samples_per_symbol=int(self._unit*self._samp_rate))
        
        # init file sink
        self._file_sink = blocks.file_sink(gr.sizeof_gr_complex, "/tmp/out.dat")
        
        # init scope sink
        self._scope_sink = scopesink2.scope_sink_c(
            panel,
            title="Scope Plot",
            sample_rate=self._samp_rate,
            num_inputs=1,
            v_scale=0.01,
        	v_offset=0,
        	t_scale=0.5e-3
        )
        vbox.Add(self._scope_sink.win, 1, wx.EXPAND)
        
        # init waterfall sink
        self._waterfall_sink = waterfallsink2.waterfall_sink_c(
            panel,
            baseband_freq=self._freq,
            dynamic_range=100,
            ref_level=0,
            ref_scale=2.0,
            sample_rate=self._samp_rate,
            fft_size=512,
            fft_rate=15,
            average=False,
            avg_alpha=None
        )
        vbox.Add(self._waterfall_sink.win, 1, wx.EXPAND)
        
        # init button
        self._button = wx.Button(panel, id=wx.ID_ANY, label="Press Me!")
        self._button.Bind(wx.EVT_BUTTON, self.foo)
        vbox.Add(self._button, 1, wx.EXPAND)
        
        # init uhd sink (USRP)
        self._uhd_sink = uhd.usrp_sink(device_addr='', stream_args=uhd.stream_args('fc32'))
        self._uhd_sink.set_samp_rate(self._samp_rate)
        self._uhd_sink.set_center_freq(self._freq, 0)
        self._uhd_sink.set_gain(15, 0)
        self._uhd_sink.set_antenna('TX/RX', 0)
        
        # init uhd source (USRP)
        #self._uhd_source = uhd.usrp_source(device_addr='', stream_args=uhd.stream_args('fc32'))
        #self._uhd_source.set_samp_rate(self._samp_rate)
        #self._uhd_source.set_center_freq(433.935e6, 0)
        #self._uhd_source.set_gain(0, 0)
        #self._uhd_source.set_antenna("RX2", 0)
        
        # wire everything up
        # tx path
        self.connect(self._pkt_source, self._modulator)
        self.connect(self._modulator, self._uhd_sink)
        self.connect(self._modulator, self._scope_sink)
        self.connect(self._modulator, self._waterfall_sink)
        self.connect(self._modulator, self._file_sink)
        
        # rx path
        #self.connect(self._uhd_source, (self._scope_sink, 0))
        #self.connect(self._uhd_source, (self._waterfall_sink, 0))
        #self.connect(self._uhd_source, self._file_sink)
        
    def send_pkt(self, payload='',eof=False):
        if eof:
            msg = gr.message(1)
        else:
            msg = gr.message_from_string(payload)
        return self._pkt_source.msgq().insert_tail(msg)

    def foo(self, event):
        print "foo!"
        self.send_pkt("\x30\xA6\x84\x00")


if __name__ == '__main__':
    try:
        print "initializing"
        app = stdgui2.stdapp(my_top_block, "gr-ook")
        app.MainLoop()
    except KeyboardInterrupt:
        pass

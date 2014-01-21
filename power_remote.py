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
import bitstring
from bitstring import BitArray, BitStream


class power_remote(stdgui2.std_top_block):
    
    button_codes = {
        'A': '0101010110',
        'B': '0101011001',
        'C': '0101100101',
        'D': '0110010101',
        'E': '1001010101',
        'M': '0101010101'
    }
    
    def __init__(self, frame, panel, vbox, argv):
        stdgui2.std_top_block.__init__(self, frame, panel, vbox, argv)
        self._frame = frame;
        self._panel = panel;
        self._vbox = vbox;
        
        ## Variable
        self._samp_rate = 1000000
        self._freq = 433.92e6
        self._unit = 5.33e-4 # 533us unit pulse width
        
        self._pkt_source = blocks.message_source(gr.sizeof_char, 8)
        self._modulator = bask_mod(samples_per_symbol=int(self._unit*self._samp_rate))
        self.init_gui()
        
        # init uhd sink (USRP)
        self._uhd_sink = uhd.usrp_sink(device_addr='', stream_args=uhd.stream_args('fc32'))
        self._uhd_sink.set_samp_rate(self._samp_rate)
        self._uhd_sink.set_center_freq(self._freq, 0)
        self._uhd_sink.set_gain(15, 0)
        self._uhd_sink.set_antenna('TX/RX', 0)
        
        # wire everything up
        self.connect(self._pkt_source, self._modulator, self._uhd_sink)

    def init_gui(self):
        self._vbox.AddSpacer(20)
        
        # add on/off buttons
        grid = wx.GridSizer(rows=5, cols=2, vgap=5, hgap=5)
        grid.AddMany([
            (wx.Button(self._panel, label='A on', name='A1')), (wx.Button(self._panel, label='A off', name='A0')),
            (wx.Button(self._panel, label='B on', name='B1')), (wx.Button(self._panel, label='B off', name='B0')),
            (wx.Button(self._panel, label='C on', name='C1')), (wx.Button(self._panel, label='C off', name='C0')),
            (wx.Button(self._panel, label='D on', name='D1')), (wx.Button(self._panel, label='D off', name='D0')),
            (wx.Button(self._panel, label='Master on', name='M1')), (wx.Button(self._panel, label='Master off', name='M0')),
        ])
        self._panel.Bind(wx.EVT_BUTTON, self.button_clicked)
        self._vbox.Add(grid, 1, wx.EXPAND)
        
        # add some vertical space
        self._vbox.AddSpacer(30)
        
        # add dip switches (toggle buttons)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddMany([
            (wx.ToggleButton(self._panel, label='1', size=(35, 20), name='DP1')),
            (wx.ToggleButton(self._panel, label='2', size=(35, 20), name='DP2')),
            (wx.ToggleButton(self._panel, label='3', size=(35, 20), name='DP3')),
            (wx.ToggleButton(self._panel, label='4', size=(35, 20), name='DP4')),
            (wx.ToggleButton(self._panel, label='5', size=(35, 20), name='DP5')),
        ])
        self._vbox.Add(hbox, 1, wx.EXPAND)
        
        
    def send_pkt(self, payload='',eof=False):
        if eof:
            msg = gr.message(1)
        else:
            msg = gr.message_from_string(payload)
        # send message twice
        for i in range(2):
            self._pkt_source.msgq().insert_tail(msg)
        
    def button_clicked(self, event):
        name = event.GetEventObject().GetName()
        button = name[0]
        state = name[1] == '1'
        print 'button clicked: ' + name
        payload = BitArray(bin=self.get_address())          # address as defined by dip switches
        payload += BitArray(bin='01'*11)                    # padding
        payload += BitArray(bin='10' if state else '01')    # switch state
        payload += BitArray(bin='0101')                     # padding
        payload += BitArray(bin=power_remote.button_codes[button])     # button code
        payload += BitArray(bin='01000000')                 # padding and end
        print payload.bin
        self.send_pkt(payload.bytes)
    
    def get_address(self):
        addr = ''
        for i in range(1, 6):
            name = "DP%d" % (i)
            dp = self._panel.FindWindowByName(name)
            addr += '10' if dp.GetValue() else '01'
        return addr

if __name__ == '__main__':
    try:
        print "initializing"
        app = stdgui2.stdapp(power_remote, "PowerRemote")
        app.MainLoop()
    except KeyboardInterrupt:
        pass

#!/bin/env python

import sys
import time

try:
    import queue
except ImportError:
    import Queue as queue
#~ import json
#~ import ConfigParser

import serial
from serial.threaded import LineReader
from serial.threaded import ReaderThread

from fabtotum.os.config import *

class PrintLines(LineReader):
    
    TERMINATOR = b'\n'
    
    def connection_made(self, transport):
        super(PrintLines, self).connection_made(transport)
        sys.stdout.write('port opened\n')
        self.transport.serial.reset_input_buffer()
        #self.write_line('hello world')

    #~ def handle_packet(self, packet):
        #~ print 'handle_packet'
        
    #~ def data_received(self, data):
        #~ print('data received', repr(data))

    def handle_line(self, data):
        print 'handle_line'
        sys.stdout.write('line received: {}\n'.format(repr(data)))

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        sys.stdout.write('port closed\n')

ser = serial.serial_for_url(UART_PORT_NAME, baudrate=UART_BAUD_RATE, timeout=5)
protocol = ReaderThread(ser, PrintLines)
protocol.write_line('M105')
protocol.write_line('G28 X0 Y0')
    
time.sleep(5)
#~ protocol.write_line('hello')
#~ time.sleep(2)


#~ class GCodeReader(LineReader):
    
    #~ def __init__(self, ser):
        #~ super(GCodeReader, self).__init__(ser)
    
    #~ def handle_line(self, line):
        #~ print 'handle_line: ['+line+']'
        
#~ ser = serial.serial_for_url(UART_PORT_NAME, baudrate=UART_BAUD_RATE, timeout=UART_READ_TIMEOUT)

#~ gc = GCodeReader()



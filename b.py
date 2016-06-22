#!/bin/env python
# -*- coding: utf-8; -*-
#
# (c) 2015 FABtotum, http://www.fabtotum.com
#
# This file is part of FABUI.
#
# FABUI is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# FABUI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FABUI.  If not, see <http://www.gnu.org/licenses/>.


# Import standard python module
import time
from threading import Event, Thread

# Import internal modules
from fabtotum.totumduino.gcode import GCodeService

###############################

gcs = GCodeService()
gcs.start()

is_active = True

def temperature_monitor_handler():
    global is_active
    print "temperature_monitor thread: started"
    while is_active:
        for i in range(50):
            reply = gcs.send('M105')
            print 'Temp [',reply,']'
            
            #time.sleep(0.5)
            
            #reply = gcs.send('G0 Z+0.1')
            
            time.sleep(0.1)
            
            if not is_active:
                break
        is_active = False
        #gcs.stop()
    print "temperature_monitor thread: stopped"

def gcode_pause_handler():
    global is_active
    while is_active:
        time.sleep(3)
        print "[ PAUSE ]"
        gcs.pause()
        #~ gcs.send('G91')
        #~ gcs.send('G0 X0')
        #~ time.sleep(0.5)
        time.sleep(10)
        print "[ RESUME ]"
        gcs.resume()
        break
#~ def gcode_sender_handler():
    #~ global is_active
    #~ print "gcode_sender thread: started"
    
    #~ gcs.send('G28 X0 Y0')
    
    #~ while is_active:
        
        #~ gcs.send('G91')
        #~ gcs.send('G1 X10 F3000')
        #~ gcs.send('G1 Y10 F3000')
        #~ gcs.send('G1 X-10 F3000')
        #~ gcs.send('G1 Y-10 F3000')
        #~ #gcs.send('M503')
        #~ #gcs.send('M300')
        #~ #gcs.send('M400')
        #~ gcs.send('M740')
        #~ #gcs.send('M743')
    #~ print "gcode_sender thread: stoppped"

#~ gcode_sender = Thread(target=gcode_sender_handler)
#~ gcode_sender.start()

def file_done_callback():
    global is_active
    is_active = False
    gcs.stop()
    
temperature_monitor = Thread(target=temperature_monitor_handler)
temperature_monitor.start()

pause_thread = Thread(target=gcode_pause_handler)
pause_thread.start()

gcs.send_file('./test.gcode', 'raw', file_done_callback)

#~ gcode_sender.join()
temperature_monitor.join()

#!/bin/env python
# -*- coding: utf-8; -*-
#
# (c) 2016 FABtotum, http://www.fabtotum.com
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

__author__ = "Krios Mane, Daniel Kesler"
__license__ = "GPL - https://opensource.org/licenses/GPL-3.0"
__version__ = "1.0"

# Import standard python module
import json
import re
import os
import time
import gettext

# Import external modules
import RPi.GPIO as GPIO

# Import internal modules
from fabtotum.fabui.config import ConfigService

# Set up message catalog access
tr = gettext.translation('usbdrive_monitor', 'locale', fallback=True)
_ = tr.ugettext

class GPIOMonitor:
    
    ACTION_PIN = None
    
    def __init__(self, WebSocket, gcs, action_pin):
        self.ws = WebSocket
        self.gcs = gcs
        self.ACTION_PIN = int(action_pin)
        
    def gpioEventListener(self, chanel):
        """
        Triggered when a level change on a pin is detected.
        """
        print "====== START ============"
        print 'GPIO STATUS: ', GPIO.input(chanel)
        if GPIO.input(chanel) == 0 :
            reply = self.gcs.send("M730")
            
            if reply:
                reply = reply[0]

            print "REPLY: ", reply
            #~ search = re.search('ERROR\s:\s(\d+)', reply)
            #~ if search != None:
                #~ errorNumber = int(search.group(1))
                #~ manageErrorNumber(errorNumber)
            #~ else:
                #~ print "Error number not recognized: ", reply
        GPIO_STATUS = GPIO.HIGH
        print 'GPIO STATUS on EXIT: ', GPIO.input(chanel)
        print "====== EXIT ============"

    def start(self):
        # Setup BCM GPIO numbering
        GPIO.setmode(GPIO.BCM)                                          
        # Set GPIO as input (button)
        GPIO.setup(self.ACTION_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        # Register callback function for gpio event, callbacks are handled from a separate thread
        GPIO.add_event_detect(self.ACTION_PIN, GPIO.BOTH, callback=self.gpioEventListener, bouncetime=100)
        
    def stop(self):
        """ Clean-up """
        GPIO.remove_event_detect(self.ACTION_PIN)
        
    def join(self):
        """ Place holder """
        pass

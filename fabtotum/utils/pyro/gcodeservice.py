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

# Import external modules
import Pyro4

# Import internal modules
from fabtotum.totumduino.gcode import GCodeService

###############################

#Pyro4.config.COMMTIMEOUT=0.5
PYRO_URI_FILE = '/run/gcodeservice.uri'
GCS = None

class GCodeServicePyroServer:
    def __init__(self):
        print "New GCodeService Wrapper"
        self.client_callback = None
    
    def send(self, code, expected_reply = 'ok', block = True):
        global GCS
        return GCS.send(code.encode('latin-1'), expected_reply.encode('latin-1'), block)
        
    def send_file(self, filename):
        global GCS
        GCS.send_file(filename)
    
    def __callback_handler(self, action, data):
        if self.client_callback:
            self.client_callback.do_callback(action, data)
    
    def register_callback(self, callback_name, uri):
        global GCS
        self.client_callback = Pyro4.Proxy(uri)
        GCS.register_callback(callback_name, self.__callback_handler)

    def get_progress(self):
        global GCS
        return GCS.get_progress()

    def get_idle_time(self):
        global GCS
        return GCS.get_idle_time()

def GCodeServiceApplication():
    global GCS
    
    GCS = GCodeService()
    GCS.start() 
    #daemon = Pyro4.Daemon(port=9999)
    daemon = Pyro4.Daemon()

    service_wrapper = GCodeServicePyroServer()
    uri = daemon.register(service_wrapper, objectId='GCodeService')

    with open(PYRO_URI_FILE, 'w') as file:
        file.write(uri.asString())

    daemon.requestLoop()

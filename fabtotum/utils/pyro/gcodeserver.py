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


# Import standard python module
import time

# Import external modules
import Pyro4

# Import internal modules
from fabtotum.totumduino.gcode import GCodeService

###############################

#Pyro4.config.COMMTIMEOUT=0.5
PYRO_URI_FILE = '/run/gcodeservice.uri'
GCS = None

class GCodeServiceServerPyroWrapper(object):
    def __init__(self, gcs):
        print "New GCodeService Wrapper"
        self.gcs = gcs
        self.client_callback = None
        self.callback_list = []
    
    def send(self, code, expected_reply = 'ok', block = True, timeout = None):
        return self.gcs.send(code.encode('latin-1'), expected_reply.encode('latin-1'), block, timeout)
        
    def send_file(self, filename):
        self.gcs.send_file(filename)
    
    def __callback_handler(self, action, data):
        if self.callback_list:
            for tup in self.callback_list:
                remote = tup[0]
                try:
                    remote.do_callback(action, data)
                except CommunicationError:
                    self.callback_list.remove(tup)
    
    def register_callback(self, callback_name, uri):
        remote = Pyro4.Proxy(uri)
        
        self.callback_list.append( (remote, uri) )
            
        if self.callback_list:
            self.gcs.register_callback(callback_name, self.__callback_handler)

    def unregister_callback(self, callback_name, uri):
        for client in self.callback_list:
            if client[1] == uri:
                self.callback_list.remove(client)

        if not self.callback_list:
            self.gcs.unregister_callback()

    def get_progress(self):
        return self.gcs.get_progress()

    def get_idle_time(self):
        return self.gcs.get_idle_time()

class GCodeServiceServer(object):
    
    def __init__(self, gcs = None):
        
        if gcs:
            self.gcs = gcs
            self.gcs_external = True
        else:
            self.gcs = GCodeService()
            self.gcs.start()
            self.gcs_external = False
        
        daemon = Pyro4.Daemon()
        wrapper = GCodeServiceServerPyroWrapper(self.gcs)
        uri = daemon.register(wrapper, objectId='GCodeService')
        
        self.daemon = daemon
        self.wrapper = wrapper
        self.uri = uri
        
        # Write pyro_uri to a file
        with open(PYRO_URI_FILE, 'w') as file:
            file.write(uri.asString())

    def loop(self):
        self.daemon.requestLoop()
        if not self.gcs_external:
            self.gcs.loop()
        
    def stop(self):
        self.daemon.shutdown()
        time.sleep(1)

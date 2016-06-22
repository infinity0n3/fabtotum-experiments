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

# Import external modules
import Pyro4
Pyro4.config.COMMTIMEOUT = 3
Pyro4.config.MAX_RETRIES = 40
Pyro4.config.LOGWIRE = True
#Pyro4.config.PYRO_LOGFILE = 'client.pyro.log'

# Import internal modules
from fabtotum.utils.singleton import Singleton
from gcodeservice import PYRO_URI_FILE

###############################

class CallbackHandler:
    def __init__(self, gc):
        self.gc = gc
    
    def do_callback(self, action, data):
        if action:
            print "client: callback received (", action, data, ")"
            self.gc.do_callback(action, data)
   
class GCodeServicePyroClient:
    __metaclass__ = Singleton
    
    def __init__(self):
        self.daemon = None
        self.running = True
        self.callback = None
 
        self.ch = CallbackHandler(self)
 
        with open(PYRO_URI_FILE, 'r') as file:
            uri = file.read()
            print uri
            self.server = Pyro4.Proxy(uri)
        #~ uri = 'PYRO:GCodeService@localhost:9999'
        #~ self.server = Pyro4.Proxy(uri)
    
    def do_callback(self, action, data):
        if self.callback:
            print 'calling callback'
            self.callback(action, data)
    
    def still_running(self):
        return self.running
    
    def __close(self):
        print "client: stop"
        self.running = False
        self.daemon.shutdown()
    
    def __register_callback(self, callback_fun):
        print "client: register_callback"
        
        if not self.daemon:
            self.daemon = Pyro4.Daemon()
            self.uri = self.daemon.register( self.ch )
        
        self.callback = callback_fun
        self.server.register_callback('<pyro_callback>', self.uri.asString())
    
    def __loop(self):
        print "client: loop"
        self.daemon.requestLoop(loopCondition=self.still_running)
        self.daemon.close()
        print "client: loop end"
    
    def __getattr__(self, attr):            
        if attr == 'register_callback':
            return self.__register_callback
        elif attr == 'stop':
            return self.__close
        elif attr == 'loop':
            return self.__loop
        else:
            return getattr(self.server, attr)
        

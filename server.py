#!/bin/env python
import Pyro4
Pyro4.config.COMMTIMEOUT = 1.0 # without this daemon.close() hangs

class TestAPI:
    def __init__(self, daemon):
        self.daemon = daemon
        self.running = True
        
    def hello(self, msg):
        print 'client said {}'.format(msg)
        return 'hola'
        
    def shutdown(self):
        print 'shutting down...'
        self.running = False
        
    def callme(self):
        print 'calling you', self.uri
        self.callback.do_callback()
        
    def register_callback(self, uri):
        self.uri = uri
        self.callback = Pyro4.Proxy(uri)

if __name__ == '__main__':
    daemon = Pyro4.Daemon(port=9999)
    tapi = TestAPI(daemon)
    uri = daemon.register(tapi, objectId='TestAPI')
    def checkshutdown():
        return tapi.running
    print 'starting loop'
    daemon.requestLoop(loopCondition=checkshutdown) # permits self-shutdown
    print 'exited requestLoop'
    daemon.close()
    print 'daemon closed'

#!/bin/env python
import Pyro4
import time
from threading import Event, Thread

Pyro4.config.COMMTIMEOUT = 1.0 # without this daemon.close() hangs

class CallbackAPI:
    def __init__(self, daemon):
        self.daemon = daemon
        self.running = True
                
    def shutdown(self):
        print 'shutting down...'
        self.running = False
        
    def do_callback(self):
        print 'callback'
        pass
                
if __name__ == '__main__':
    
        daemon = Pyro4.Daemon(port=9998)
        tapi = CallbackAPI(daemon)
        uri_callback = daemon.register(tapi, objectId='CallbackAPI')
            
        uri = 'PYRO:TestAPI@localhost:9999'
        remote = Pyro4.Proxy(uri)
        response = remote.hello('hello')
        print 'server said {}'.format(response)
        
        def thread_fun():
            time.sleep(2)
            remote.callme()
        
        remote.register_callback(uri_callback)

        def checkshutdown():
            return tapi.running
            
        callback_thread = Thread(target = thread_fun)
        callback_thread.start()
            
        print 'starting loop'
        daemon.requestLoop(loopCondition=checkshutdown) # permits self-shutdown
        
        remote.shutdown()
        remote._pyroRelease()
        print 'client exiting'

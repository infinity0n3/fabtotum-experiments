#!/bin/env python
# -*- coding: utf-8; -*-

#from gcodeclient import GCodeServicePyroClient
from fabtotum.utils.pyro.gcodeclient import GCodeServiceClient

def callback_function(action, data):
    print "Callback working:", action
    if action == 'file_done':
        gcs.stop()
    else:
        print action, data
        

gcs = GCodeServiceClient()

#reply = gcs.send('M728')
#print reply

#~ reply = gcs.send('M119')
#~ print reply

print gcs.send('M744')
print gcs.send('M742')

#~ gcs.register_callback(callback_function)

#~ gcs.send_file('test_short.gcode')
#~ gcs.send_file('fake_cura.gcode')

#~ gcs.loop()

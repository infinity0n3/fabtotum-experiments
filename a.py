#!/bin/env python
# -*- coding: utf-8; -*-

from gcodeclient import GCodeServicePyroClient

def callback_function(action, data):
    print "Callback working:", action
    if action == 'file_done':
        gcs.stop()

gcs = GCodeServicePyroClient()

#reply = gcs.send('M728')
#print reply

#reply = gcs.send('M119')
#print reply

#gcs.register_callback(callback_function)

gcs.send_file('test_short.gcode')

#gcs.loop()

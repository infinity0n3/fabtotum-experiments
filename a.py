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

reply = gcs.send('M105')
print reply

#~ reply = gcs.send('M119')
#~ print reply

data = gcs.send('M503')
#data = "".join(data, "\n")
#z_probe_old = float(data.split("Z Probe Length: ")[1].split("\n")[0])

for line in data:
    if line.startswith("echo:Z Probe Length:"):
        print line.split("Z Probe Length: ")[1]

#print "z_probe_old",z_probe_old
print "-------------"
data = gcs.send('M114')
data = data[0]
z_touch = float(data.split("Z:")[1].split(" ")[0])
print z_touch

#~ gcs.register_callback(callback_function)

#~ gcs.send_file('test_short.gcode')
#~ gcs.send_file('fake_cura.gcode')

gcs.loop()

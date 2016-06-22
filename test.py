#!/bin/env python
from fabtotum.totumduino.gcode import GCode

gc = GCode()

reply = gc.send('M105')
print '[' + reply + ']'

reply = gc.send('G28 X0 Y0', 'ok', 40)
print '[' + reply + ']'

gc.close()

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
import sys
import re
import json
import argparse
import time
from threading import Event, Thread

# Import external modules

# Import internal modules
from fabtotum.fabui.config      import ConfigService
#~ from fabtotum.totumduino.gcode  import GCodeService
from gcodeclient import GCodeServicePyroClient

###################################################
def parse_temperature(line):
    temperature_match = re.search('ok\sT:([0-9]+\.[0-9]+)\s\/([0-9]+\.[0-9]+)\sB:([0-9]+\.[0-9]+)\s\/([0-9]+\.[0-9]+)\s', line)
    if temperature_match != None:
        return float(temperature_match.group(1)) \
            ,  float(temperature_match.group(2)) \
            ,  float(temperature_match.group(3)) \
            ,  float(temperature_match.group(4))
###################################################

config = ConfigService()

# SETTING EXPECTED ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("file",         help="gcode file to execute")
parser.add_argument("command_file", help="command file")
parser.add_argument("task_id",      help="id_task")
parser.add_argument("monitor",      help="monitor file",  default=config.get('general', 'task_monitor'), nargs='?')
parser.add_argument("trace",        help="trace file",  default=config.get('general', 'trace'), nargs='?')
parser.add_argument("--ext_temp",   help="extruder temperature (for UI feedback only)",  default=180, nargs='?')
parser.add_argument("--bed_temp",   help="bed temperature (for UI feedback only)",  default=50,  nargs='?')

# GET ARGUMENTS
args = parser.parse_args()

# INIT VARs
gcode_file      = args.file         # GCODE FILE
command_file    = args.command_file # OVERRIDE DATA FILE 
task_id         = args.task_id      # TASK ID  
monitor_file    = args.monitor      # TASK MONITOR FILE (write stats & task info, es: temperatures, speed, etc
log_trace       = args.trace        # TASK TRACE FILE 
ext_temp_target = args.ext_temp     # EXTRUDER TARGET TEMPERATURE (previously read from file) 
bed_temp_target = args.bed_temp     # BED TARGET TEMPERATURE (previously read from file) 

is_active       = True

#~ gcs = GCodeService(
    #~ serial_port = config.get('serial', 'port'),
    #~ serial_baud = config.get('serial', 'baud')
    #~ )
#~ gcs.start()
gcs = GCodeServicePyroClient()

# READ TEMPERATURES BEFORE PRINT STARTS (improve UI feedback response)
reply = gcs.send("M105")
if reply:
    ext_temp, ext_temp_target, bed_temp, bed_temp_target = parse_temperature(reply[0])

def attribute_change_callback(data):
    print "Attribute changed"

def file_done_callback(data):
    global is_active
    print "File DONE"
    is_active = False
    gcs.stop()
    
def callback_handler(action, data):
    if action == 'file_done':
        file_done_callback(data)
    elif action == 'attr_change':
        attribute_change_callback(data)

def temperature_monitor_loop():
    global gcs
    global ext_temp
    global ext_temp_target
    global bed_temp
    global bed_temp_target
    
    while is_active:
        reply = gcs.send("M105")
        if reply:
            ext_temp, ext_temp_target, bed_temp, bed_temp_target = parse_temperature(reply[0])
        print ext_temp, ext_temp_target, bed_temp, bed_temp_target
        time.sleep(1)

temperature_monitor = Thread(target=temperature_monitor_loop)
temperature_monitor.start()

gcs.register_callback(callback_handler)

gcs.send_file(gcode_file)

gcs.loop()
temperature_monitor.join()

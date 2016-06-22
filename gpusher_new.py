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
from threading import Event, Thread, RLock

# Import external modules
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# Import internal modules
from fabtotum.fabui.config import ConfigService
from fabtotum.utils.gcodefile import GCodeFile
from fabtotum.utils.pyro.gcodeclient import GCodeServiceClient


################################################################################
def parse_temperature(line):
    temperature_match = re.search('ok\sT:([0-9]+\.[0-9]+)\s\/([0-9]+\.[0-9]+)\sB:([0-9]+\.[0-9]+)\s\/([0-9]+\.[0-9]+)\s', line)
    if temperature_match != None:
        return float(temperature_match.group(1)) \
            ,  float(temperature_match.group(2)) \
            ,  float(temperature_match.group(3)) \
            ,  float(temperature_match.group(4))

def writeMonitor(filename, info):
    """
    Write stats to monitor file
    """    
    _layers =   {
                'total' : info['layer_count'], 
                'actual': info['current_layer']
                }
                
    _stats  =   {
                "percent"           : info['progress'],
                "line_number"       : info['current_line_number'],
                "extruder"          : info['ext_temp'],
                "bed"               : info['ext_temp_target'],
                "extruder_target"   : info['bed_temp'],
                "bed_target"        : info['bed_temp_target'] ,
                "z_override"        : info['z_override'],
                "layers"            : info['layer_count'],
                "fan"               : info['fan'],
                "speed"             : info['speed'],
                "flow_rate"         : info['flow_rate']
                }
                
    _tip    =   {
                "show"              : info['tip'],
                "message"           : info['message']
                }
                
    _print  =   {
                "name"              : info["gcode_info"]["filename"],
                "lines"             : info["gcode_info"]["line_count"],
                "print_started"     : "", #str(print_started),
                "started"           : "", #str(started),
                "paused"            : "", #str(paused),
                "completed"         : info["completed"],
                "completed_time"    : info["completed_time"],
                "shutdown"          : "", #str(shutdown),
                "tip"               : _tip,
                "stats"             : _stats
                }
    
    engine = 'unknown'
    if 'slicer' in info["gcode_info"]:
        engine = info["gcode_info"]["slicer"]
    
    stats   =   {
                "type"      : "print", 
                "print"     : _print,
                "engine"    : str(engine),
                "task_id"   : info["task_id"]
                }
    
    with open(filename,'w+') as file:
        file.write(json.dumps(stats))

    return

def GCodePusherApplication(
        gcode_file, command_file, task_id, monitor_file, log_trace,
        ext_temp, ext_temp_target, bed_temp, bed_temp_target 
    ):
    """
    GCode pusher application.
    """
    
    def first_move_callback(gcs):
        print "First move"
        
        monitor_lock.acquire()
        monitor_info['print_started'] = True
        monitor_lock.release()
    
    def gcode_comment_callback(gcs, data):
        monitor_lock.acquire()
        if 'layer' in data:
            monitor_info['current_layer'] = data['layer']
        monitor_lock.release()

    def gcode_action_callback(gcs, data):
        print "GCode action", data
        monitor_lock.acquire()
        monitor_lock.release()

    def file_done_callback(gcs, data):
        monitor_lock.acquire()
        monitor_info["completed"] = True
        monitor_lock.release()
        gcs.stop()
        
    def callback_handler(action, data):
        if action == 'file_done':
            file_done_callback(gcs, data)
        elif action == 'gcode_comment':
            gcode_comment_callback(gcs, data)
        elif action == 'gcode_action':
            gcode_action_callback(gcs, data)
        elif action == 'first_move':
            first_move_callback(gcs)

    def temperature_monitor_thread(gcs):
        while gcs.still_running():
            reply = gcs.send("M105")
            
            # Don't lock until there is something to process
            # so that other threads are not unnecessary blocked
            monitor_lock.acquire()
            
            if reply:
                monitor_info['ext_temp'],
                monitor_info['ext_temp_target'],
                monitor_info['bed_temp'],
                monitor_info['bed_temp_target'] = parse_temperature(reply[0])
            
            monitor_info['progress'] = gcs.get_progress()
            
            monitor_lock.release()
            
            writeMonitor(monitor_file, monitor_info)
            
            time.sleep(1)
            
    # Application body
    gcs = GCodeServiceClient()

    # READ TEMPERATURES BEFORE PRINT STARTS (improve UI feedback response)
    reply = gcs.send("M105")
    if reply:
        ext_temp, ext_temp_target, bed_temp, bed_temp_target = parse_temperature(reply[0])

    gfile = GCodeFile(gcode_file)

    monitor_info = {
        "progress"              : 0.0,
        "completed"             : False,
        "completed_time"        : 0,
        "layer_count"           : 0,
        "current_layer"         : 0,
        "filename"              : gcode_file,
        "task_id"               : task_id,
        "ext_temp"              : ext_temp,
        "ext_temp_target"       : ext_temp_target,
        "bed_temp"              : bed_temp,
        "bed_temp_target"       : bed_temp_target,
        "z_override"            : 0.0,
        "fan"                   : 0.0,    
        "speed"                 : 100.0,
        "flow_rate"             : 100.0,
        "tip"                   : False,
        "message"               : '',
        "current_line_number"   : 0,
        "gcode_info"            : gfile.info
    }

    monitor_lock = RLock()

    temperature_monitor = Thread(target=temperature_monitor_thread, args=[gcs] )
    temperature_monitor.start()

    gcs.register_callback(callback_handler)

    gcs.send_file(gcode_file)

    gcs.loop()
    temperature_monitor.join()
    
def main():
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
    ext_temp        = 0.0
    ext_temp_target = args.ext_temp     # EXTRUDER TARGET TEMPERATURE (previously read from file) 
    bed_temp        = 0.0
    bed_temp_target = args.bed_temp     # BED TARGET TEMPERATURE (previously read from file) 

    GCodePusherApplication(gcode_file, command_file, task_id, monitor_file, log_trace,
                    ext_temp, ext_temp_target, bed_temp, bed_temp_target)


if __name__ == "__main__":
    main()

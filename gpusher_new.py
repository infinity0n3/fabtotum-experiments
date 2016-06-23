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
import logging
from threading import Event, Thread, RLock

import gettext

# Import external modules
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# Import internal modules
from fabtotum.fabui.config import ConfigService
from fabtotum.utils.gcodefile import GCodeFile
from fabtotum.utils.pyro.gcodeclient import GCodeServiceClient

# Set up message catalog access
tr = gettext.translation('gpusher', 'locale', fallback=True)
_ = tr.ugettext

################################################################################
def parse_temperature(line):
    match = re.search('ok\sT:(?P<T>[0-9]+\.[0-9]+)\s\/(?P<TT>[0-9]+\.[0-9]+)\sB:(?P<B>[0-9]+\.[0-9]+)\s\/(?P<BT>[0-9]+\.[0-9]+)\s', line)
    if match:
        return ( match.group('T'), match.group('TT'), match.group('B'), match.group('BT') )

def writeMonitor(filename, info):
    """
    Write stats to monitor file
    """    
    _layers =   {
                'total' : str(info['layer_count']), 
                'actual': str(info['current_layer'])
                }
                
    _stats  =   {
                "percent"           : str(info['progress']),
                "line_number"       : str(info['current_line_number']),
                "extruder"          : str(info['ext_temp']),
                "bed"               : str(info['bed_temp']),
                "extruder_target"   : str(info['ext_temp_target']),
                "bed_target"        : str(info['bed_temp_target'] ),
                "z_override"        : str(info['z_override']),
                "layers"            : str(info['layer_count']),
                "fan"               : str(info['fan']),
                "speed"             : str(info['speed']),
                "flow_rate"         : str(info['flow_rate'])
                }
                 
    _tip    =   {
                "show"              : str(info['tip']),
                "message"           : str(info['message'])
                }
                 
    _print  =   {
                "name"              : str(info["gcode_info"]["filename"]),
                "lines"             : str(info["gcode_info"]["line_count"]),
                "print_started"     : str(info["print_started"]),
                "started"           : str(info["started"]),
                "paused"            : str(info["paused"]),
                "completed"         : str(info["completed"]),
                "completed_time"    : str(info["completed_time"]),
                "shutdown"          : str(info["auto_shutdown"]),
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
    
    ''' WRITE TO TRACE FILE '''
    def trace(log_msg):
        logging.info(log_msg)
        print log_msg
        
    ''' RESET LOG TRACE to avoid annoing verbose '''
    def resetTrace():
        with open(log_trace, 'w'):
            pass
    
    def shutdown_procedure(gcs):
        trace( _("Schutting down...") )
        # Wait for all commands to be finished
        reply = gcs.send('M400')
        # Tell totumduino Raspberry is going to sleep :'(
        reply = gcs.send('M729')
        # Stop the GCodeService connection
        gcs.stop()
        
        # TODO: trigger system shutdown
        
    
    def first_move_callback(gcs):
        trace( _("Print Started") )
        
        monitor_lock.acquire()
        monitor_info['print_started'] = True
        monitor_lock.release()
    
    def gcode_comment_callback(gcs, data):
        monitor_lock.acquire()
        if 'layer' in data:
            monitor_info['current_layer'] = data['layer']
        monitor_lock.release()

    def temp_change_callback(gcs, action, data):
        monitor_lock.acquire()
        
        if action == 'all':
            #print "Ext: {0}, Bed: {1}".format(data[0], data[1])
            monitor_info['ext_temp'] = float(data[0])
            monitor_info['bed_temp'] = float(data[1])
        elif action == 'bed':
            #print "Bed: {0}".format(data[0])
            monitor_info['bed_temp'] = float(data[0])
        elif action == 'ext':
            #print "Ext: {0}".format(data[0])
            monitor_info['ext_temp'] = float(data[0])
            
        monitor_lock.release()
        
        writeMonitor(monitor_file, monitor_info)
        
    def gcode_action_callback(gcs, action, data):
        #print _("GCode action"), data
        
        monitor_lock.acquire()
        
        if action == 'heating':
            
            
            if data[0] == 'M109':
                trace( _("Wait for nozzle temperature to reach {0}&deg;C").format(data[1]) )
                monitor_info['ext_temp_target'] = float(data[1])
            elif data[0] == 'M190':
                trace( _("Wait for bed temperature to reach {0}&deg;C").format(data[1]) )
                monitor_info['bed_temp_target'] = float(data[1])
            elif data[0] == 'M104':
                trace( _("Nozzle temperature set to {0}&deg;C").format(data[1]) )
                monitor_info['ext_temp_target'] = float(data[1])
            elif data[0] == 'M140':
                trace( _("Bed temperature set to {0}&deg;C").format(data[1]) )
                monitor_info['bed_temp_target'] = float(data[1])
            
        elif action == 'cooling':
            if data[0] == 'M106':
                value = int((float( data[1] ) / 255) * 100)
                trace( _("Fan value set to {0}%").format(value) )
            elif data[0] == 'M107':
                trace( _("Fan off") )
            
        elif action == 'printing':
            pass
            
        elif action == 'message':
            print "MSG: {0}".format(data)

        monitor_lock.release()
        
        writeMonitor(monitor_file, monitor_info)

    def file_done_callback(gcs, data):
        print _("File Done")
        
        monitor_lock.acquire()
        
        monitor_info["completed_time"] = int(time.time())
        monitor_info["completed"] = True        
        monitor_info['progress'] = 100.0 #gcs.get_progress()
        writeMonitor(monitor_file, monitor_info)
        
        monitor_lock.release()
        
        if monitor_info["auto_shutdown"]:
            shutdown_procedure(gcs)
        else:
            gcs.stop()
    
    def state_change_callback(data):
        monitor_lock.acquire()
        
        if data == 'paused':
            trace( _("Print is now paused") )
            monitor_info["paused"] = True
        elif data == 'resumed':
            monitor_info["paused"] = False
            
        monitor_lock.release()
        
        writeMonitor(monitor_file, monitor_info)
    
    def callback_handler(action, data):
        if action == 'file_done':
            file_done_callback(gcs, data)
        elif action == 'gcode_comment':
            gcode_comment_callback(gcs, data)
        elif action.startswith('gcode_action'):
            gcode_action_callback(gcs, action.split(':')[1], data)
        elif action == 'first_move':
            first_move_callback(gcs)
        elif action.startswith('temp_change'):
            temp_change_callback(gcs, action.split(':')[1], data)
        elif action == 'state_change':
            state_change_callback(gcs)

    def temperature_monitor_thread(gcs):
        while gcs.still_running():
            reply = gcs.send("M105")
            
            # Don't lock until there is something to process
            # so that other threads are not unnecessary blocked
            monitor_lock.acquire()
            
            if reply:
                #print reply
                a, b, c, d = parse_temperature(reply[0])
                monitor_info['ext_temp'] = a
                monitor_info['ext_temp_target'] = b
                monitor_info['bed_temp'] = c
                monitor_info['bed_temp_target'] = d
            
            monitor_info['progress'] = gcs.get_progress()
            
            #print monitor_info['ext_temp'], monitor_info['progress']
            
            monitor_lock.release()
            
            writeMonitor(monitor_file, monitor_info)
            
            time.sleep(1)
            
    ''' WATCHDOG CLASS HANDLER FOR DATA FILE COMMAND '''
    class OverrideCommandsHandler(PatternMatchingEventHandler):
        backtrack = []
        
        def catch_all(self, event, op):
            if event.is_directory:
                return
                
            if(event.src_path == command_file):
                with open(event.src_path) as f:
                    for line in f:
                        c = line.rstrip()
                        if not c in ovr_cmd and c != "": 
                            ovr_cmd.append(c)
                            #~ if c=="!kill":
                                #~ killed=True
                                #~ EOF=True
                                
                open(event.src_path, 'w').close()
                
        def on_modified(self, event):
            self.catch_all(event, 'MOD')
          
    # Application body
    gcs = GCodeServiceClient()

    # READ TEMPERATURES BEFORE PRINT STARTS (improve UI feedback response)
    reply = gcs.send("M105")
    if reply:
        ext_temp, ext_temp_target, bed_temp, bed_temp_target = parse_temperature(reply[0])

    gfile = GCodeFile(gcode_file)

    monitor_info = {
        "progress"              : 0.0,
        "paused"                : False,
        "print_started"         : False,
        "started"               : time.time(),
        "auto_shutdown"         : False,
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

    logging.basicConfig( filename=log_trace, level=logging.INFO, format='%(message)s')
    resetTrace()

    monitor_lock = RLock()

    temperature_monitor = Thread(target=temperature_monitor_thread, args=[gcs] )
    temperature_monitor.start()
    
    event_handler = OverrideCommandsHandler(patterns=[command_file])
    observer = Observer()
    observer.schedule(event_handler, '/var/www/tasks/', recursive=True)
    observer.start()

    gcs.register_callback(callback_handler)

    gcs.send_file(gcode_file)

    gcs.loop()
    observer.stop()
    temperature_monitor.join()
    observer.join()
    
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

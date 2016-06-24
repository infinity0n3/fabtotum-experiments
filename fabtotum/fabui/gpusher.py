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
from fabtotum.utils.gcodefile import GCodeFile, GCodeInfo
from fabtotum.utils.pyro.gcodeclient import GCodeServiceClient

# Set up message catalog access
tr = gettext.translation('gpusher', 'locale', fallback=True)
_ = tr.ugettext

################################################################################
def parse_temperature(line):
    match = re.search('ok\sT:(?P<T>[0-9]+\.[0-9]+)\s\/(?P<TT>[0-9]+\.[0-9]+)\sB:(?P<B>[0-9]+\.[0-9]+)\s\/(?P<BT>[0-9]+\.[0-9]+)\s', line)
    if match:
        return ( match.group('T'), match.group('TT'), match.group('B'), match.group('BT') )

class GCodePusher(object):
    """
    GCode pusher application.
    """
    
    def __init__(self, log_trace, monitor_file = None, gcs = None, use_callback = True):
        
        self.config = ConfigService()
        
        self.monitor_file = monitor_file
        self.trace_file = log_trace
        
        self.monitor_lock = RLock()
        self.monitor_info = {
            "progress"              : 0.0,
            "paused"                : False,
            "print_started"         : False,
            "started"               : time.time(),
            "auto_shutdown"         : False,
            "completed"             : False,
            "completed_time"        : 0,
            "layer_count"           : 0,
            "current_layer"         : 0,
            "filename"              : "",
            "task_id"               : 0,
            "ext_temp"              : 0.0,
            "ext_temp_target"       : 0.0,
            "bed_temp"              : 0.0,
            "bed_temp_target"       : 0.0,
            "z_override"            : 0.0,
            "fan"                   : 0.0,    
            "speed"                 : 100.0,
            "flow_rate"             : 100.0,
            "tip"                   : False,
            "message"               : '',
            "current_line_number"   : 0,
            "gcode_info"            : None
        }
        
        if not gcs:
            self.gcs = GCodeServiceClient()
        else:
            self.gcs = gcs
        
        if use_callback:
            self.gcs.register_callback(self.callback_handler)
        
        self.macro_error = 0
        self.macro_warning = 0
        self.macro_skipped = 0
        
        self.progress_monitor = None
        
        logging.basicConfig( filename=log_trace, level=logging.INFO, format='%(message)s')
    
    def writeMonitor(self):
        """
        Write stats to monitor file
        """
        _layers =   {
                    'total' : str(self.monitor_info['layer_count']), 
                    'actual': str(self.monitor_info['current_layer'])
                    }
 
        _stats  =   {
                    "percent"           : str(self.monitor_info['progress']),
                    "line_number"       : str(self.monitor_info['current_line_number']),
                    "extruder"          : str(self.monitor_info['ext_temp']),
                    "bed"               : str(self.monitor_info['bed_temp']),
                    "extruder_target"   : str(self.monitor_info['ext_temp_target']),
                    "bed_target"        : str(self.monitor_info['bed_temp_target'] ),
                    "z_override"        : str(self.monitor_info['z_override']),
                    "layers"            : str(self.monitor_info['layer_count']),
                    "fan"               : str(self.monitor_info['fan']),
                    "speed"             : str(self.monitor_info['speed']),
                    "flow_rate"         : str(self.monitor_info['flow_rate'])
                    }
                                
        _tip    =   {
                    "show"              : str(self.monitor_info['tip']),
                    "message"           : str(self.monitor_info['message'])
                    }

        if self.monitor_info["gcode_info"]:
            filename = self.monitor_info["gcode_info"]["filename"]
            line_count = self.monitor_info["gcode_info"]["line_count"]
        else:
            filename =''
            line_count = 0

         
        _print  =   {
                    "name"              : str(filename),
                    "lines"             : str(line_count),
                    "print_started"     : str(self.monitor_info["print_started"]),
                    "started"           : str(self.monitor_info["started"]),
                    "paused"            : str(self.monitor_info["paused"]),
                    "completed"         : str(self.monitor_info["completed"]),
                    "completed_time"    : str(self.monitor_info["completed_time"]),
                    "shutdown"          : str(self.monitor_info["auto_shutdown"]),
                    "tip"               : _tip,
                    "stats"             : _stats
                    }

        engine = 'unknown'
        if self.monitor_info["gcode_info"]:
            if 'slicer' in self.monitor_info["gcode_info"]:
                engine = self.monitor_info["gcode_info"]["slicer"]
        
        stats   =   {
                    "type"      : "print", 
                    "print"     : _print,
                    "engine"    : str(engine),
                    "task_id"   : self.monitor_info["task_id"]
                    }
            
        if self.monitor_file:
            with open(self.monitor_file,'w+') as file:
                file.write(json.dumps(stats))

        return
    
    ''' WRITE TO TRACE FILE '''
    def trace(self, log_msg):
        logging.info(log_msg)
        
    ''' RESET LOG TRACE to avoid annoing verbose '''
    def resetTrace(self):
        with open(self.trace_file, 'w'):
            pass
    
    def shutdown_procedure(self):
        self.trace( _("Schutting down...") )
        
        # Wait for all commands to be finished
        reply = self.gcs.send('M400')
        
        # Tell totumduino Raspberry is going to sleep :'(
        reply = self.gcs.send('M729')
        
        # Stop the GCodeService connection
        self.gcs.stop()
        
        # TODO: trigger system shutdown
        
    
    def first_move_callback(self):
        self.trace( _("Task Started") )
        
        self.monitor_lock.acquire()
        self.monitor_info['print_started'] = True
        self.monitor_lock.release()
    
    def gcode_comment_callback(self, data):
        self.monitor_lock.acquire()
        if 'layer' in data:
            self.monitor_info['current_layer'] = data['layer']
        self.monitor_lock.release()

    def temp_change_callback(self, action, data):
        self.monitor_lock.acquire()
        
        if action == 'all':
            #print "Ext: {0}, Bed: {1}".format(data[0], data[1])
            self.monitor_info['ext_temp'] = float(data[0])
            self.monitor_info['bed_temp'] = float(data[1])
        elif action == 'bed':
            #print "Bed: {0}".format(data[0])
            self.monitor_info['bed_temp'] = float(data[0])
        elif action == 'ext':
            #print "Ext: {0}".format(data[0])
            self.monitor_info['ext_temp'] = float(data[0])
            
        self.monitor_lock.release()
        
        self.writeMonitor()
        
    def gcode_action_callback(self, action, data):
        
        self.monitor_lock.acquire()
        
        if action == 'heating':

            if data[0] == 'M109':
                self.trace( _("Wait for nozzle temperature to reach {0}&deg;C").format(data[1]) )
                self.monitor_info['ext_temp_target'] = float(data[1])
            elif data[0] == 'M190':
                self.trace( _("Wait for bed temperature to reach {0}&deg;C").format(data[1]) )
                self.monitor_info['bed_temp_target'] = float(data[1])
            elif data[0] == 'M104':
                self.trace( _("Nozzle temperature set to {0}&deg;C").format(data[1]) )
                self.monitor_info['ext_temp_target'] = float(data[1])
            elif data[0] == 'M140':
                self.trace( _("Bed temperature set to {0}&deg;C").format(data[1]) )
                self.monitor_info['bed_temp_target'] = float(data[1])
            
        elif action == 'cooling':
            
            if data[0] == 'M106':
                value = int((float( data[1] ) / 255) * 100)
                self.trace( _("Fan value set to {0}%").format(value) )
            elif data[0] == 'M107':
                self.trace( _("Fan off") )
            
        elif action == 'printing':
            pass
            
        elif action == 'message':
            print "MSG: {0}".format(data)
            
        self.monitor_lock.release()
        
        self.writeMonitor()

    def file_done_callback(self):
        if self.monitor_info["auto_shutdown"]:
            self.shutdown_procedure()
        else:
            self._stop()
            
    def __file_done_callback(self, data):
        self.monitor_lock.acquire()
        
        self.monitor_info["completed_time"] = int(time.time())
        self.monitor_info["completed"] = True        
        self.monitor_info['progress'] = 100.0 #gcs.get_progress()
        self.writeMonitor()
        
        self.monitor_lock.release()
        
        self.file_done_callback()
    
    def state_change_callback(self, data):
        self.monitor_lock.acquire()
        
        if data == 'paused':
            self.trace( _("Print is now paused") )
            self.monitor_info["paused"] = True
        elif data == 'resumed':
            self.monitor_info["paused"] = False
            
        self.monitor_lock.release()
        
        self.writeMonitor()
    
    def progress_callback(self, percentage):
        pass
    
    def callback_handler(self, action, data):
        if action == 'file_done':
            self.__file_done_callback(data)
        elif action == 'gcode_comment':
            self.gcode_comment_callback(data)
        elif action.startswith('gcode_action'):
            self.gcode_action_callback(action.split(':')[1], data)
        elif action == 'first_move':
            self.first_move_callback()
        elif action.startswith('temp_change'):
            self.temp_change_callback(action.split(':')[1], data)
        elif action == 'state_change':
            self.state_change_callback()

    def progress_monitor_thread(self):
        old_progress = -1
        monitor_write = False
        
        while self.gcs.still_running():
            
            progress = self.gcs.get_progress()
            
            if self.monitor_info["gcode_info"]:
                if self.monitor_info["gcode_info"]["type"] == GCodeInfo.PRINT:
                    reply = self.gcs.send("M105")
                    a, b, c, d = parse_temperature(reply[0])
                    self.monitor_lock.acquire()
                    self.monitor_info['ext_temp'] = a
                    self.monitor_info['ext_temp_target'] = b
                    self.monitor_info['bed_temp'] = c
                    self.monitor_info['bed_temp_target'] = d
                    self.monitor_lock.release()
                    monitor_write = True
                
            if old_progress != progress:
                old_progress = progress
                self.monitor_lock.acquire()
                self.monitor_info['progress'] = progress
                self.monitor_lock.release()
                self.progress_callback(progress)
                monitor_write = True

            if monitor_write:
                self.writeMonitor()
                monitor_write = False

            time.sleep(2)
            
    #~ ''' WATCHDOG CLASS HANDLER FOR DATA FILE COMMAND '''
    #~ class OverrideCommandsHandler(PatternMatchingEventHandler):
        #~ backtrack = []
        
        #~ def catch_all(self, event, op):
            #~ if event.is_directory:
                #~ return
                
            #~ if(event.src_path == command_file):
                #~ with open(event.src_path) as f:
                    #~ for line in f:
                        #~ c = line.rstrip()
                        #~ if not c in ovr_cmd and c != "": 
                            #~ ovr_cmd.append(c)
                            #~ if c=="!kill":
                                #~ killed=True
                                #~ EOF=True
                                
                #~ open(event.src_path, 'w').close()
                
        #~ def on_modified(self, event):
            #~ self.catch_all(event, 'MOD')
       
    def prepare(self, gcode_file, task_id,
                    ext_temp = 0.0, ext_temp_target = 0.0,
                    bed_temp = 0.0, bed_temp_target = 0.0,
                    rpm = 0):
        
        gfile = GCodeFile(gcode_file)
        
        self.monitor_info["progress"] = 0.0
        self.monitor_info["paused"] = False
        self.monitor_info["print_started"] = False
        self.monitor_info["started"] = time.time()
        self.monitor_info["auto_shutdown"] = False
        self.monitor_info["completed"] = False
        self.monitor_info["completed_time"] = 0
        self.monitor_info["layer_count" ] = 0
        self.monitor_info["current_layer"] = 0
        self.monitor_info["filename"] = gcode_file
        self.monitor_info["task_id"] = task_id
        self.monitor_info["ext_temp"] = ext_temp
        self.monitor_info["ext_temp_target"] = ext_temp_target
        self.monitor_info["bed_temp"] = bed_temp
        self.monitor_info["bed_temp_target"] = bed_temp_target
        self.monitor_info["z_override"] = 0.0
        self.monitor_info["rpm"] = 0
        self.monitor_info["fan"] = 0.0
        self.monitor_info["speed"] = 100.0
        self.monitor_info["flow_rate"] = 100.0
        self.monitor_info["tip"] = False
        self.monitor_info["message"] = ''
        self.monitor_info["current_line_number"] = 0
        self.monitor_info["gcode_info"] = gfile.info
        
        #~ self.temperature_monitor = Thread( target=self.temperature_monitor_thread )
        #~ self.temperature_monitor.start()
        if self.monitor_file:
            print "Creating monitor thread"
            
            self.progress_monitor = Thread( target=self.progress_monitor_thread )
            self.progress_monitor.start() 
        else:
            print "Skipping monitor thread"
        
        if gfile.info['type'] == GCodeInfo.PRINT:
            # READ TEMPERATURES BEFORE PRINT STARTS (improve UI feedback response)
            reply = self.gcs.send("M105")
            if reply:
                ext_temp, ext_temp_target, bed_temp, bed_temp_target = parse_temperature(reply[0])

        self.monitor_info["ext_temp"] = ext_temp
        self.monitor_info["ext_temp_target"] = ext_temp_target
        self.monitor_info["bed_temp"] = bed_temp
        self.monitor_info["bed_temp_target"] = bed_temp_target
        self.monitor_info["z_override"] = 0.0
        self.monitor_info["rpm"] = rpm
        
        self.resetTrace()
    
    def loop(self):
        """
        Wait for all GCodePusher threads to finish.
        """
        self.gcs.loop()
        if self.progress_monitor:
            self.progress_monitor.join()
        time.sleep(0.5)
        
    def __stop_thread(self):
        self.gcs.stop()   
        
    def stop(self):
        """
        Signal all GCodePusher threads to stop.
        """
        stop_thread = Thread( target = self.__stop_thread )
        stop_thread.start()
        
    def send(self, code, expected_reply = 'ok', block = True, timeout = None, trace = None):
        """
        Send a single gcode command and display trace message.
        """
        if trace:
            self.trace(trace)
        return self.gcs.send(code, expected_reply, block, timeout)
    
    def reset_macro_status(self):
        self.macro_warning = 0
        self.macro_error = 0
        self.macro_skipped = 0
        
    def macro(self, code, expected_reply, timeout, error_msg, delay_after, warning=False, verbose=True):
        """
        """
        if self.macro_error == 0:
            if verbose:
                self.trace(error_msg)
            
            reply = self.gcs.send(code)
            if expected_reply:
                # Check if the reply is as expected
                if reply[0] != expected_reply:
                    if warning:
                        self.trace(error_msg + _(": Warning!"))
                        self.macro_warning += 1
                    else:
                        self.trace(error_msg + _(": Failed ({0})".format(reply[0]) ))
                        self.macro_error += 1
        else:
            self.trace(error_msg + _(": Skipped"))
            self.macro_skipped += 1
                
        #time.sleep(delay_after) #wait the desired amount
        
    def send_file(self, filename):
        self.gcs.send_file(filename)
    
#~ def main():
    #~ config = ConfigService()

    #~ # SETTING EXPECTED ARGUMENTS
    #~ parser = argparse.ArgumentParser()
    #~ parser.add_argument("file",         help="gcode file to execute")
    #~ parser.add_argument("command_file", help="command file")
    #~ parser.add_argument("task_id",      help="id_task")
    #~ parser.add_argument("monitor",      help="monitor file",  default=config.get('general', 'task_monitor'), nargs='?')
    #~ parser.add_argument("trace",        help="trace file",  default=config.get('general', 'trace'), nargs='?')
    #~ parser.add_argument("--ext_temp",   help="extruder temperature (for UI feedback only)",  default=180, nargs='?')
    #~ parser.add_argument("--bed_temp",   help="bed temperature (for UI feedback only)",  default=50,  nargs='?')

    #~ # GET ARGUMENTS
    #~ args = parser.parse_args()

    #~ # INIT VARs
    #~ gcode_file      = args.file         # GCODE FILE
    #~ command_file    = args.command_file # OVERRIDE DATA FILE 
    #~ task_id         = args.task_id      # TASK ID  
    #~ monitor_file    = args.monitor      # TASK MONITOR FILE (write stats & task info, es: temperatures, speed, etc
    #~ log_trace       = args.trace        # TASK TRACE FILE 
    #~ ext_temp        = 0.0
    #~ ext_temp_target = args.ext_temp     # EXTRUDER TARGET TEMPERATURE (previously read from file) 
    #~ bed_temp        = 0.0
    #~ bed_temp_target = args.bed_temp     # BED TARGET TEMPERATURE (previously read from file) 

    #~ GCodePusherApplication(gcode_file, command_file, task_id, monitor_file, log_trace,
                    #~ ext_temp, ext_temp_target, bed_temp, bed_temp_target)


#~ if __name__ == "__main__":
    #~ main()

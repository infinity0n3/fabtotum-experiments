#!/bin/env python
# -*- coding: utf-8; -*-

# Import standard python module
    
# Import external modules
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# Import internal modules

command_file = '/mnt/nfs/print.data'

''' WATCHDOG CLASS HANDLER FOR DATA FILE COMMAND '''
class OverrideCommandsHandler(PatternMatchingEventHandler):
    
    def on_modified(self, event):
        new_commands = False
        
        if event.is_directory:
            print "is a directory"
            return
        if(event.src_path == command_file):
            with open(event.src_path) as f:
                for line in f:
                    c = line.rstrip()
                    new_commands = True
                    print "command:", c
                    #if not c in ovr_cmd and c != "": 
                    #    ovr_cmd.append(c)
            
            if new_commands:
                open(event.src_path, 'w').close()
    #~ def on_modified(self, event):
        #~ print event
        #~ self.catch_all(event, 'MOD')

event_handler = OverrideCommandsHandler(patterns=[command_file])
observer = Observer()
observer.schedule(event_handler, '/mnt/nfs', recursive=True)
observer.start()

print "started"

while 1:
    pass

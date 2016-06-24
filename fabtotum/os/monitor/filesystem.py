# Import standard python module
import json
import gettext

# Import external modules
from watchdog.events import PatternMatchingEventHandler
from watchdog.events import FileSystemEventHandler

# Import internal modules
from fabtotum.fabui.config              import ConfigService

class CommandParser:
    
    def __init__(self, gcs):
        self.gcs = gcs
    
    def parse_command(self, line):
        args = line.split(':')
        try:
            cmd = args[0]
            if cmd == '!kill':      #~ !kill
                self.gcs.abort()
                
            elif cmd == '!pause':   #~ !pause
                # execute gmacro pause_position
                self.gcs.pause()
                
            elif cmd == '!resume':  #~ !resume
                # execute gmacro resume_from_pause_position
                self.gcs.resume()
                
            elif cmd == '!z_plus':  #~ !z_plus:<float>
                pass
                
            elif cmd == '!z_minus': #~ !z_minus:<float>
                pass
                
            elif cmd == '!shutdown':#~ !shutdown:<on|off>
                pass
                
            elif cmd == '!speed':   #~ !speed:<float>
                self.gcs.send('M S{0}'.format(args[1]), block=False)
                
            elif cmd == '!fan':     #~ !fan:<int>
                self.gcs.send('M106 S{0}\r\n'.format(args[1]), block=False)
                
            elif cmd == '!flow_rate':#~ !flow_rate:<float>
                self.gcs.send('M S{0}\r\n', block=False)
                
            elif cmd == '!gcode':   #~ !gcode:<gcode>
                self.gcs.send('{0}\r\n'.format(args[1]), block=False)
                
            elif cmd == '!file':    #~ !file:<filename>
                pass

        except Exception as e:
            # Just ignore this command
            print "Error parsing command [{0}]".format(line), e
    
    def parse_file(self, filename):
        erase_file = False
        
        with open(filename, 'r+') as file:
            for line in file:
                line = line.strip()
                erase_file = True
                if line:
                    self.parse_command(line)
                
        # Erase the file.
        if erase_file:
            open(filename, 'w').close()

###################################################################################################################
## Event Listener for the most used files
###################################################################################################################
class FolderTempMonitor(PatternMatchingEventHandler):
    
    patterns = []
    ignore_directories = None
    ignore_patterns = None 
    case_sensitive = None
    ws = None #web socket, used to notify UI
    TRACE = None
    MACRO_RESPONSE = None
    TASK_MONITOR = None
    COMMAND = None
    
    def __init__(self, WebSocket, gcs, trace_file, monitor_file, response_file, command_file):
        
        self.TRACE = trace_file
        self.COMMAND = command_file
        self.TASK_MONITOR = monitor_file
        self.MACRO_RESPONSE = response_file
        self.gcs = gcs
        
        self.parser = CommandParser(gcs)
        
        self.patterns = [self.TRACE, self.COMMAND, self.TASK_MONITOR, self.MACRO_RESPONSE]
        self.ignore_directories = None
        self._ignore_patterns = None
        self.case_sensitive = None
        self.ws = WebSocket
        
    def on_modified(self, event):
        
        messageType = ''
        messageData = ''
        
        #print "Monitor:", event.src_path
        
        if event.src_path == self.TRACE:
            messageData = {'type': 'trace', 'content': str(self.getFileContent(self.TRACE))}
            messageType = "macro"
            self.sendMessage(messageType, messageData)
            
        elif event.src_path == self.COMMAND:
            self.parser.parse_file(self.COMMAND)
            
        #~ elif event.src_path == self.TASK_MONITOR:
            #~ pass
        #~ elif event.src_path == self.MACRO_RESPONSE:
            #~ pass
            
        
            
        
    def on_created(self, event):
        #self.process(event)
        print "CRAETED: ", event.src_path
        #self.ws.send("CRAETED")
    
    def on_deleted(self, event):
        #self.process(event)
        print "DELETED: ", event.src_path
        #self.ws.send("CRAETED")
        
    def sendMessage(self, type, data):
        message = {'type': type, 'data':data}
        self.ws.send(json.dumps(message))
        
    def getFileContent(self, file_path):
        file = open(file_path, 'r')
        content= file.read()
        file.close()
        return content



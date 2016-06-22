#!/bin/env python
# -*- coding: utf-8; -*-
#
# (c) 2016 FABtotum, http://www.fabtotum.com
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
import time
from threading import Event, Thread
try:
    import queue
except ImportError:
    import Queue as queue
    
# Import external modules
import serial

# Import internal modules
from fabtotum.os.config import UART_PORT_NAME, UART_BAUD_RATE
from fabtotum.utils.singleton import Singleton
from fabtotum.utils.gcodefile import GCodeFile

#############################################

class Command(object):
    
    NONE   = 'none'
    GCODE  = 'gcode'
    FILE   = 'file'
    ABORT  = 'abort'
    PAUSE  = 'pause'
    RESUME = 'resume'
    KILL   = 'kill'
    
    def __init__(self, id, data = None, expected_reply = 'ok'):
        self.id = id
        self.data = data
        self.reply = []
        self.ev = Event()
        self.expected_reply = expected_reply

    def __str__(self):
        msg = 'cmd: ' + self.id
        if isinstance(self.data, str):
            msg += ', data: ' + self.data
        else:
            msg += ', data: <' + str(type(self.data)) + '>'
        return msg
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.id == other
        elif isinstance(other, Command):
            return self.id == other.id
        else:
            return NotImplemented
    
    def notify(self):
        self.ev.set()
        
    def hasExpectedReply(self, line):
        return line[:len(self.expected_reply)] == self.expected_reply;
        
    def hasError(self, line):
        return line[:5] == 'ERROR';
    
    @classmethod
    def abort(cls):
        return cls(Command.ABORT, None)

    @classmethod
    def kill(cls):
        return cls(Command.KILL, None)

    @classmethod
    def pause(cls):
        return cls(Command.PAUSE, None)

    @classmethod
    def resume(cls):
        return cls(Command.RESUME, None)

    @classmethod
    def gcode(cls, code, expected_reply):
        return cls(Command.GCODE, code, expected_reply)

    @classmethod
    def file(cls, filename):
        return cls(Command.FILE, filename)

def is_valid_gcode_line(line):
    pass

ERROR_CODES = {
    #error codes
    '100' : 'ERROR_KILLED',
    '101' : 'ERROR_STOPPED',
    '102' : 'ERROR_DOOR_OPEN',
    '103' : 'ERROR_MIN_TEMP',
    '104' : 'ERROR_MAX_TEMP',
    '105' : 'ERROR_MAX_BED_TEMP',
    '106' : 'ERROR_X_MAX_ENDSTOP',
    '107' : 'ERROR_X_MIN_ENDSTOP',
    '108' : 'ERROR_Y_MAX_ENDSTOP',
    '109' : 'ERROR_Y_MIN_ENDSTOP',
    '110' : 'ERROR_IDLE_SAFETY',
    #error codes for FABUI configurable functionalities
    '120' : 'ERROR_Y_BOTH_TRIGGERED',
    '121' : 'ERROR_Z_BOTH_TRIGGERED'
}

class GCodeService:
    __metaclass__ = Singleton
    
    IDLE        = 0
    EXECUTING   = 1
    FILE        = 2
    PAUSED      = 3
    
    WRITE_TERM   = b'\r\n'
    READ_TERM    = b'\n'
    ENCODING = 'ascii'
    UNICODE_HANDLING = 'replace'
    
    REPLY_QUEUE_SIZE = 8
    
    def __init__(self, serial_port = UART_PORT_NAME, serial_baud = UART_BAUD_RATE):
        self.running = True
        
        # Serial
        self.serial = serial.serial_for_url(
                                serial_port,
                                baudrate = serial_baud,
                                timeout = 5
                                )
        self.serial.flushInput()
        self.buffer = bytearray()
        
        # Inter-thread communication
        # Must be defined before any thread is created
        self.cq = queue.Queue() # Command Queue
        self.rq = queue.Queue(self.REPLY_QUEUE_SIZE) # Reply Queue
        self.active_cmd = None
        self.wait_for_cmd = None
        self.ev_tx_started = Event()
        self.ev_tx_stopped = Event()
        self.ev_rx_started = Event()
        self.ev_rx_stopped = Event()
        
        # Callback handler
        self.callback = None
    
    """ Internal *private* functions """
    
    def __file_done_thread(self, last_command):
        """
        To ensure that the callback function cannot block sender/receiver threads
        calling it must be done from a separate thread.
        """
        print "waiting for last_command", last_command
        last_command.ev.wait()
        
        self.state = GCodeService.IDLE
        
        #~ if 'file_done' in self.callbacks:
            #~ self.callbacks['file_done']()
        if self.callback:
            self.callback('file_done', None)
                        
    def __sender_thread(self):
        """
        Sender thread used to send commands to Totumduino.
        """
        print "sender thread: started"
        
        self.state = GCodeService.IDLE
        
        self.ev_tx_started.set()
        
        while self.running:
            cmd = self.cq.get()

            if cmd == Command.GCODE:
                self.serial.write(cmd.data + '\r\n')
                #print "@ >>", cmd.data
                self.rq.put(cmd)
            elif cmd == Command.FILE:
                filename = cmd.data
                last_command = None
                aborted = False
                
                self.state = GCodeService.FILE
                
                #with open(filename, 'r+') as file:
                
                # TODO: try except protection
                
                gfile = GCodeFile(filename)
                
                for line, attrs in gfile:
                    line = line.rstrip()
                    print "L >> ", line
                    # TODO: process comments
                    
                    if line:
                        
                        # QUESTION: should this be handled or not?
                        if line == 'M25':
                            self.pause()
                        elif line == 'M24':
                            self.resume()
                        else:
                            self.serial.write(line + '\r\n')
                            last_command = Command.gcode(line, 'ok')
                            self.rq.put(last_command)
                        
                        try:
                            cmd = self.cq.get_nowait()
                            
                            if cmd == Command.GCODE:
                                self.serial.write(cmd.data + '\r\n')
                                #print "# >>", cmd.data
                                self.rq.put(cmd)
                            elif cmd == Command.PAUSE:
                                self.state = GCodeService.PAUSED
                                
                                while self.running:
                                    cmd = self.cq.get()
                                    if cmd == Command.GCODE:
                                        self.serial.write(cmd.data + '\r\n')
                                        self.rq.put(cmd)
                                    elif cmd == Command.RESUME:
                                        self.state = GCodeService.FILE
                                        break
                                    elif cmd == Command.ABORT or cmd == Command.KILL:
                                        break
                                
                                # This is not a mistake. Once ABORT or KILL is received
                                # during PAUSE it will exit that loop and the
                                # command will be processed.
                                if cmd == Command.ABORT or cmd == Command.KILL:
                                    aborted = True
                                    break
                                
                            elif cmd == Command.ABORT or cmd == Command.KILL:
                                aborted = True
                                break
                                
                        except queue.Empty as e:
                            cmd = Command.NONE
                            continue
                
                # Create a new thread that is waiting for the last command 
                # to get it's reply and call the callback function if one
                # was specified.
                callback_thread = Thread( 
                        target = self.__file_done_thread, 
                        args=( [last_command] ) 
                        )
                callback_thread.start()
                
            elif cmd == Command.KILL:
                break
                
        self.ev_tx_stopped.set()
        print "sender thread: stopped"
    
    def __handle_line(self, line_raw):
        """
        Process a one line of reply message.
        """
        try:
            # The received packet is a bytearray so it has to be converted to a
            # string type according to selected ENCODING
            line = line_raw.decode(self.ENCODING, self.UNICODE_HANDLING)
        except Exception as e:
            print e
            return
        
        print "@ <<", line
        
        if not line:
            return
        
        # If there is no active command try to get it from the reply queue
        if not self.active_cmd:
            try:
                self.active_cmd = self.rq.get()
                #print 'active-cmd:', self.active_cmd
            except queue.Empty as e:
                print e
        
        if self.active_cmd:
            # Get the active command as this is the on waiting for the reply.
            cmd = self.active_cmd
            cmd.reply.append( line )
            
            # TODO: handle 'Resend' and/or errors
            # If this line contains the expected reply consider that the complete
            # reply is received and notify the sender of this.
            if cmd.hasExpectedReply(line):
                
                if cmd.reply[0][:5] == 'ERROR':
                    #print "Fuck, error", cmd, cmd.reply
                    msg,error_no = cmd.reply[0].split(':')
                    
                    error_no = error_no.strip()
                    
                    if error_no in ERROR_CODES:
                        print ERROR_CODES[error_no]
                    else:
                        print 'unknown error: [', cmd.reply[0], ']'
                    
                    cmd.reply = []
                    return
                    
                cmd.notify()
                self.active_cmd = None
                
                #print cmd, cmd.reply
                    
    
    def __receiver_thread(self):
        """
        Thread handling incoming serial data.
        """
        print "receiver thread: started"
        
        if not hasattr(self.serial, 'cancel_read'):
            self.serial.timeout = 1
            print "has not cancel_read"
        
        self.ev_rx_started.set()
        
        while (self.running and self.serial.is_open) or self.wait_for_reply:
            
            try:
                # read all that is there or wait for one byte (blocking)
                data = self.serial.read(self.serial.in_waiting or 1)
            except serial.SerialException as e:
                # probably some I/O problem such as disconnected USB serial
                # adapters -> exit
                error = e
                print e
                break
            else:
                if data:
                    self.buffer.extend(data)
                    while self.READ_TERM in self.buffer:
                        line_raw, self.buffer = self.buffer.split(self.READ_TERM, 1)
                        self.__handle_line(line_raw)
                        if self.rq.empty():
                            self.wait_for_reply = False
                            break

        
        self.ev_rx_stopped.set()
        print "receiver thread: stopped"
    
    """ APIs *public* functions """
    
    def start(self):
        """
        Start GCodeService threads.
        """
        # Sender Thread
        self.sender = Thread( target = self.__sender_thread )
        self.sender.start()
        # Receiver Thread
        self.receiver = Thread( target = self.__receiver_thread )
        self.receiver.start()
        
        # Wait for both threads to start before continuing
        self.ev_tx_started.wait()
        self.ev_rx_started.wait()
    
    def loop(self):
        """
        Wait until all threads are closed.
        """
        self.sender.join()
        self.receiver.join()
        
    def stop(self, wait_for_reply = False):
        """
        Stop the service by stopping all running threads.
        """
        self.wait_for_reply = wait_for_reply
        self.running = False
        if hasattr(self.serial, 'cancel_read'):
            self.cancel_read()
        self.cq.put( Command.kill() )
        
        # Wait for both threads to be stopped and then clean up the queues.
        self.sender.join()
        self.receiver.join()
        
        # stop() is called from another thread of execution so try to suspend it
        # to allow the thread system to switch to other running threads
        time.sleep(1)
        
        # Release all threads waiting for a reply (from reply queue)
        while not self.rq.empty:
            print "reply queue is not empty"
            try:
                cmd = self.rq.get_nowait()
                cmd.notify()
                print "notifing ", cmd
            except queue.Empty as e:
                print "reply queue is empty, exiting..."
                break
        
        # Release all threads waiting for a reply (from command queue)
        while not self.cq.empty:
            print "command queue is not empty"
            try:
                cmd = self.cq.get_nowait()
                cmd.notify()
                print "notifing ", cmd
            except queue.Empty as e:
                print "command queue is empty, exiting..."
                break
        
        print "All threads stopped"       
    
    def pause(self):
        """
        Pause current file push. In case no file is being pushed this command
        has no effect.
        """
        self.cq.put( Command.pause() )
        
    def resume(self):
        """
        Resume current file push. In case no file is being pushed this command
        has no effect.
        """
        self.cq.put( Command.resume() )
        
    def abort(self):
        """
        Abort current file push. In case no file is being pushed this command
        has no effect.
        """
        self.cq.put( Command.abort() )
    
    def register_callback(self, callback_name, callback_fun):
        """
        Callbacks: update, file_done, paused, resumed
        """
        #self.callbacks[callback_name] = callback_fun
        self.callback = callback_fun
    
    def send(self, code, expected_reply = 'ok', block = True):
        """
        Send GCode and return reply.
        """
        code = code.encode('latin-1')
        expected_reply = expected_reply.encode('latin-1')
        if self.running:
            
            # QUESTION: should this be handled or not?
            if code == 'M25':
                self.pause()
                return None
            elif code == 'M24':
                self.resume()
                return None
            
            cmd = Command.gcode(code, expected_reply)
            self.cq.put(cmd)
            
            # Don't block, return immediately 
            if not block:
                return None
            
            # Protection #1 in case the service is stopped
            if not self.running:
                return None
            # Last resort protection #2 if service is stopped
            # As this function is called from a separate thread from 'sender'
            # and 'receiver' it can be active after they have been terminated.
            # In which case no one will trigger cmd.ev event to unlock it.
            # Timeout is a safety measure to handle this corner case.
            while not cmd.ev.wait(3):
                if not self.running and not self.wait_for_reply:
                    # Aborting because the service has been stopped
                    print 'Aborting reply.'
                    return None
            return cmd.reply
        else:
            return None
        
    def send_file(self, filename):
        """
        Send GCode from a file.
        """
        if self.running:
            cmd = Command.file(filename)
            self.cq.put(cmd)

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
import re
from threading import Event, Thread
try:
    import queue
except ImportError:
    import Queue as queue
    
# Import external modules
import serial

# Import internal modules
from fabtotum.utils.singleton import Singleton
from fabtotum.utils.gcodefile import GCodeFile
from fabtotum.totumduino.hooks import action_hook
from fabtotum.totumduino.hardware import reset as totumduino_reset
from fabtotum.totumduino.hardware import startup as totumduino_startup

#############################################

ERROR_CODES = {
    #error codes
    '0' : 'NO_ERROR',
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

HOOKS = [
    action_hook
]

class Command(object):
    
    """
    Command objects store individual commands sent to the ``GCodeService``. Along with the 
    command id they contain all the necesary data to execute and handle it.
    
    
    :param id: Command id can be ``NONE``, ``GCODE``, ``FILE``, ``ABORT``, ``PAUSE``, ``RESUME``, ``ZMODIFY`` and ``RESET``
    :param data: Any command data
    :param expected_reply: Expected command reply
    :param group: Aknowledge group. ``GCODE`` commands use `'gcode'` and ``FILE`` uses `'file'`
    :type data: any
    :type expected_reply: string
    :type group: string
    """    
    NONE    = 'none'
    GCODE   = 'gcode'
    FILE    = 'file'
    ABORT   = 'abort'
    PAUSE   = 'pause'
    RESUME  = 'resume'
    ZMODIFY = 'zmodify'
    KILL    = 'kill'
    RESET   = 'reset'
    
    def __init__(self, id, data = None, expected_reply = 'ok', group = 'raw'):
        self.id = id
        self.data = data
        self.reply = []
        self.__ev = Event()
        self.expected_reply = expected_reply
        self.group = group

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
        """
        Notify the waiting thread that the reply has been received.
        """
        self.__ev.set()
        
    def wait(self, timeout = None):
        """
        Wait for until a reply to this command is receiver or timeout expires.
        
        :param timeout: Time in seconds to wait until returning. If this parameter is omitted no timeout will be used.
        :type timeout: float, None
        """
        return self.__ev.wait(timeout)
    
    def isGroup(self, group):
        """
        """
        return self.group == group
    
    def hasExpectedReply(self, line):
        """
        Check whether **line** contains expected reply.
        
        :param line: Line to be checked
        :type line: string
        :returns:   ``True`` if **line** contains the expected reply, ``False`` otherwise
        :rtype: bool
        """
        return line[:len(self.expected_reply)] == self.expected_reply;
        
    def hasError(self, line):
        """
        Check whether a **line** contains an error.
        
        :param line: Line to be checked
        :type line: string
        :returns:   ``True`` if **line** contains an error, ``False`` otherwise
        :rtype: bool
        """
        return line[:5] == 'ERROR';
    
    @classmethod
    def reset(cls):
        """ Constructor for ``RESET`` command. """
        return cls(Command.RESET, None)
        
    @classmethod
    def abort(cls):
        """ Constructor for ``ABORT`` command. """
        return cls(Command.ABORT, None)

    @classmethod
    def kill(cls):
        """ Constructor for ``KILL`` command. """
        return cls(Command.KILL, None)

    @classmethod
    def pause(cls):
        """ Constructor for ``PAUSE`` command. """
        return cls(Command.PAUSE, None)

    @classmethod
    def resume(cls):
        """ Constructor for ``RESUME`` command. """
        return cls(Command.RESUME, None)

    @classmethod
    def gcode(cls, code, expected_reply = 'ok', group = 'gcode'):
        """
        Constructor for ``GCODE`` command.
        
        :param code: GCode
        :param expected_reply: Expected reply
        :param group: Acknowledge group. **Used internally**
        :type code: string
        :type expected_reply: string
        :type group: string
        """
        return cls(Command.GCODE, code, expected_reply, group)

    @classmethod
    def zmodify(cls, z):
        """
        Constructor for ``ZMODIFY`` command.
        
        :param z: Amount by which to modify z axis.
        :type z: float
        """
        return cls(Command.ZPLUS, z)

    @classmethod
    def file(cls, filename):
        """
        Constructor for ``FILE`` command.
        
        :param filename: Filename of file to be pushed.
        :type filename: string
        """
        return cls(Command.FILE, filename, 'file')


class GCodeService:
    """This class docstring shows how to use sphinx and rst syntax

    The first line is brief explanation, which may be completed with 
    a longer one. For instance to discuss about its methods. The only
    method here is :func:`function1`'s. The main idea is to document
    the class and methods's arguments with 

    - **parameters**, **types**, **return** and **return types**::

          :param arg1: description
          :param arg2: description
          :type arg1: type description
          :type arg1: type description
          :return: return description
          :rtype: the return type description

    - and to provide sections such as **Example** using the double commas syntax::

          :Example:

          followed by a blank line !

      which appears as follow:

      :Example:

      followed by a blank line

    - Finally special sections such as **See Also**, **Warnings**, **Notes**
      use the sphinx syntax (*paragraph directives*)::

          .. seealso:: blabla
          .. warnings also:: blabla
          .. note:: blabla
          .. todo:: blabla

    .. note::
        There are many other Info fields but they may be redundant:
            * param, parameter, arg, argument, key, keyword: Description of a
              parameter.
            * type: Type of a parameter.
            * raises, raise, except, exception: That (and when) a specific
              exception is raised.
            * var, ivar, cvar: Description of a variable.
            * returns, return: Description of the return value.
            * rtype: Return type.

    .. note::
        There are many other directives such as versionadded, versionchanged,
        rubric, centered, ... See the sphinx documentation for more details.

    Here below is the results of the :func:`function1` docstring.

    """
    
    __metaclass__ = Singleton
    
    IDLE        = 0
    EXECUTING   = 1
    FILE        = 2
    PAUSED      = 3
    
    WRITE_TERM   = b'\r\n'
    READ_TERM    = b'\n'
    ENCODING = 'utf-8'
    UNICODE_HANDLING = 'replace'
    
    REPLY_QUEUE_SIZE = 1
        
    def __init__(self, serial_port, serial_baud, serial_timeout = 5, use_checksum = False):
        self.running = False
        self.is_resetting = False
        self.SERIAL_PORT = serial_port
        self.SERIAL_BAUD = serial_baud
        self.SERIAL_TIMEOUT = serial_timeout
        
        # Serial
        self.serial = serial.serial_for_url(
                                serial_port,
                                baudrate = serial_baud,
                                timeout = serial_timeout
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
        self.ev_rx_started = Event()
        
        self.file_time_started = None
        self.file_time_finished = None
        self.idle_time_started = time.time()
        self.progress = 0.0
        self.current_line_number = 0
        self.total_line_number = 0
        
        # Note: experimental feature
        self.use_checksum = use_checksum
        self.line_number = 0
        
        self.group_ack = {'gcode' : 0, 'file' : 0, 'gmacro' : 0}
        self.atomic_group = None
        
        # Callback handler
        self.callback = None
    
    """ Internal *private* functions """
    
    def __file_done_thread(self, last_command):
        """
        To ensure that the callback function cannot block sender/receiver threads
        calling it must be done from a separate thread.
        """
        print "waiting for last_command", last_command
        last_command.wait()
        
        self.progress = 100.0
        
        self.state = GCodeService.IDLE
        
        if self.callback:
            self.callback('file_done', None)
            
        self.progress = 0.0
    
    def __trigger_file_done(self, last_command):
        callback_thread = Thread( 
                target = self.__file_done_thread, 
                args=( [last_command] ) 
                )
        callback_thread.start()
        
    def __callback_thread(self, callback_name, data):
        if self.callback:
            self.callback(callback_name, data)
        
    def __trigger_callback(self, callback_name, data):
        print "trigger_callback", callback_name, data
        callback_thread = Thread( 
                target = self.__callback_thread, 
                args=( [callback_name, data] ) 
                )
        callback_thread.start()
    
    def __send_gcode_command(self, code, group = 'gcode'):
        """
        Internal gcode send function with command processing hooks
        """
        if isinstance(code, str):
            gcode_raw = code
            gcode_command = Command.gcode(gcode_raw, group=group)
        elif isinstance(code, Command):
            gcode_raw = code.data + '\r\n'
            gcode_command = code
        else:
            print "Unknown command"
            raise AttributeError
        
        for hook in HOOKS:
            trigger, callback_name, callback_data = hook.process_command(gcode_raw)
            if trigger:
                self.__trigger_callback(callback_name, callback_data)
        
        # Note: experimental feature
        if self.use_checksum:
            data = gcode_raw[:-2]
            self.line_number += 1
            new_code = "N{0} {1}".format(self.line_number, data)
            
            checksum = 0
            
            for c in new_code:
                checksum = int(checksum) ^ ord(c)
            checksum = checksum & 0xff
            
            # Modify original command
            gcode_complete = "{0}*{1}\r\n".format(new_code, checksum)
        else:
            gcode_complete = gcode_raw
        
        print "<< ", gcode_complete[:-2]
        
        #~ self.rq.put(gcode_command)
        self.serial.write(gcode_complete)
        self.rq.put(gcode_command)
        
        return gcode_command

    def __sender_thread(self):
        """
        Sender thread used to send commands to Totumduino.
        """
        print "sender thread: started"
        
        self.state = GCodeService.IDLE
        
        self.ev_tx_started.set()
        
        while (self.running and self.serial.is_open):
            cmd = self.cq.get()

            if cmd == Command.GCODE:
                self.__send_gcode_command(cmd)
                #print "G <<", cmd.data
                
            elif cmd == Command.FILE:
                filename = cmd.data
                last_command = None
                aborted = False
                first_move = False
                
                self.state = GCodeService.FILE
                self.progress = 0.0
                # TODO: try except protection
                
                gfile = GCodeFile(filename)
                
                self.total_line_number = gfile.info['line_count']
                self.current_line_number = 0
                
                gcode_count = self.total_line_number = gfile.info['gcode_count']
                
                self.group_ack['file'] = 0
                
                for line, attrs in gfile:
                    line = line.rstrip()
                    #print "L << ", line
                    
                    if attrs:
                        self.__trigger_callback('process_comment', attrs)
                    
                    if not first_move:
                        if line[:2] == 'G0' or line[:2] == 'G1':
                            self.__trigger_callback('first_move', None)
                            first_move = True
                    
                    self.current_line_number += 1
                    
                    #~ self.progress = 100 * float(self.current_line_number) / float(self.total_line_number)
                    self.progress = 100 * float(self.group_ack['file']) / float(gcode_count)
                    
                    if line:
                        # QUESTION: should this be handled or not?
                        #~ if line == 'M25':
                            #~ self.pause()
                        #~ elif line == 'M24':
                            #~ self.resume()
                        #~ else:
                        
                        last_command = self.__send_gcode_command(line + '\r\n', group='file')
                        
                        # Wait until reply received M109 M190 G28 
                        if ( line[:4] == 'M109' or
                             line[:4] == 'M190' or
                             line[:3] == 'G28'):
                            """ Wait for reply before continuing """
                            last_command.wait()
                        
                        try:
                            cmd = self.cq.get_nowait()
                            
                            if cmd == Command.GCODE:
                                #~ self.serial.write(cmd.data + '\r\n')
                                #~ #print "# >>", cmd.data
                                #~ self.rq.put(cmd)
                                
                                self.__send_gcode_command(cmd)
                                
                            elif cmd == Command.PAUSE:
                                self.state = GCodeService.PAUSED
                                
                                self.__trigger_callback('state_change', 'paused')
                                
                                while self.running:
                                    cmd = self.cq.get()
                                    if cmd == Command.GCODE:
                                        self.serial.write(cmd.data + '\r\n')
                                        self.rq.put(cmd)
                                    elif cmd == Command.RESUME:
                                        self.state = GCodeService.FILE
                                        self.__trigger_callback('state_change', 'resumed')
                                        break
                                    elif cmd == Command.ABORT or cmd == Command.KILL:
                                        break
                                
                                # This is not a mistake. Once ABORT or KILL is received
                                # during PAUSE it will exit that loop and the
                                # command will be processed.
                                if cmd == Command.ABORT or cmd == Command.KILL:
                                    self.__trigger_callback('state_change', 'aborted')
                                    aborted = True
                                    break
                                
                            elif cmd == Command.ABORT or cmd == Command.KILL:
                                self.__trigger_callback('state_change', 'aborted')
                                aborted = True
                                break
                                
                        except queue.Empty as e:
                            cmd = Command.NONE
                            continue
                
                # Create a new thread that is waiting for the last command 
                # to get it's reply and call the callback function if one
                # was specified.
                self.__trigger_file_done(last_command)
                
            elif cmd == Command.KILL:
                break
                
        print "sender thread: stopped"
    
    def __handle_line(self, line_raw):
        """
        Process a one line of reply message.
        """
        
        print "__handle_line", line_raw, "[", self.active_cmd, self.rq.qsize(),  "]"
        
        if self.is_resetting:
            return
        
        try:
            # The received packet is a bytearray so it has to be converted to a
            # string type according to selected ENCODING
            line = line_raw.decode(self.ENCODING, self.UNICODE_HANDLING)
        except Exception as e:
            print e
            return
        
        #print "__handle_line: decoded"
        
        if not line:
            #print "__handle_line: return line_empty"
            return
            
        # Update idle time start
        self.idle_time_started = time.time()
        
        #print "__handle_line: get reply from queue"
        
        # If there is no active command try to get it from the reply queue
        if not self.active_cmd:
            try:
                if self.rq.qsize() > 0:
                    #print "there is something, block until I get it."
                    self.active_cmd = self.rq.get()
                    #print "ok, I got it:", self.active_cmd
                else:
                    #print "there might be something, let's try."
                    self.active_cmd = self.rq.get_nowait()
            except queue.Empty as e:
                #print "Reply queue is EMPTY, ignoring received reply."
                print ">>", line
                return
         
        print "@ >>", line, self.active_cmd
        
        if self.active_cmd:
            # Get the active command as this is the on waiting for the reply.
            cmd = self.active_cmd
            cmd.reply.append( line )

            if cmd.hasExpectedReply(line):
                
                
                #~ if cmd.reply[0][:5] == 'ERROR' and cmd.data[:4] != 'M730':
                    #~ msg,error_no = cmd.reply[0].split(':')
                    #~ error_no = error_no.strip()
                    #~ error_msg = 'UNKNOWN_ERROR: ' + str(cmd.reply[0])
                    
                    #~ if error_no in ERROR_CODES:
                        #~ error_msg = ERROR_CODES[error_no]
                    #~ self.__trigger_callback('error', [error_no, error_msg] )
                                        
                    #~ print error_msg
                    #~ cmd.reply = []
                    
                # TODO: should a command be resent?
                if len(cmd.reply) > 1:
                    if cmd.reply[-2].startswith("Resend:") and cmd.data[:4]: # Second to last line of reply
                        
                        resend, line_no = cmd.reply[-2].split(':')
                        
                        self.line_number = int(line_no) -1
                        
                        #print "Communication error. Need to resend command [{0}]".format(cmd.data)
                        print cmd.reply
                        
                        if cmd.data[:4] != 'M999' and cmd.data[:4] != 'M998':
                            cmd.reply = None
                        
                print "Notify:", cmd
                cmd.notify()
                
                group = self.active_cmd.group
                if group:
                    count = 1
                    if group in self.group_ack:
                        count = self.group_ack[group]

                    count += 1
                        
                    self.group_ack[group] = count
                    
                    #print "group_ack", group, count
                
                self.active_cmd = None
                
            # Line does not contain expected reply
            else:
                
                if cmd.data[:4] == 'M109': # Extruder
                    # T:27.4 E:0 W:?
                    #print "=== M109 [{0}]".format(line)
                    temps = line.split()
                    T = temps[0].replace("T:","").strip()
                    
                    #~ match = re.search('T:(?P<T>[0-9.]+)\sE:(?P<E>[0-9.]+)\sB:(?P<B>[0-9.]+)\s', line)
                    #~ print match
                    #~ if match:
                        #~ T = match.group('T')
                        #~ B = match.group('B')
                    #print "self.__trigger_callback('temp_change:ext', [{0}])".format(T)
                    self.__trigger_callback('temp_change:ext', [T])
                        
                        
                elif cmd.data[:4] == 'M190': # Bed
                    # @ >> T:27.38 E:0 B:54.9
                    #print "=== M190 [{0}]".format(line)
                    
                    temps = line.split()
                    T = temps[0].replace("T:","").strip()
                    B = temps[2].replace("B:","").strip()
                    #~ match = re.search('T:(?P<T>[0-9.]+)\sE:(?P<E>[0-9.]+)\sW:(?P<W>[0-9.?]+)', line)
                    #~ print match
                    #~ if match:
                        #~ T = match.group('T')
                    self.__trigger_callback('temp_change:all', [T,B])
    
        #print "__handle_line: return"
    
    def __receiver_thread(self):
        """
        Thread handling incoming serial data.
        """
        print "receiver thread: started"
        
        if not hasattr(self.serial, 'cancel_read'):
            self.serial.timeout = 1
            print "has no cancel_read"
        
        self.ev_rx_started.set()

        # Run this thread while the service is active        
        while self.running and self.serial.is_open:
            
            #while self.serial.is_open:
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
                    #print 'R: [', data, ']'
                    while self.READ_TERM in self.buffer:
                        line_raw, self.buffer = self.buffer.split(self.READ_TERM, 1)
                        self.__handle_line(line_raw)
        
        print "receiver thread: stopped"
    
    def __reset_totumduino(self):
        """ Does a hardware reset of the totumduino board. """
        
        self.is_resetting = True
        
        self.__cleanup()
        
        #self.serial.close()
        
        totumduino_reset()
        time.sleep(1)
        #self.serial.open()
        
        self.__cleanup()
    
        self.is_resetting = False
        
        time.sleep(1)
        totumduino_startup(self)
    
    def __cleanup(self):
        """
        Internal function cleaning up queues and serial communication.
        """
        self.serial.flush()
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        
        if self.active_cmd:
            self.active_cmd.reply = None
            self.active_cmd.notify()
            self.active_cmd = None
        
        # Release all threads waiting for a reply (from reply queue)
        while not self.rq.empty:
            print "reply queue is not empty"
            try:
                cmd = self.rq.get_nowait()
                cmd.notify()
                #print "notifing ", cmd
            except queue.Empty as e:
                break
        
        # Release all threads waiting for a reply (from command queue)
        while not self.cq.empty:
            print "command queue is not empty"
            try:
                cmd = self.cq.get_nowait()
                cmd.notify()
                #print "notifing ", cmd
            except queue.Empty as e:
                break
                

        
    
    """ APIs *public* functions """
    
    def start(self):
        """
        Start GCodeService threads.
        """
        
        self.running = True
        
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
        
        self.__cleanup()
        
        self.serial.close()
        
        print "All threads stopped"       
    
    def reset(self):
        """
        Force Totumduino hardware reset.
        """
        self.__reset_totumduino()
    
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
    
    def z_modify(self, z):
        """
        Modify the Z axis by amount z
        """
        self.cq.put( Command.zplus(z) )
    
    def register_callback(self, callback_name, callback_fun):
        """
        Callbacks: update, file_done, paused, resumed
        """
        #self.callbacks[callback_name] = callback_fun
        self.callback = callback_fun
        
    def unregister_callback(self):
        """
        Unregister previously registered callback function.
        """
        self.callback = None
    
    def set_atomic_group(self, group):
        """
        Set which group of commands are part of an atomic block.
        
        :param group:
        :tyoe group: string
        """
        self.atomic_group = group
    
    def atomic_begin(self, timeout = None):
        """
        Initiate an atomic block lock. Wait if an atomic operation is already
        in progress.
        Once the atomic lock is aquired and timeout is given. The atomic lock will 
        be released automatically if there is not new command or reply withing
        timeout period.
        
        :param timeout: Maximal allowed time of inactivity before atomic lock is automatically released. 
        :type timeout: float
        """
        pass
        
    def atomic_end(self):
        """
        Atomic block end. With this command the atomic lock is released.
        """
        pass
    
    def send(self, code, block = True, timeout = None):
        """
        Send GCode and return reply.
        """
        code = code.encode('latin-1')
        if self.running:
            sent_timestamp = time.time()
            # QUESTION: should this be handled or not?
            if code == 'M25':
                self.pause()
                return None
            elif code == 'M24':
                self.resume()
                return None
            
            cmd = Command.gcode(code, 'ok')
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
            while not cmd.wait(3):
                if not self.running:
                    # Aborting because the service has been stopped
                    print 'Aborting reply.'
                    return None
                if timeout:
                    if ( time.time() - sent_timestamp ) >= timeout:
                        print 'Timeout for ',code
                        return None                        
            return cmd.reply
        else:
            return None
        
    def send_file(self, filename):
        """
        Send GCode from a file.
        Returns ``False`` if a file is already being pushed.
        
        :rtype: bool
        """
        if self.running:
            if self.state == GCodeService.IDLE:
                cmd = Command.file(filename)
                self.cq.put(cmd)
                return True
                
        return False
            
    def get_progress(self):
        """
        Return current file progress.
        After file_done callback is finished executing, progress will be set to 0.
        """
        return self.progress
        
    def get_idle_time(self):
        """
        Return amount of time that no command was executed from a file.
        """
        return self.idle_time_started - time.time()

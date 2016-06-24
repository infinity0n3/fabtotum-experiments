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
import gettext

# Import external modules


# Import internal modules
from fabtotum.fabui.config              import ConfigService
from fabtotum.totumduino.gcode          import GCodeService
from fabtotum.utils.pyro.gcodeserver    import GCodeServiceServer

cofnig = ConfigService()

# Load configuration
LOCK_FILE           = config.get('general', 'lock')
TRACE               = config.get('general', 'trace')
MACRO_RESPONSE      = config.get('general', 'macro_response')
TASK_MONITOR        = config.get('general', 'task_monitor')
EMERGENCY_FILE      = config.get('general', 'emergency_file')
##################################################################
SOCKET_HOST         = config.get('socket', 'host')
SOCKET_PORT         = config.get('socket', 'port')
##################################################################
HW_DEFAULT_SETTINGS = config.get('hardware', 'default_settings')
HW_CUSTOM_SETTINGS  = config.get('hardware', 'custom_settings')
##################################################################
USB_DISK_FOLDER     = config.get('usb', 'usb_disk_folder')
USB_FILE            = config.get('usb', 'usb_file')
##################################################################
SERIAL_PORT = config.get('serial', 'PORT')
SERIAL_BAUD = config.get('serial', 'BAUD')

# Start gcode service
gcservice = GCodeService(SERIAL_PORT, SERIAL_BAUD)
gcservice.start()

gcserver = GCodeServiceServer(gcservice)



# Wait for all threads to finish
gcserver.loop()
gcservice.loop()

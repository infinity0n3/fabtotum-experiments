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
import ConfigParser

# Import external modules

# Import internal modules
from fabtotum.os.config import INI_FILE, SERIAL_INI
from fabtotum.utils.singleton import Singleton

#####################################################

class ConfigService:
    __metaclass__ = Singleton
    
    def __init__(self):
        """ LOAD INI FILE """
        self.config = ConfigParser.ConfigParser()
        self.config.read(INI_FILE)

        self.serialconfig = ConfigParser.ConfigParser()
        self.serialconfig.read(SERIAL_INI)
        
    def get(self, section, key):
        # TODO: try except protection
        
        value = ''
        
        if section == 'serial':
            value = self.serialconfig.get('serial', key)
        else:
            value = self.config.get(section, key)
        
        return value

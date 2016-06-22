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

# Import internal modules

###############################

#~ class GCodeServiceClient:
    #~ def __getattr__(self, attr):
        #~ print "attr:", attr
        #~ return None

#~ gc = GCodeServiceClient()

#~ print gc.some_attribute

EXTERNALS ={
    'a' : 1,
    'b' : 2
}

for v in EXTERNALS.values():
    print v

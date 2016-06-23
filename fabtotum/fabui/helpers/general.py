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

#zero_all
def home_all(gcs, _trace):
    trace("Now homing all axes")
    macro("G90","ok",2,"set abs position",0,verbose=False)
    
    #macro("G28","ok",100,"homing all axes",1,verbose=False)
    if zprobe_disabled:
        print "Z probe disabled"
        macro("G27 X0 Y0 Z" + str(zmax_home_pos),"ok",100,"Homing all axes",0.1)
        macro("G0 Z50 F10000","ok",15,"raising",0.1, verbose=False)
    else:
        macro("G28","ok",100,"homing all axes",1,verbose=False)

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

# Import internal modules

###############################

#~ class GCodeServiceClient:
    #~ def __getattr__(self, attr):
        #~ print "attr:", attr
        #~ return None

#~ gc = GCodeServiceClient()

#~ print gc.some_attribute

#~ EXTERNALS ={
    #~ 'a' : 1,
    #~ 'b' : 2
#~ }

#~ for v in EXTERNALS.values():
    #~ print v

import re



#~ line = "T:58.05 E:0 B:54.7"
#~ match = re.search('T:(?P<T>[0-9.]+)\sE:(?P<E>[0-9.]+)\sB:(?P<B>[0-9.]+)', line)

#~ print line
#~ if match:
    #~ print match.group('T')
    #~ print match.group('E')
    #~ print match.group('B')

#~ print ''

#~ line = "T:57.7 E:0 W:?"
#~ match = re.search('T:(?P<T>[0-9.]+)\sE:(?P<E>[0-9.]+)\sW:(?P<W>[0-9.?]+)', line)

#~ print line
#~ if match:
    #~ print match.group('T')
    #~ print match.group('E')
    #~ print match.group('W')
    
#~ def tuple():
    #~ return 1,2,3,4
    
#~ line = 'ok T:70.0 /75.0 B:55.1 /55.0 T0:70.0 /70.0 @:13 B@:127'

#~ match = re.search('ok\sT:(?P<T>[0-9]+\.[0-9]+)\s\/(?P<TT>[0-9]+\.[0-9]+)\sB:(?P<B>[0-9]+\.[0-9]+)\s\/(?P<BT>[0-9]+\.[0-9]+)\s', line)
#~ if match:
    #~ print match.group('T'), match.group('TT'), match.group('B'), match.group('BT')
    #~ return float(temperature_match.group(1)) \
        #~ ,  float(temperature_match.group(2)) \
        #~ ,  float(temperature_match.group(3)) \
        #~ ,  float(temperature_match.group(4))

#~ a,b,c,d = tuple()
#~ print a,b,c,d

some_list = []

some_list.append( ('a', 1) )
some_list.append( ('b', 10) )
some_list.append( ('c', 100) )

for tup in some_list:
    print tup
    if tup[0] == 'b':
        some_list.remove(tup)

print some_list

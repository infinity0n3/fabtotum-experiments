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


# Set up message catalog access
tr = gettext.translation('gmacro', 'locale', fallback=True)
_ = tr.ugettext

def home_all(app, args):
    
    zprobe = app.config.get('units', 'zprobe')
    zprobe_disabled = (zprobe['disable'] == 1)
    zmax_home_pos   = float(zprobe['zmax'])
    
    app.trace( _("Now homing all axes") )
    app.macro("G90", "ok", 2, _("Set abs position"), 0, verbose=False)
    
    #macro("G28","ok",100,"homing all axes",1,verbose=False)
    if zprobe_disabled:
        app.macro("G27 X0 Y0 Z" + str(zmax_home_pos),   "ok", 100,  _("Homing all axes"), 0.1)
        app.macro("G0 Z50 F10000",                      "ok", 15,   _("Raising"), 0.1, verbose=False)
    else:
        app.macro("G28",                                "ok", 100,  _("Homing all axes"), 1, verbose=False)

def start_up(app, args):
    
    color = app.config.get('units', 'color')
    
    try:
        safety_door = app.config.get('units', 'safety')['door']
    except KeyError:
        safety_door = 0
    
    try:
        switch = app.config.get('units', 'switch')
    except KeyError:
        switch = 0
    
    try:
        collision_warning = app.config.get('units', 'safety')['collision-warning']
    except KeyError:
        collision_warning = 0
    
    app.trace( _("Starting up") )
    app.macro("M728",                   "ok", 2, _("Alive!"), 1,verbose=False)
    app.macro("M402",                   "ok", 1, _("Probe Up"), 0)
    app.macro("M701 S"+str(color['r']), "ok", 2, _("turning on lights"), 0.1, verbose=False)
    app.macro("M702 S"+str(color['g']), "ok", 2, _("turning on lights"), 0.1, verbose=False)
    app.macro("M703 S"+str(color['b']), "ok", 2, _("turning on lights"), 0.1, verbose=False)
    
    app.macro("M732 S"+str(safety_door),"ok", 2, _("Safety Settings"), 0.1, verbose=False)
    app.macro("M714 S"+str(switch),     "ok", 2, _("Homing direction"), 0.1, verbose=False)
    

    app.macro("M734 S"+str(collision_warning),  "ok", 2, _("Machine Limits Collision warning") ,0.1,verbose=False)

def shutdown(app, args):
    app.trace( _("Shutting down...") ) 
    app.macro("M300",   "ok", 5, _("Play alert sound!"), 1, verbose=False)
    app.macro("M729",   "ok", 2, _("Asleep!"), 1, verbose=False)
    
def raise_bed(app, args):
    """
    For homing procedure before probe calibration and print without homing.
    """
    zprobe = app.config.get('units', 'zprobe')
    zprobe_disabled = (zprobe['disable'] == 1)
    zmax_home_pos   = float(zprobe['zmax'])
    
    app.macro("M402",   "ok", 4,    _("Raising probe"), 0.1, verbose=True)
    app.macro("G90",    "ok", 2,    _("Setting absolute position"), 1)
    
    #macro("G27","ok",100,"Homing all axes",0.1)
    #macro("G0 Z10 F10000","ok",15,"raising",0.1)
    #macro("G28","ok",100,"homing all axes",0.1)
    if zprobe_disabled:
        app.macro("G27 X0 Y0 Z" + str(zmax_home_pos),   "ok", 100,  _("Homing all axes"), 0.1)
        app.macro("G0 Z50 F10000",                      "ok", 15,   _("Raising"), 0.1)
    else:
        app.macro("G27",            "ok", 100,  _("Homing all axes"), 0.1)
        app.macro("G0 Z10 F10000",  "ok", 15,   _("Raising"), 0.1)
        app.macro("G28",            "ok", 100,  _("homing all axes"), 0.1, verbose=False)

def auto_bed_leveling(app, args):
    app.trace( _("Auto Bed leveling Initialized") )
    app.macro("G91",                "ok", 2,    _("Setting relative position"), 1, verbose=False)
    app.macro("G0 Z25 F1000",       "ok", 2,    _("Moving away from the plane"), 1,verbose=False)
    app.macro("G90",                "ok", 2,    _("Setting abs position"), 1, verbose=False)
    app.macro("G28",                "ok", 90,   _("Homing all axis"), 1)
    app.macro("G29",                "ok", 140,  _("Auto bed leveling procedure"), 1)
    app.macro("G0 X5 Y5 Z60 F2000", "ok", 100,  _("Getting to idle position"), 1)

def probe_down(app, args):
    app.macro("M401",   "ok", 1, _("Probe Down"), 0)
    
def probe_up(app, args):
    app.macro("M402",   "ok", 1, _("Probe Up"), 0)

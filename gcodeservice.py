#!/bin/env python
# -*- coding: utf-8; -*-

from fabtotum.utils.pyro.gcodeservice import GCodeServiceServer

gcss = GCodeServiceServer()
gcss.loop()

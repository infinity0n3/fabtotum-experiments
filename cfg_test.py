#!/bin/env python
# -*- coding: utf-8; -*-

# Import internal modules
from fabtotum.fabui.config import ConfigService

cfg = ConfigService()

print cfg.get('serial', 'baud')
print cfg.get('serial', 'port')
print cfg.get('task', 'lock_file')

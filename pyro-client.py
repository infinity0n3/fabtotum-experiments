#!/bin/env python
# -*- coding: utf-8; -*-

# saved as greeting-client.py
import Pyro4

uri = 'PYRO:obj_27aa912bc44f4017b754a5d430b1e12b@localhost:37896' #input("What is the Pyro uri of the greeting object? ").strip()
name = 'Daniel' #input("What is your name? ").strip()

greeting_maker = Pyro4.Proxy(uri)         # get a Pyro proxy to the greeting object
print(greeting_maker.get_fortune(name))   # call method normally

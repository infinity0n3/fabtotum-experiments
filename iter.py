#!/bin/env python

from fabtotum.utils.gcodefile import GCodeFile

class CustomContainer:
    def __init__(self, count):
        self.count = count
        self.iter_count = 0
        
    def __iter__(self):
        print "__iter__"
        return self
        
    def next(self):
        print "next()"
        self.iter_count += 1
        if self.iter_count < self.count:
            return self.iter_count
        else:
            raise StopIteration
        

#~ cont = CustomContainer(5)
#~ for i in cont:
    #~ print i

#~ gcf = GCodeFile('test.gcode')
#~ print gcf.info.attribs

#~ gcf = GCodeFile('slicer.gcode')
#~ print gcf.info.attribs

gcf = GCodeFile('slicer.gcode')


#~ for code in gcf:
    #~ if code:
        #~ print '[' + code + ']'

print gcf.info.attribs

#!python  -u

import sprites


class ScreenObject(object):
    """ Abstract base class representing items that show up on screen """
    def __init__(self, started=False):
        super(ScreenObject, self).__init__()
        self.started = started
        
    def start(self):
        # Start the SO running
        pass

    def update(self, dt, userInput):
        # Called every game-tick when active
        pass        

    def draw(self):
        # Called every draw-tick when active. 
        # Make OpenGL calls here, but leave the stack the way you found it.
        pass        

    def done(self):
        # Returns boolean.
        pass        

    def delete(self):
        # Called after done returns true. 
        # A chance to free up resources (OpenGL stuff?)
        pass        

class SerialObjects(ScreenObject):
    """ Run a series of SO's one after the other"""
    def __init__(self, *objects):
        super(ScreenObject, self).__init__()
        self.objects = objects
        self.iObject = 0
        self.alive = True

    def start(self):
        self.objects[0].start()

    def update(self, dt, userInput):
        if not self.alive:
            #print "this shouldn't happen"
            return

        so = self.objects[self.iObject]
        so.update(dt, userInput)

        if so.done():
            so.delete()
            self.iObject += 1

            if self.iObject < len(self.objects):
                self.objects[self.iObject].start()
            else:
                self.alive = False

    def draw(self, window):
        if not self.alive:
            #print "this shouldn't happen 2"
            return

        self.objects[self.iObject].draw(window)

    def done(self):
        return not self.alive

class ParallelObjects(ScreenObject):
    """ Run a series of objects in parallel.
        Stays alive as long as the longest lived one. """
    def __init__(self, *objects):
        super(ParallelObjects, self).__init__()
        self.objects = objects
        self.alive = True

    def start(self):
        for so in self.objects:
            so.start()

    def update(self, dt, userInput):
        anyLeft = False
        for so in self.objects:
            if not so.done():
                so.update(dt, userInput)
                anyLeft = True

        if not anyLeft:
            self.alive = False

    def draw(self, window):
        for so in self.objects:
            so.start(window)

    def delete(self):
        for so in self.objects:
            so.delete()

class XSO(ScreenObject):
    """docstring for XSO"""
    def __init__(self, props):
        super(XSO, self).__init__()
        self.x = sprites.GameOver(props)

    def update(self, dt, userInput):
        self.x.update(dt)
    def draw(self, window):
        self.x.draw()
    def done(self):
        return self.x.done()

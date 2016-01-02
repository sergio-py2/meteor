#!python  -u

import pyglet
import pyglet.gl as gl

import timevars as tv
import sprites
from config import Config

class ActiveObject(object):
    """ Abstract base class representing items that show up on screen """
    def __init__(self, started=False):
        super(ActiveObject, self).__init__()
        self.started = started
        
    def start(self):
        # Start the SO running
        pass

    def update(self, dt, userInput):
        # Called every game-tick when active
        pass        

    def draw(self, window):
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

class SerialObjects(ActiveObject):
    """ Run a series of AO's one after the other"""
    def __init__(self, *objects):
        super(ActiveObject, self).__init__()
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

        #print "iObject", self.iObject

    def draw(self, window):
        if not self.alive:
            #print "this shouldn't happen 2"
            return

        #print self.objects[self.iObject]

        self.objects[self.iObject].draw(window)

    def done(self):
        return not self.alive

class ParallelObjects(ActiveObject):
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

class XSOXXXX(ActiveObject):
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



class GameOverAO(ActiveObject):
    """docstring for GameOver"""
    def __init__(self, props):
        #super(GameOver, self).__init__()
        self.props = props

        self.display = "GAME OVER"

        self.text = pyglet.text.Label(
            text=self.display, font_name='Orbitron',  bold=True, font_size=108,
            anchor_x = "center", anchor_y="bottom",
            color=(0,255,0, 200),
            #x=props.windowWidth//2,
            #y=200
            x=0,
            y=0
            )

        self.timeAlive = 0
        self.zoom    = tv.PLInterpolator([(0,0.2), (1,0.3), (2,0.5), (3,1.0), (1000,1.0)])
        self.height  = tv.PLInterpolator([(0,150), (2,450), (3,320), (1000,370)])
        self.height.shift(0,props.windowHeight-660)
        self.alive = True


    def update(self, dt, userInput):
        self.timeAlive += dt
        if self.timeAlive > 5.0:
            self.alive = False
        
    def draw(self, window):
        a = self.zoom(self.timeAlive)
        h = self.height(self.timeAlive)

        gl.glPushMatrix()
        gl.glTranslatef(self.props.windowWidth//2, h, 0)
        gl.glScalef(a,a,a)

        self.text.draw()
        
        gl.glPopMatrix()

    def done(self):
        return not self.alive


class DelayAO(ActiveObject):
    def __init__(self, seconds, started=False):
        self.secondsDelay = seconds
        self.secondsRunning = 0.
        self.running = started
        
    def start(self):
        self.running = True

    def update(self, dt, userInput):
        if self.running:
            self.secondsRunning += dt

    def done(self):
        return self.secondsRunning > self.secondsDelay

class MarkerAO(ActiveObject):
    ''' Just an objects that marks when it becomes active'''
    def __init__(self):
        self.isDone = False
        
    def start(self):
        self.isDone = True

    def done(self):
        return self.isDone

class SpriteWrapperAO(ActiveObject):
    # My sprites don't have a well-defined interface so this only works for
    # Multiexplosion  right now.
    def __init__(self, sprite, started=False):
        self.sprite = sprite
        
    def start(self):
        self.sprite.start()

    def update(self, dt, userInput):
        self.sprite.update(dt)

    def draw(self, window):
        self.sprite.draw(window)

    def done(self):
        return self.sprite.done()

class SoundWrapperAO(ActiveObject):
    def __init__(self, sound, started=False):
        self.sound = sound
        self.isDone = False
        
    def start(self):
        if Config.Instance().sound():
            self.sound.play()
        self.isDone = True


    def done(self):
        return self.isDone

class FunctionWrapperAO(ActiveObject):
    """ Just calls a (no-argument) function when started"""
    def __init__(self, fn):
        super(FunctionWrapperAO, self).__init__()
        self.fn = fn
        self.isDone = False
        
    def start(self):
        self.fn()
        self.isDone = True

    def done(self):
        return self.isDone
        
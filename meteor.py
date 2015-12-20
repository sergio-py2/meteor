#!python  -u
#!/c/Python27/python.exe  -u

from __future__ import division

import os
import sys

import pyglet
import pyglet.gl as gl
import pyglet.window.mouse as mouse
import pyglet.window.key as key
import pyglet.font.ttf

import random
import math

import timevars as tv
import vector as vec
from vector import Vector as Vec

import sprites
from sprites import *
from gameassets import GameAssets
import shipsprite
import gamephase
import gameelements

import geoip

gApp = None
gAssets = None
gGeoData = {}

# Objects that just hold a bunch of attributes
class Attributes(object):
    pass

# Define the application class

class Application(object):
    """
    Application maybe with multiple windows. Should be a Singleton.
    Does little for now but it's where communication between / coordination
    of multiple windows would happen.
    """
    def __init__(self, windowOpts):
        super(Application, self).__init__()

        joysticks = pyglet.input.get_joysticks()
        if len(joysticks) > 0:
            js = joysticks[0]
            js.open()
        else:
            js = None

        #windowOpts = {'width': 1200, 'height': 500}
        #windowOpts = {'fullscreen': True}

        self.window = GameWindow(js, **windowOpts)

    def update(self, dt):
        self.window.update(dt)

class WindowProps(object):
    """Properties of a GameWindow, suitable for passing around without
        passing the full window."""
    
    def __init__(self):
        pass

# Game Phases
(
    GP_STARTING,
    GP_PLAYING,
    GP_DYING,
    GP_SHOWSCORE
) = range(1,5)

class GameWindow(pyglet.window.Window):
    """A single window with a game taking place inside it"""
    
    def __init__(self, joystick, **kwargs):
        # These might not do anything here.
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glEnable( gl.GL_BLEND)
        gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        super(GameWindow, self).__init__(**kwargs)        
        
        if not self.fullscreen:
            self.set_location(20,35)

        self.set_vsync(True)
        self.set_mouse_visible(False)

        self.gameTime = 0.0
        self.state = GP_STARTING
        #self.boom = None
        #self.dyingTimer = None
        self.gameOver = None

        props = WindowProps()
        props.windowWidth     = self.width
        props.windowHeight    = self.height
        self.props = props

        #self.gameElements = GameElements(props)
        #self.gameElements.populateGame( gAssets )

        ge = gameelements.GameElements(props)
        ge.populateGame( gAssets )

        self.userInput = Attributes()

        self.userInput.joystick = joystick
        self.userInput.keys = key.KeyStateHandler()
        self.push_handlers(self.userInput.keys)

        self.gamePhase = gamephase.PlayPhase( ge, props, self )
        #self.gamePhase = gamephase.LeaderBoardPhase( props, self, (1,2,3) )
        #s = random.randint(5,500)
        #self.gamePhase = gamephase.LeaderBoardPhase(props, self, (None, 'MA', s))


        # I think extending Window automatically has this as a handler
        #self.push_handlers(self.on_key_press)

    def on_key_pressXXX(self, symbol, modifiers):
        pass
        #print "GameWindow.on_key_press", symbol
        #if self.keys[key.Q]:
            #print "State is %s" % gGeoData.get('state', 'unknown')
        #    pyglet.app.exit()        
    

    # --------------------------------------------
    #     Most of the game logic goes here
    # --------------------------------------------
    def update(self, dt):
        k = self.userInput.keys 
        if k[key.Q] and (k[key.LCTRL] or k[key.RCTRL]):
            #print "State is %s" % gGeoData.get('state', 'unknown')
            #print "Q", self.userInput.keys[key.LCTRL]
            pyglet.app.exit()        

        self.gameTime += dt
        state = self.state
        
        gp = self.gamePhase.update(dt, self.userInput)

        if gp is None:
            return

        # State change
        self.gamePhase.delete()
        gp.start()

        self.gamePhase = gp

            
    def on_draw(self):
        self.gamePhase.draw(self)




def update(dt):
    #print "update", dt

    global gApp
    gApp.update(dt)


def getJoystickPolarLeft(js):
    # Note 1: I assume th will just be jittery around the origin.
    # Note 2: It's possible r will go above 1.0. We can normalize r based
    #         on angle here if we want.

    x,y = js.x, js.y
    r2 = x*x + y*y
    th = math.atan2(y,x) * (180.0/math.pi)

    return math.sqrt(r2), th

def getJoystickPolarRight(js):
    x,y = js.rx, js.ry
    r2 = x*x + y*y
    th = math.atan2(y,x) * (180.0/math.pi)

    return math.sqrt(r2), th



def main():
    global gApp
    global gAssets
    global gGeoData

    #LaserCannon.resetTime = 0.05

    # Launch thread to try to get geoData
    # Theoretically there's a race condition, but it's a one-shot thread
    # so there's not much rish
    worker = geoip.GeoIPFetchThread(gGeoData)
    worker.setDaemon(True)
    worker.start()

    gamephase.gGeoData = gGeoData

    if len(sys.argv) > 1 and sys.argv[1] == '-f':
        windowOpts = {'fullscreen': True}
    else:
        windowOpts = {'width': 1200, 'height': 600}

    for theme in ['user01', 'default']:
        d = 'themes/' + theme + "/"
        pyglet.resource.path += [d+'images', d+'sounds', d+'fonts']

    pyglet.resource.reindex()

    # Create the (few) global objects, and make sure they get set in the modules
    # that need them. (This is such bad programming)
    gAssets = GameAssets()
    gAssets.loadAssets()
    sprites.gAssets = gAssets
    shipsprite.gAssets = gAssets
    gamephase.gAssets = gAssets

    gApp = Application(windowOpts)
    
    # First time a sound is played there is a delay. So 
    # play it now to get it over with. (Causes slight delay. Or maybe not?)
    developing = False
    if not developing:
        player = pyglet.media.Player()
        player.volume = 0
        player.queue(gAssets.getSound('lazer-shot-1'))
        player.queue(gAssets.getSound('bomb-explosion-1'))
        #player.queue(gAssets.getSound('boom2'))
        player.play()


    pyglet.clock.set_fps_limit(60)
    pyglet.clock.schedule_interval(update, 1/60.)

    pyglet.app.run()


if __name__ == '__main__':
    main()


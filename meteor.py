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

import geoip

gApp = None
gAssets = None
gGeoData = {}

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

# GamePlayStates
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

        self.joystick = joystick

        self.gameTime = 0.0
        self.state = GP_STARTING
        self.boom = None
        self.dyingTimer = None
        self.gameOver = None

        props = WindowProps()
        props.windowWidth     = self.width
        props.windowHeight    = self.height
        self.props = props

        self.viewportOrigin = [0.0, 0.0]

        self.gameElements = GameElements(props)
        self.gameElements.populateGame( gAssets )

        self.destinationTracker = tv.TimeAverage2(0.7, *self.gameElements.ship.getPosition())

        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)

        self.shake = None

        # I think extending Window automatically has this as a handler
        #self.push_handlers(self.on_key_press)

    def on_key_press(self, symbol, modifiers):
        #print "GameWindow.on_key_press", symbol
        if self.keys[key.Q]:
            #print "State is %s" % gGeoData.get('state', 'unknown')
            pyglet.app.exit()        
    

    # --------------------------------------------
    #     Most of the game logic goes here
    # --------------------------------------------
    def update(self, dt):
        self.gameTime += dt
        state = self.state

        if state == GP_PLAYING:
            self.updatePlay(dt)

        elif state == GP_STARTING:
            self.state = GP_PLAYING
            self.updatePlay(dt)

        elif state == GP_DYING:
            self.updateDying(dt)

        elif state == GP_SHOWSCORE:
            pass


    def updateDying(self, dt):
        self.gameElements.update(dt)
        self.updateViewport(dt)
        self.dyingTimer.update(dt)

        if self.dyingTimer.done() and self.boom is None:
            p1 = self.gameElements.ship.getPosition()
            self.boom = sprites.MultiExplosion(p1[0], p1[1], [0.0, 0.3, 0.5, 0.6, 1.0])

        if self.boom is not None:
            self.boom.update(dt)

        if self.gameOver is not None:
            self.gameOver.update(dt)

            

    def updatePlay(self, dt):
        g = self.gameElements

        # Elements that evolve pretty much by themselves.
        g.update(dt)

        # Use controls to update the ship.
        if self.joystick is not None:
            self.joystickUpdate(dt)
        else:
            self.keyboardUpdate(dt)

        if self.keys[key.M]:
            print ""
            for i,m  in enumerate(g.swarm.meteors):
                print "Meteor % 2d: %s" %(i,m.dump())

        if self.keys[key.K]:
            self.spaceShipDeath()
            self.gameOver = GameOver(self.props)
            #self.boom = sprites.MultiExplosion(200, 150, [0.1, 0.3, 0.5, 0.6, 1.0])
            #self.boom = sprites.MultiExplosion(200, 150, [0.1, 0.8, 1.2, 1.7, 2.0])


        # Interactions
        # We handle lazer blasts when they are created
        # What else should go here?

        self.updateViewport(dt)
        ship = self.gameElements.ship 

        # Check for hits on space ship
        p1 = Vec(*ship.getPosition())
        r1 = ship.getRadius()

        prevMinD = 1000000 #ifty
        hitObj = None
        severity = 1000.0

        for o in g.swarm.objects():
            p2 = Vec(*o.getCenter())
            r2 = o.getRadius()

            d = vec.Distance(p1, p2)
            if d < r1 + r2 and d < prevMinD:
                #print d, r1, r2
                prevMinD = d
                hitObj = o
                severity = d/(r1+r2)

        if hitObj is not None:
            #print "Hit", severity
            if severity > 0.8:
                #print "graze", severity
                pass
            elif severity > 0.28:
                # Shake
                if self.shake is None:
                    self.shake = tv.Shaker2(0.75, 10.0, 3.0)
                    g.score.addScore([-1]*4)
            else:
                # Explode
                self.spaceShipDeath()

        posn = ship.getPosition()
        g.swarm.spawnNew(posn, self.viewportOrigin)

        g.radar.setNumItems( g.swarm.nItems())



    def spaceShipDeath(self):
        self.shake = tv.Shaker2(0.75, 22.0, 8.0)
        self.gameElements.score.addScore([-2]*8)
        self.state = GP_DYING
        self.dyingTimer = tv.CountDownTimer(0.8)

    def updateViewport(self, dt):
        # Viewport tracks ship, roughly, i.e. it shift when ship gets near an edge.
        #
        # Well, we either need to explicitly trim the projected position so it doesn't
        # shove the ship off the screen, or, acheive the same effect by making the 
        # amount of time we project forward depend on the angle of travel. Why?
        # because drag limits speed, and horizontally, 1.2sec ahead and the ship
        # always fit on the same screen. Travelling vertically, they get too far apart.
        #

        ship = self.gameElements.ship 

        #x,y = ship.getPosition()
        #x,y = ship.getProjectedPosition(0.4)
        vx,vy = ship.getDirection()
        t = 1.3 * abs(vx) + 0.4 * abs(vy)

        x,y = self.destinationTracker.update(*ship.getProjectedPosition(t))

        border = 200
        factor = 0.8

        # Shift the viewport
        xRel = x - self.viewportOrigin[0]
        if xRel > self.width - border:
            self.viewportOrigin[0] += factor * (xRel - self.width + border)
        elif xRel < border:
            self.viewportOrigin[0] -= factor * (border - xRel)

        yRel = y - self.viewportOrigin[1]
        if yRel > self.height - border:
            self.viewportOrigin[1] += factor * (yRel - self.height + border)
        elif yRel < border:
            self.viewportOrigin[1] -= factor * (border - yRel)

        if self.shake is not None:
            self.shake.update(dt)
            (sx,sy) = self.shake.getValue()
            self.viewportOrigin[0] += sx
            self.viewportOrigin[1] += sy

            if not self.shake.alive:
                self.shake = None


    def joystickUpdate(self, dt):
        js = self.joystick
        g = self.gameElements

        g.dbgSquare1.shift(3*js.rx, -3*js.ry)
        #g.dbgSquare2.shift(3*js.rx, -3*js.ry)
        g.dbgSquare2.xPos.target = g.dbgSquare1.xPos
        g.dbgSquare2.yPos.target = g.dbgSquare1.yPos

        # Right joystick rotates and uses rear engine
        r, th = getJoystickPolarRight(js)
        if r > 0.1:
            g.ship.angleVar.setTarget(th + 90)
            g.ship.thrust(dt, r)
        else:
            g.ship.thrust(dt, 0)    # needed for drawing flames

        # Left joystick just rotates
        r, th = getJoystickPolarLeft(js)
        if r > 0.45:
            g.ship.angleVar.setTarget(th + 90)
            #g.ship.angle = th + 90.0

        # Front thrust, useful for braking
        # Nope, converted to increasing drag
        if js.buttons[4] :
            g.ship.drag( 1.0 )
            #g.ship.sprite = pyglet.sprite.Sprite(self.assets.dbgImage2)
        else:
            g.ship.drag(0.0)

        if js.buttons[7]:
            # dump a few more meteors in 
            #g.addMeteors(10)
            pass

        #if js.buttons[5]:
        if js.z < -0.15:
            self.shoot()

    def keyboardUpdate(self, dt):
        # Use keyboard to control ship
        g = self.gameElements

        drot = 800
        rot = g.ship.angleVar.value

        thrust = 0
        rotNew = rot

        if self.keys[key.LEFT]:
            rotNew +=  -drot * dt
            #g.ship.angleVar.setTarget(th - drot * dt)
            #g.ship.rot( -drot * dt)

        if self.keys[key.RIGHT]:
            rotNew +=  +drot * dt
            #g.ship.angleVar.setTarget(th + drot * dt)
            #g.ship.rot( drot * dt)
        
        if self.keys[key.UP]:
            thrust += 1.0
            #g.ship.thrust( dt, 1.0)

        # Nope, converted to increasing drag
        if self.keys[key.DOWN]:
            g.ship.drag( 1.0 )
            #g.ship.sprite = pyglet.sprite.Sprite(self.assets.dbgImage2)
        else:
            g.ship.drag(0.0)

        g.ship.thrust( dt, thrust)
        g.ship.angleVar.setTarget(rotNew)

        if self.keys[key.SPACE] :
            self.shoot()

    def shoot(self):
        g = self.gameElements
        shot = g.ship.shoot(g.shotBatch)
        gAssets.getSound('lazer-shot-1').play()

        if shot is not None:
            g.shots.append(shot)

            m = g.swarm.findShotHit(shot)
            
            if m is not None:
                points = m.getValue()
                g.score.addScore(points)
                g.swarm.explode(m)
                gAssets.getSound('bomb-explosion-1').play()

                #m.alive = False
                #g.score.addScore(10)


    def on_draw(self):
        # I really don't know what these are doing, and if there's any difference having them
        # here instead of just once at the top.
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        #gl.glClearColor(0.0, 0.0, 0.08, 1.0)
        gl.glEnable( gl.GL_BLEND)
        #gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        gl.glPushMatrix()

        # GL matrices are applied last-added-first, so this *is* the right
        # order for pushing them.
        gl.glTranslatef(-self.viewportOrigin[0], -self.viewportOrigin[1], 0.0)

        if self.shake is not None:
            # We want to rotate around the center of the current viewport
            # vpc = view port center
            vpc_x = self.viewportOrigin[0] + self.props.windowWidth//2
            vpc_y = self.viewportOrigin[1] + self.props.windowHeight//2
            
            gl.glTranslatef(vpc_x, vpc_y, 0.0)
            gl.glRotatef(self.shake.getAngle(), 0, 0, 1)
            gl.glTranslatef(-vpc_x, -vpc_y, 0.0)


        
        self.clear()
        g = self.gameElements

        # Should I be pushing most of this code into GameElements?

        g.starField.draw()
        g.swarm.draw()
        #g.expl.draw()

        if self.state == GP_PLAYING:
            g.ship.draw()
        elif self.state == GP_DYING and not self.dyingTimer.done():
            g.ship.draw()
        #g.dbgSquare1.draw()
        #g.dbgSquare2.draw()

        if self.state == GP_DYING and self.boom is not None:
            self.boom.draw()

        for shot in g.shots:
            if shot.alive:
                shot.draw()
        
        gl.glPopMatrix()
        g.score.draw()
        g.radar.draw()

        if self.gameOver is not None:
            self.gameOver.draw()


class GameElements(object):
    """Holds all the elements that make up a game"""
    def __init__(self, props):
        super(GameElements, self).__init__()
        self.props = props
        
    def populateGame(self, assets):
        w = self.props.windowWidth
        h = self.props.windowHeight

        self.ship = shipsprite.ShipSprite( x=w//2, y=h//2, w=w, h=h)
        self.score = ScoreBoard(self.props)
        self.radar = MeteorRadar(self.props)

        self.swarm = Swarm(self.props)
        posn = self.ship.getPosition()
        self.swarm.initialMeteors(14, posn)

        self.shots = []
        self.shotBatch = pyglet.graphics.Batch()

        self.starField = StarField(w, h)

        self.dbgSquare1 = DgbSquare(10,10)
        self.dbgSquare2 = DgbSquare2(10,10)


    def update(self, dt):
        self.swarm.update(dt)

        for sh in self.shots:
            sh.update(dt)
            if not sh.alive:
                sh.delete()

        self.shots = [sh for sh in self.shots if sh.alive == True]

        self.ship.update(dt)
        self.score.update(dt)

        #self.dbgSquare1.update(dt)
        #self.dbgSquare2.update(dt)



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

    if len(sys.argv) > 1 and sys.argv[1] == '-f':
        windowOpts = {'fullscreen': True}
    else:
        windowOpts = {'width': 1200, 'height': 600}

    for theme in ['ss', 'default']:
        d = 'themes/' + theme + "/"
        pyglet.resource.path += [d+'images', d+'sounds', d+'fonts']

    pyglet.resource.reindex()

    # Create the (few) global objects, and make sure they get set in the modules
    # that need them. (This is such bad programming)
    gAssets = GameAssets()
    gAssets.loadAssets()
    sprites.gAssets = gAssets
    shipsprite.gAssets = gAssets

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


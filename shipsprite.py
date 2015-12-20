#!python

import random
import math

import pyglet

import vector as vec
import timevars as tv

import sprites
from sprites import ShotSprite
from gameassets import GameAssets

#gAssets = None


class ShipSprite(object):

    
    def __init__(self, *args, **kwargs):
        #super(ShipSprite, self).__init__(self.__class__.image, x=kwargs['x'], y=kwargs['y'])
        ga = GameAssets.Instance()
        x, y = kwargs['x'], kwargs['y']
        self.spriteShip = pyglet.sprite.Sprite(ga.getImage('ship'), x=x, y=y)
        self.spriteFlames = pyglet.sprite.Sprite(ga.getImage('flames'), x=x, y=y)
        self.spriteFlames.opacity = 0
        self.motion = tv.ThrustMotionWithDrag( x, y)
        self.motion.setDrag(0.05)
        self.tipOffset = ga.shipTipAboveCenter

        rotPull = 9000
        rotDrag = 800    
        self.angleVar = tv.AngleTargetTracker(rotPull, rotDrag)
        self.angleVar.initVals(0.0, 0.0)
        self.w = kwargs['w']
        self.h = kwargs['h']

        self.radius = (self.spriteShip.width + self.spriteShip.height)/2./2.

        self.alive = True
        self.laserCannon = LaserCannon()
        self.maxThrustPower = 400
        self.currThrottle = 0.0

    def draw(self):
        self.spriteShip.draw()
        self.spriteFlames.opacity = tv.clamp(0, self.currThrottle * 255, 255)
        self.spriteFlames.draw()


    def rotXXX(self, dtheta):
        self.angle += dtheta

    def thrust(self, dt, throttle):
        # We assume that at self.angle == 0, the forward direction
        # is x = 0, y = +1, and that +ive rotation is clock-wise
        # Throttle is from 0.0 to 1.0 (well, I guess I'm allowing negative tto)
        #ux, uy = vec.uvec(self.angle)
        if throttle != 0.0:
            ux, uy = vec.uvec(self.angleVar.value)
            ds = throttle * self.maxThrustPower * dt
            self.motion.thrust( ds * ux, ds * uy)

        self.currThrottle = throttle

    def drag(self, drag):
        # Increase the drag (input drag should be between 0.0 and 1.0)
        self.motion.setDrag(0.05 + 0.5*drag)

    def update(self, dt):
        self.motion.update(dt)
        #self.motion.wrap(self.w, self.h)
        #self.motion.bounce(self.w, self.h)

        self.laserCannon.update(dt)

        # Update properties used by pyglet.Sprite when drawing
        #self.x, self.y = self.motion.position()
        x, y = self.motion.position()
        self.spriteShip.x, self.spriteShip.y = x, y
        self.spriteFlames.x, self.spriteFlames.y = x, y-3

        self.angleVar.update(dt)
        #self.rotation = self.angle
        #self.rotation = self.angleVar.value
        self.spriteShip.rotation = self.angleVar.value
        self.spriteFlames.rotation = self.spriteShip.rotation

    def getPosition(self):
        return self.motion.position()

    def getRadius(self):
        return self.radius

    def getDirection(self):
        # unit vector indirection of travel
        vx, vy = self.motion.velocity()
        l = math.sqrt(vx*vx + vy*vy)
        if l == 0:
            return (0,0)

        return (vx/l, vy/l)

    def getProjectedPosition(self, sec):
        sx, sy = self.motion.position()
        vx, vy = self.motion.velocity()
        return (sx+sec*vx, sy+sec*vy)


    def getTipParams(self):
        ''' Return postion of tip and forward direction (as angle)'''
        x,y = self.motion.position()
        th = self.angleVar.value
        #fwd = self.angle - 90.0

        ux, uy = vec.uvec(th)
        #tipOffset = gAssets.shipTipAboveCenter
        x,y = x + self.tipOffset*ux, y + self.tipOffset*uy

        return ((x,y), th-90.0)

    def shoot(self, batch):
        # returns either a ShotSprite or None
        if self.laserCannon.shoot():
            tip, fwd = self.getTipParams()
            return ShotSprite(tip, fwd, batch)

            # Cheat a bit
            #dt = 1/30.0
            #nextTip = (tip[0]+dt*self.motion.vx, tip[1]+dt*self.motion.vy)
            #return ShotSprite(nextTip, fwd)            
        else:
            return None


class LaserCannon(object):
    resetTime = 0.05

    def __init__(self):
        super(LaserCannon, self).__init__()
        self.sinceShot = 1000.0

    def update(self, dt):
        self.sinceShot += dt

    def shoot(self):
        if self.sinceShot > self.__class__.resetTime:
            self.sinceShot = 0.0
            return True
        else:
            return False

#!python

import random
import math

import pyglet

import vector as vec
import timevars as tv


gAssets = None

class Swarm(object):
    ''' All the non-player objects (not sure if ShotSprites are included)'''
    def __init__(self, props):
        self.props = props
        self.meteors = []
        self.meteorBatch = pyglet.graphics.Batch()
        self.addMeteors(30)
        #self.expl = ExplosionSprite(200, 350)

        self.explosions = []

        self.gameTime = 0.0

    def objects(self):
        return self.meteors

    def explode(self, meteor):
        meteor.alive = False
        exp = ExplosionSprite(meteor.x, meteor.y)
        self.explosions.append(exp)


    def draw(self):
        self.meteorBatch.draw()

        for exp in self.explosions:
            exp.draw()

    def update(self, dt):
        self.gameTime += dt

        for m in self.meteors:
            m.update(dt)
            if not m.alive:
                m.delete()

        self.meteors = [m for m in self.meteors if m.alive == True]

        for exp in self.explosions:
            exp.update(dt)

        self.explosions = [e for e in self.explosions if e.alive == True]

        #self.expl.update(dt)


    # To Be Obsoleted
    def addMeteors(self, n):
        w = self.props.windowWidth
        h = self.props.windowHeight

        for _ in range(0,n):
            x = w*(3*random.random() - 1)
            y = h*(3*random.random() - 1)
            self.meteors.append(MeteorSprite(x,y,w,h, self.meteorBatch))
        
        #self.score.incrOutOf( 10 * n)

    def findShotHit(self, shot):
        prevNearest = 1000000
        hitMeteor = None

        rayO, rayU = shot.get()

        for m in self.meteors:
            x,y = m.getCenter()            
            across, along = vec.ray_x_pnt(rayO, rayU, vec.Vector(x,y))

            if along > 0 and along < 1200 and across < 50 and along < prevNearest:
                hitMeteor = m
                prevNearest = along

        return hitMeteor

class MeteorSprite(pyglet.sprite.Sprite):
    #lifeTime = 0.08

    def __init__(self, x, y, w, h, batch):
        #global gAssets
        super(self.__class__, self).__init__(gAssets.getImage('asteroid'), x,y, batch=batch)

        th = 360*random.random()
        u,v = vec.uvec(th)
        speed = random.gauss(100, 50)
        self.motion = tv.LinearMotion2(x,y, speed*u, speed*v)
        #self.motion = tv.LinearMotion2(x,y, 0, 0)
        self.wrapW = w
        self.wrapH = h
        #self.motion = tv.LinearMotion2(x,y, 4, 4)
        self.angle = angle = tv.LinearMotion(0,90+90*random.random())
        self.alive = True
        self.timeAlive = 0.0

        self.radius = (self.width + self.height)/2/2

        self.update(0.0)

    def update(self, dt):
        self.motion.update(dt)
        self.angle.update(dt)

        #self.motion.wrap(-self.wrapW, 2 * self.wrapW, -self.wrapH, 2 * self.wrapH)
        #self.motion.wrap(-1.0* self.wrapW, 2.0 * self.wrapW, -1.0 * self.wrapH, 2.0 * self.wrapH)
        self.motion.bounce(-1.0* self.wrapW, 2.0 * self.wrapW, -1.0 * self.wrapH, 2.0 * self.wrapH)

        self.x, self.y = self.motion.getValue()

        self.rotation = self.angle.getValue()

    def getCenter(self):
        return self.x, self.y

    def getRadius(self):
        return self.radius

    def getValue(self):
        return [1]*10

    def dump(self):
        return "(%d, %d)" % (self.x, self.y)


class ShotSprite(pyglet.sprite.Sprite):
    lifeTime = 0.08

    def __init__(self, position, angle, batch):
        ga = gAssets
        super(ShotSprite, self).__init__(ga.getImage('shot'), *position, batch=batch)
        self.position = position
        self.angle = angle
        self.alive = True
        self.timeAlive = 0.0

        self.update(0.0)

    def update(self, dt):
        self.x, self.y = self.position
        self.rotation = self.angle

        self.timeAlive += dt
        if self.timeAlive > self.__class__.lifeTime:
            self.alive = False

    def get(self):
        # Sigh. Gotta set some standards w.r.t. angles
        return vec.Vector(self.x, self.y), vec.Vector(*vec.uvec(self.rotation+90.))

class MultiExplosion(object):
    """A timed sequence of animated sprites and sounds"""
    def __init__(self, x, y, times):
        super(MultiExplosion, self).__init__()
        self.x = x
        self.y = y
        self.times = times
        self.alive = True
        self.timeAlive = 0.0

        # Note: sounds are just started and continue on their own, sprites
        # need to be rememberd and drawn by us.

        self.sprites = []
        self.players = []

        self.nextTimeIdx = 0

    def update(self, dt):
        self.timeAlive += dt
        for s in self.sprites:
            s.update(dt)

        if self.nextTimeIdx >= len(self.times):
            self.alive = False
            return

        if self.timeAlive < self.times[self.nextTimeIdx]:
            return

        # Time for next boom
        s = ExplosionSprite(self.x + 100*random.random(), self.y + 100*random.random())
        self.sprites.append(s)

        player = pyglet.media.Player()
        player.queue(gAssets.getSound('boom'))
        player.play()
        self.players.append(player)

        #gAssets.getSound('boom2').play()

        self.nextTimeIdx += 1
        

    def draw(self):
        for s in self.sprites:
            s.draw()

class ExplosionSprite(pyglet.sprite.Sprite):
    lifeTime = 0.75 # Just a guess, doesn't matter as it's only used for clean-up

    def __init__(self, x, y):
        super(self.__class__, self).__init__(gAssets.getImage('explosion'), x, y)

        th = 360*random.random()
        u,v = vec.uvec(th)
        self.alive = True
        self.timeAlive = 0.0
        self.angle = tv.LinearMotion(0,120)

    def update(self, dt):
        #self.motion.update(dt)
        self.angle.update(dt)

        #self.x, self.y = self.motion.getValue()

        self.rotation = self.angle.getValue()
        self.timeAlive += dt

        if self.timeAlive > self.__class__.lifeTime:
            self.alive = False


class DgbSquare(pyglet.sprite.Sprite):

    def __init__(self, x, y):
        super(DgbSquare, self).__init__(gAssets.getImage('dbg1'), x,y)
        self.xPos = x
        self.yPos = y

    def shift(self, dx, dy):
        self.xPos += dx
        self.yPos += dy

    def update(self, dt):
        self.x = self.xPos
        self.y = self.yPos

class DgbSquare2(pyglet.sprite.Sprite):

    def __init__(self, x, y):
        super(self.__class__, self).__init__(gAssets.getImage('dbg2'), x,y)
        d = 300
        p = 2000
        critP = d*d/4
        critD = math.sqrt(4.0 * p)

        d = 500
        #print "critP", critP, ", critD", critD
        #print "p", p, ", d", d
        # p 2000 , d 500 works nice


        self.xPos = tv.TargetTracker(p, d)
        self.xPos.initVals(0,0)
        
        self.yPos = tv.TargetTracker(p, d)
        self.yPos.initVals(0,0)

    def shift(self, dx, dy):
        self.xPos += dx
        self.yPos += dy

    def update(self, dt):
        self.x = self.xPos.update(dt)
        self.y = self.yPos.update(dt)


# Not exactly sprites down here, just other things that decorate the screen

class ScoreBoard(pyglet.text.Label):
    """docstring for Score"""

    flipRate = 0.05 # seconds between flips

    def __init__(self, props):

        super(ScoreBoard, self).__init__(
            text="0", font_name='Orbitron',  bold=True, font_size=24,
            anchor_x = "center", anchor_y="bottom",
            color=(255,255,0, 200),
            x= 25 + props.windowWidth//2,
            y=10)

        self.value = 0
        #self.outOf = 0
        self.pendingBumps = []
        self.timeSinceBump = 10000.0 # infinity
        self.justBumped = False

    def incrOutOfXXX(self, x):
        self.outOf += x
        self.text = "%d / %d" % (self.value, self.outOf)


    def addScore(self, bumps):
        #self.value += bump
        #self.text = "%d / %d" % (self.value, self.outOf)
        #self.text = "%d" % (self.value, )
        for i, b in enumerate(bumps):
            if i < len(self.pendingBumps):
                self.pendingBumps[i] += b
            else:
                self.pendingBumps.append(b)


    def update(self, dt):
        self.timeSinceBump += dt

        if self.pendingBumps and self.timeSinceBump > self.__class__.flipRate:
            self.value += self.pendingBumps.pop(0)
            self.font_size = 36
            self.text = "%d" % (self.value, )
            self.timeSinceBump = 0.0
            self.justBumped = True
        elif not self.pendingBumps and self.justBumped :
            # Back to normal size after bumping
            self.font_size = 24
            self.text = "%d" % (self.value, )
            self.justBumped = False


class StarField(object):

    def __init__(self, w, h ):
        ga = gAssets
        self.stars = []
        self.batch = pyglet.graphics.Batch()

        arr = (
            22 * [ga.getImage('star-sml-1')] +
            22 * [ga.getImage('star-sml-2')] +
            22 * [ga.getImage('star-sml-3')] +
            22 * [ga.getImage('star-sml-4')] +
            22 * [ga.getImage('star-sml-5')] +
            22 * [ga.getImage('star-sml-6')] +
            15 * [ga.getImage('star-med-1')] +
            15 * [ga.getImage('star-med-2')] +
            3 * [ga.getImage('star-lrg-1')] +
            3 * [ga.getImage('star-lrg-2')]
            )

        #arr = 50 * [ga.getImage('star-sml-2')]
        #arr = 50 * [ga.getImage('star-sml-5')]
        #arr = 50 * [ga.getImage('star-sml-6')]

        for st in 7*arr:
            #x, y = random.randrange(-2*w,3*w), random.randrange(-2*h,3*h)
            x, y = random.gauss(0.5*w,2*w), random.gauss(0.5*h,2*h)
            sprite = pyglet.sprite.Sprite(st, x, y, batch=self.batch)

            #sprite.opacity = 128 + 128 * random.random()
            sprite.opacity = random.gauss(200, 30)
            sprite.rotation = 360 * random.random()
            self.stars.append(sprite)

        glxy = pyglet.sprite.Sprite(ga.getImage('galaxy'), 0.3*w, 0.3*h, batch=self.batch)
        self.stars.append(glxy)

    def update(self, dt):
        pass # For now. Later, twinkling!


    def draw(self):
        self.batch.draw()


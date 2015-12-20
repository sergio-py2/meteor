#!python

import random
import math

import pyglet
import pyglet.gl as gl

import vector as vec
import timevars as tv


gAssets = None

class Swarm(object):
    ''' All the non-player objects (not sure if ShotSprites are included)'''

    def __init__(self, props):
        self.props = props
        self.meteors = []
        self.meteorBatch = pyglet.graphics.Batch()

        self.explosions = []

        self.gameTime = 0.0

        self.meteorCountCurve = tv.PLInterpolator([
            (  0, 12),
            ( 60, 25),
            (120, 30),
            (240, 45),
            (300, 55),
            (1000, 1000),
            ])

        self.meteorSpeedCurve = tv.PLInterpolator([
            (  0, 100),
            ( 90, 150),
            (180, 200),
            (220, 230),
            (1000,500),
            ])

        self.meteorPool = (
            20 * ['asteroid-1'] +
            10 * ['asteroid-2'] +
             5 * ['asteroid-3']
            )

    def initialMeteors(self, n, shipPosition):

        w = self.props.windowWidth
        h = self.props.windowHeight

        for i in range(0,n):
            x = random.uniform(-w, 2*w)
            y = random.uniform(-h, 2*h)
            
            dx, dy = (x - shipPosition[0]), (y - shipPosition[1])
            if dx*dx + dy*dy < 150*150:
                # Don't start off right next to a meteor
                # And it's okay if we don't get exactly n created here.
                continue
            
            speed = random.gauss(100, 30)
            name = random.choice(self.meteorPool)

            m = MeteorSprite(name, x, y, speed, self.meteorBatch, self.props)
            self.meteors.append(m)


    def nItems(self):
        return len(self.meteors)

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

        #nMeteors = len(self.meteors)


    def spawnNew(self, shipPosition, viewportOrigin):
        # This is very stochastic. It tries to create a new meteor,
        # but if it doesn't on this go-around is just returns, as it will
        # be called again fairly soon.
        #targetN = 15
        targetN = int(self.meteorCountCurve(self.gameTime))

        if len(self.meteors) >= targetN:
            return
        #print "Have", len(self.meteors), "meteors, want", targetN

        w = self.props.windowWidth
        h = self.props.windowHeight

        x = None
        y = None
        offset = 250

        side = random.randint(0,3)
        # side selects (left, right, bottom, top) 
        sides = ('left', 'right', 'bottom', 'top') # for debugging
        if side < 2:
            # left or right
            y = viewportOrigin[1] + random.randrange(h)
            if side == 0:
                x = viewportOrigin[0] - offset  
            else:
                x = viewportOrigin[0] + w + offset

        else:
            # top or bottom
            x = viewportOrigin[0] + random.randrange(w)
            if side == 2:
                y = viewportOrigin[1] - offset  
            else:
                y = viewportOrigin[1] + h + offset

        # Make sure it's within the meteor field
        if x < -w or y < -h or x > 2*w or y > 2*h:
            return

        speedBase = self.meteorSpeedCurve(self.gameTime)
        speed = random.gauss(speedBase, 30)
        name = random.choice(self.meteorPool)

        m = MeteorSprite(name, x, y, speed, self.meteorBatch, self.props)
        self.meteors.append(m)

        #print "generated meteor", shipPosition, viewportOrigin, sides[side], x, y

    # To Be Obsoleted
    def addMeteorsXXX(self, n, shipPosition):
        return
        w = self.props.windowWidth
        h = self.props.windowHeight

        for _ in range(0,n):
            # Meteors bounce around in a 3w x 3h block
            # Spawn new meteor on "opposite side of the torus"
            # This is not good!!! XXX
            speed = random.gauss(100, 30)
            x = tv.wrap(shipPosition[0] + 1.5*w, -w, 2*w)
            y = tv.wrap(shipPosition[1] + 1.5*h, -h, 2*h)
            m = MeteorSprite(x, y, speed, self.meteorBatch, self.props)
            self.meteors.append(m)
            #print shipPosition, x, y
        

    def findShotHit(self, shot, margin):
        prevNearest = 1000000
        hitMeteor = None

        rayO, rayU = shot.get()

        for m in self.meteors:
            x,y = m.getCenter()            
            across, along = vec.ray_x_pnt(rayO, rayU, vec.Vector(x,y))

            if (along > 0 and along < 1200 and 
                across < m.getRadius() + margin and 
                along < prevNearest):

                hitMeteor = m
                prevNearest = along

        return hitMeteor

class MeteorSprite(pyglet.sprite.Sprite):

    def __init__(self, name, x, y, speed, batch, props):
        #global gAssets
        super(self.__class__, self).__init__(gAssets.getImage(name), x,y, batch=batch)
        self.props = props
        self.name = name

        th = 360*random.random()
        u,v = vec.uvec(th)
        #speed = random.gauss(100, 50)
        self.motion = tv.LinearMotion2(x,y, speed*u, speed*v)
        #self.motion = tv.LinearMotion2(x,y, 0, 0)
        #self.wrapW = w
        #self.wrapH = h
        #self.motion = tv.LinearMotion2(x,y, 4, 4)
        self.angle = angle = tv.LinearMotion(0,90+90*random.random())
        self.alive = True
        self.timeAlive = 0.0

        self.radius = (self.width + self.height)/2/2

        self.update(0.0)

    def update(self, dt):
        self.motion.update(dt)
        self.angle.update(dt)

        w = self.props.windowWidth
        h = self.props.windowHeight

        #self.motion.wrap(-self.wrapW, 2 * self.wrapW, -self.wrapH, 2 * self.wrapH)
        #self.motion.wrap(-1.0* self.wrapW, 2.0 * self.wrapW, -1.0 * self.wrapH, 2.0 * self.wrapH)
        self.motion.bounce(-w, 2.0 * w, -h, 2.0 * h)

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
            # Bug: doesn't allow time for last boom to play.
            self.alive = False
            return

        if self.timeAlive < self.times[self.nextTimeIdx]:
            return

        # Time for next boom
        s = ExplosionSprite(self.x + 100*random.random(), self.y + 100*random.random())
        self.sprites.append(s)

        player = pyglet.media.Player()
        player.queue(gAssets.getSound('bomb-explosion-1'))
        player.play()
        self.players.append(player)

        #gAssets.getSound('boom2').play()

        self.nextTimeIdx += 1

    def done(self):
        return not self.alive
        

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


# Not exactly sprites down here, just other things that decorate the screen

class ScoreBoard(pyglet.text.Label):
    """docstring for Score"""

    flipRate = 0.05 # seconds between flips
    regularFontSize = 30
    bigFontSize = 36
    yellow = (255,255,0, 200)
    red = (255,0,0, 200)


    def __init__(self, props):

        super(ScoreBoard, self).__init__(
            text="0", font_name='Orbitron',  bold=True, font_size=ScoreBoard.regularFontSize,
            anchor_x = "center", anchor_y="bottom",
            color=ScoreBoard.yellow,
            x= 25 + props.windowWidth//2,
            y=10)

        self.value = 0
        #self.outOf = 0
        self.pendingBumps = []
        self.timeSinceBump = 10000.0 # infinity
        self.justBumped = False


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
            bump = self.pendingBumps.pop(0)
            self.value += bump

            if bump < 0:
                self.color = ScoreBoard.red
            else:
                self.color = ScoreBoard.yellow

            self.font_size = ScoreBoard.bigFontSize
            self.text = "%d" % (self.value, )
            self.timeSinceBump = 0.0
            self.justBumped = True
        elif not self.pendingBumps and self.justBumped :
            self.color = ScoreBoard.yellow

            # Back to normal size after bumping
            self.font_size = ScoreBoard.regularFontSize
            self.text = "%d" % (self.value, )
            self.justBumped = False


class MeteorRadar(object):
    """docstring for MeteorRader"""
    def __init__(self, props):
        super(MeteorRadar, self).__init__()
        self.props = props

        commonOpts = {
            'font_name': 'Orbitron', 
            'bold': True, 
            'font_size': 24,
            'color': (255,255,0, 200),
            'text': ""}

        t = commonOpts.copy()
        t.update( {'anchor_x': "right", 'anchor_y': "bottom", 'x':75, 'y':10})

        self.number = pyglet.text.Label(**t)

        t = commonOpts.copy()
        t.update( {'anchor_x': "left", 'anchor_y': "bottom", 'x':80, 'y':10})

        self.text = pyglet.text.Label(**t)

        self.nItems = 0

    def draw(self):
        self.number.draw()
        self.text.draw()

    def setNumItems(self, n):
        if n == self.nItems:
            return

        self.nItems = n
        self.number.text = str(n)
        self.text.text = " meteors"
        #print "set radar to", n

class Timer(object):
    """docstring for MeteorRader"""
    def __init__(self, props):
        super(Timer, self).__init__()
        self.props = props
        self.seconds = 0.0
        self.currDisplaySeconds = -1

        xPos = props.windowWidth - 100

        commonOpts = {
            'font_name': 'Orbitron', 
            'bold': True, 
            'font_size': 16,
            'color': (255,255,0, 200),
            'text': "",
            'y': 10}

        t = commonOpts.copy()
        t.update( {'x':xPos})

        self.min = pyglet.text.Label(**t)

        xPos += 22
        t.update( {'x':xPos, 'text': ":"})
        self.colon = pyglet.text.Label(**t)

        xPos += 10
        t.update( {'x':xPos, 'text': ""})
        self.sec10s = pyglet.text.Label(**t)

        xPos += 22
        t.update( {'x':xPos})
        self.sec1s = pyglet.text.Label(**t)

        self.nItems = 0

    def update(self, dt):
        self.seconds += dt
        secondsInt = int(self.seconds)
        if secondsInt != self.currDisplaySeconds:
            m,s = divmod(secondsInt, 60)
            s10, s1 = divmod(s, 10)
            self.min.text      = str(m)
            self.sec10s.text   = str(s10)
            self.sec1s.text    = str(s1)



    def draw(self):




        self.min.draw()
        self.colon.draw()
        self.sec10s.draw()
        self.sec1s.draw()

class GameOver(object):
    """docstring for GameOver"""
    def __init__(self, props):
        super(GameOver, self).__init__()
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


    def update(self, dt):
        self.timeAlive += dt
        if self.timeAlive > 4.0:
            self.alive = False
        
    def draw(self):
        a = self.zoom(self.timeAlive)
        h = self.height(self.timeAlive)

        gl.glPushMatrix()
        gl.glTranslatef(self.props.windowWidth//2, h, 0)
        gl.glScalef(a,a,a)

        self.text.draw()
        
        gl.glPopMatrix()

    def done(self):
        return not self.alive

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


# De-buggery

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

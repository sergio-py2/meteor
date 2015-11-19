#!/c/Python27/python.exe  -u

import os
import sys

import pyglet
import pyglet.gl as gl
import pyglet.window.mouse as mouse
import pyglet.window.key as key
import pyglet.font.ttf

import random
import math

import TimeVars as tv
import Vector as v

gApp = None
gAssets = None


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

        # I think extending Window automatically has this as a handler
        #self.push_handlers(self.on_key_press)

    def on_key_press(self, symbol, modifiers):
        #print "GameWindow.on_key_press", symbol
        if self.keys[key.Q]:
            pyglet.app.exit()        
        
    def update(self, dt):
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
            for i,m  in enumerate(g.meteors):
                print "Meteor % 2d: %s" %(i,m.dump())

        # Interactions
        # We handle lazer blasts when they are created
        # What else should go here?

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
            g.addMeteors(10)

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
        if shot is not None:
            g.shots.append(shot)
            m = self.findShotHit(shot)
            if m is not None:
                m.alive = False
                g.score.addScore(10)

    def findShotHit(self, shot):
        prevNearest = 1000000
        hitMeteor = None

        rayO, rayU = shot.get()

        for m in self.gameElements.meteors:
            x,y = m.getCenter()            
            across, along = ray_x_pnt(rayO, rayU, v.Vector(x,y))

            if along > 0 and along < 1200 and across < 50 and along < prevNearest:
                hitMeteor = m
                prevNearest = along

        return hitMeteor

    def on_draw(self):
        # I really don't know what these are doing, and if there's any difference having them
        # here instead of just once at the top.
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        #gl.glClearColor(0.0, 0.0, 0.08, 1.0)
        gl.glEnable( gl.GL_BLEND)
        #gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        gl.glPushMatrix()

        # I don't really know what the direction conventions for glTranslate are,
        # so the minus signs are from experimenting.
        gl.glTranslatef(-self.viewportOrigin[0], -self.viewportOrigin[1], 0.0)
        self.clear()
        g = self.gameElements

        # Should I be pushing most of this code into GameElements?

        g.starField.draw()
        g.meteorBatch.draw()

        g.ship.draw()
        #g.dbgSquare1.draw()
        #g.dbgSquare2.draw()

        for shot in g.shots:
            if shot.alive:
                shot.draw()
        
        gl.glPopMatrix()
        g.score.draw()

class GameAssets(object):
    """ Loads images, sounds, etc. from files and holds them as pyglet-compatible
        objects. """

    def __init__(self):
        super(GameAssets, self).__init__()

    def loadAssets(self):
        self.images = {}

        si = pyglet.image.load('images/space_ship_neon6.png')
        #self.shipImage = si
        si.anchor_x = si.width//2
        si.anchor_y = int(si.height * 0.35)
        self.images['ship'] = si

        # Yeah, this is kind of a miscellaneous thing but it makes sense to put
        # it in assets along with the image it's talking about.
        self.shipTipAboveCenter = si.height - si.anchor_y - 10 # there's a border

        fl = self.loadStdImage('flames.png', 'flames')
        fl.anchor_x = si.anchor_x
        fl.anchor_y = si.anchor_y
        #self.images['flames'] = fl

        li = self.loadStdImage('shot_neon.png', 'shot')
        li.anchor_x = 0
        li.anchor_y = li.height//2

        self.loadStdImage('red.png', 'dbg1')
        self.loadStdImage('green.png', 'dbg2')

        self.loadStdImage('aster4.png', 'asteroid')

        self.loadStdImage('sirius-z1 - med.png', 'star-med-1')
        self.loadStdImage('betelgeuse - med.png', 'star-med-2')

        self.loadStdImage('sirius-z1 - lrg.png', 'star-lrg-1')
        self.loadStdImage('betelgeuse - lrg.png', 'star-lrg-2')

        self.loadStdImage('star-sml-1.png', 'star-sml-1')
        self.loadStdImage('star-sml-2b.png', 'star-sml-2')
        self.loadStdImage('star-sml-3.png', 'star-sml-3')
        self.loadStdImage('star-sml-4.png', 'star-sml-4')
        self.loadStdImage('star-sml-5b.png', 'star-sml-5')
        self.loadStdImage('star-sml-6b.png', 'star-sml-6')

        self.loadStdImage('image_2400e-Andromeda-Galaxy-b.png', 'galaxy')

        self.pew = pyglet.media.load('sound/pew4.mp3', streaming=False)

        # Get this font by specifying font_name='Orbitron', bold=True
        path = 'fonts/Orbitron Bold.ttf'
        pyglet.font.add_file(path)
        #pyglet.font.add_file('fonts/matt-mcinerney_orbitron/Orbitron Medium.ttf')

        #f = pyglet.font.load('Orbitron Bold')

    def loadStdImage(self, fileName, tag):
        # Loads the image and puts the anchor in the center.
        # You can re-set the center if that default isn't right.
        img = pyglet.image.load('images/%s' % fileName)
        img.anchor_x = img.width//2
        img.anchor_y = img.height//2
        self.images[tag] = img
        return img

    def getImage(self, tag):
        return self.images[tag]

class GameElements(object):
    """Holds all the elements that make up a game"""
    def __init__(self, props):
        super(GameElements, self).__init__()
        self.props = props
        
    def populateGame(self, assets):
        w = self.props.windowWidth
        h = self.props.windowHeight

        self.ship = ShipSprite( x=w//2, y=h//2, w=w, h=h)

        self.meteors = []
        self.meteorBatch = pyglet.graphics.Batch()
        self.score = Score()
        self.addMeteors(30)


        self.shots = []
        self.shotBatch = pyglet.graphics.Batch()

        self.starField = StarField(w, h)

        self.dbgSquare1 = DgbSquare(10,10)
        self.dbgSquare2 = DgbSquare2(10,10)

    def addMeteors(self, n):
        w = self.props.windowWidth
        h = self.props.windowHeight

        for _ in range(0,n):
            x = w*(3*random.random() - 1)
            y = h*(3*random.random() - 1)
            self.meteors.append(MeteorSprite(x,y,w,h, self.meteorBatch))
        
        self.score.incrOutOf( 10 * n)

    def update(self, dt):
        for m in self.meteors:
            m.update(dt)
            if not m.alive:
                m.delete()

        self.meteors = [m for m in self.meteors if m.alive == True]

        for sh in self.shots:
            sh.update(dt)
            if not sh.alive:
                sh.delete()

        self.shots = [sh for sh in self.shots if sh.alive == True]

        self.ship.update(dt)
        self.dbgSquare1.update(dt)
        self.dbgSquare2.update(dt)

#class ShipSprite(pyglet.sprite.Sprite):
class ShipSprite(object):
    def __init__(self, *args, **kwargs):
        #super(ShipSprite, self).__init__(self.__class__.image, x=kwargs['x'], y=kwargs['y'])
        ga = gAssets
        x, y = kwargs['x'], kwargs['y']
        self.spriteShip = pyglet.sprite.Sprite(ga.getImage('ship'), x=x, y=y)
        self.spriteFlames = pyglet.sprite.Sprite(ga.getImage('flames'), x=x, y=y)
        self.spriteFlames.opacity = 0
        self.motion = tv.ThrustMotionWithDrag( x, y)
        self.motion.setDrag(0.05)
        self.angleXXX = 0.0

        rotPull = 9000
        rotDrag = 800    
        self.angleVar = tv.AngleTargetTracker(rotPull, rotDrag)
        self.angleVar.initVals(0.0, 0.0)
        self.w = kwargs['w']
        self.h = kwargs['h']

        self.alive = True
        self.laserCannon = LaserCannon()
        self.maxThrustPower = 400
        self.currThrottle = 0.0

    def draw(self):
        self.spriteShip.draw()
        self.spriteFlames.opacity = clamp(0, self.currThrottle * 255, 255)
        self.spriteFlames.draw()


    def rotXXX(self, dtheta):
        self.angle += dtheta

    def thrust(self, dt, throttle):
        # We assume that at self.angle == 0, the forward direction
        # is x = 0, y = +1, and that +ive rotation is clock-wise
        # Throttle is from 0.0 to 1.0 (well, I guess I'm allowing negative tto)
        #ux, uy = uvec(self.angle)
        if throttle != 0.0:
            ux, uy = uvec(self.angleVar.value)
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

        ux, uy = uvec(th)
        tipOffset = gAssets.shipTipAboveCenter
        x,y = x + tipOffset*ux, y + tipOffset*uy

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
    resetTime = 0.1

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
        return v.Vector(self.x, self.y), v.Vector(*uvec(self.rotation+90.))

class MeteorSprite(pyglet.sprite.Sprite):
    lifeTime = 0.08

    def __init__(self, x, y, w, h, batch):
        super(self.__class__, self).__init__(gAssets.getImage('asteroid'), x,y, batch=batch)

        th = 360*random.random()
        u,v = uvec(th)
        speed = random.gauss(100, 50)
        self.motion = tv.LinearMotion2(x,y, speed*u, speed*v)
        #self.motion = tv.LinearMotion2(x,y, 0, 0)
        self.wrapW = w
        self.wrapH = h
        #self.motion = tv.LinearMotion2(x,y, 4, 4)
        self.angle = angle = tv.LinearMotion(0,90+90*random.random())
        self.alive = True
        self.timeAlive = 0.0

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

    def dump(self):
        return "(%d, %d)" % (self.x, self.y)


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

class Score(pyglet.text.Label):
    """docstring for Score"""
    def __init__(self, *args, **kwargs):

        super(Score, self).__init__(
            text="0", font_name='Orbitron',  bold=True, font_size=24,
            anchor_x = "left", anchor_y="bottom",
            color=(255,255,0, 200),
            x=10, y=10)

        self.value = 0
        self.outOf = 0

    def incrOutOf(self, x):
        self.outOf += x
        self.text = "%d / %d" % (self.value, self.outOf)


    def addScore(self, bump):
        self.value += bump
        self.text = "%d / %d" % (self.value, self.outOf)

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


def update(dt):
    #print "update", dt

    global gApp
    gApp.update(dt)


def uvec(degrees):
    rads = math.pi * degrees / 180.0
    return (math.sin(rads), math.cos(rads))

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

def clamp(low, val, high):
    if val >= high:
        return high
    if val <= low:
        return low
    return val

def ray_x_pnt(o, u, p):
    # Returns across, along distances
    d = p-o
    along = v.Dot(u, d)
    proj =  u * along
    perp = d - proj
    return v.Norm(perp), along

def main():
    global gApp
    global gAssets

    if len(sys.argv) > 1 and sys.argv[1] == '-f':
        windowOpts = {'fullscreen': True}
    else:
        windowOpts = {'width': 1200, 'height': 700}

    # Create the (few) global object
    gAssets = GameAssets()
    gAssets.loadAssets()

    gApp = Application(windowOpts)


    pyglet.clock.set_fps_limit(60)
    pyglet.clock.schedule_interval(update, 1/60.)

    pyglet.app.run()


if __name__ == '__main__':
    main()


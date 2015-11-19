#!/c/Python27/python.exe  -u

import math
import random

class LinearMotion(object):
    def __init__(self, x, vx):
        self.sx = x
        self.vx = vx

    def update(self, dt):
        self.sx += self.vx * dt

    def wrap( self, lo, hi):
        if self.sx > hi:
            self.sx -= (hi-lo)
        elif self.sx < lo:
            self.sx += (hi-lo)

    def bounce( self, lo, hi):
        if self.sx > hi:
            self.sx = 2*hi - self.sx
            self.vx *= -1.0
        elif self.sx < lo:
            self.sx = 2*lo - self.sx
            self.vx *= -1.0

    def getValue(self):
        return self.sx

class LinearMotion2(object):
    def __init__(self, x, y, vx, vy):
        super(self.__class__, self).__init__()
        self.x = LinearMotion(x,vx)
        self.y = LinearMotion(y,vy)

    def update(self, dt):
        self.x.update(dt)
        self.y.update(dt)

    def wrap( self, lox, hix, loy, hiy):
        self.x.wrap(lox, hix)
        self.y.wrap(loy, hiy)

    def bounce( self, lox, hix, loy, hiy):
        self.x.bounce(lox, hix)
        self.y.bounce(loy, hiy)

    def getValue(self):
        return (self.x.getValue(), self.y.getValue())

class ThrustMotionWithDrag(object):
    """docstring for Motion"""
    def __init__(self, x, y):
        super(self.__class__, self).__init__()
        self.sx = x
        self.sy = y

        self.vx = 0
        self.vy = 0

        self.ax = 0
        self.ay = 0

    def setDrag(self, drag):
        self.drag = drag

    def position(self):
        #return (round(self.sx), round(self.sy))
        return (self.sx, self.sy)

    def velocity(self):
        #return (round(self.sx), round(self.sy))
        return (self.vx, self.vy)

    def update(self, dt):
        vLen = math.sqrt(self.vx * self.vx + self.vy * self.vy)

        self.vx += self.ax * dt
        self.vy += self.ay * dt

        self.sx += self.vx * dt
        self.sy += self.vy * dt

        self.ax = -self.vx * vLen * self.drag * dt
        self.ay = -self.vy * vLen * self.drag * dt


    def thrust(self, dvx, dvy):
        self.vx += dvx
        self.vy += dvy

    #def setForce(self, ax, ay):
    #    self.ax = ax
    #    self.ay = ay

    def wrap( self, w, h):
        if self.sx > w:
            self.sx -= w
        elif self.sx < 0:
            self.sx += w

        if self.sy > h:
            self.sy -= h
        elif self.sy < 0:
            self.sy += h

    def bounce( self, w, h):
        if self.sx > w:
            self.sx = 2*w - self.sx
            self.vx *= -1.0
        elif self.sx < 0:
            self.sx = -self.sx
            self.vx *= -1.0

        if self.sy > h:
            self.sy = 2*h - self.sy
            self.vy *= -1.0
        elif self.sy < 0:
            self.sy = -self.sy
            self.vy *= -1.0


class TargetTracker(object):
    """
    Value tracks target, with damping
    User should set value and target before using, but we don't enforce that
    with the c'tor.
    """
    def __init__(self, pull, drag):
        super(TargetTracker, self).__init__()
        # Parameters
        self.pull = pull
        self.drag = drag

        # Target value
        self.target = None

        # State: value and d_value/dt
        self.value  = None         # consider this publicly readable.
        self.dvalue = 0.0

        disc = self.drag * self.drag - 4.0 * self.pull
        d_over_two = -self.drag / 2.0
        if disc >= 0:
            r = math.sqrt(disc)/2.0

            #print "r1", d_over_two - r
            #print "r2", d_over_two + r
        else:
            #print d_over_two, "+-", math.sqrt(-disc)/2.0, "i"
            pass
        

    def initVals(self, value, target):
        self.value = value
        self.target = target

    def setTarget(self, target):
        self.target = target


    def update(self, dt):
        # Returns updated value as a convenience
        f = self.pull*(self.target - self.value) - self.drag * self.dvalue
        a = f * dt
        self.dvalue += a * dt
        self.value  += self.dvalue * dt
        return self.value


class AngleTargetTracker(TargetTracker):
    ''' Just a TargetTracker that handles wrapping angles. '''

    def __init__(self, pull, drag):
        super(AngleTargetTracker, self).__init__(pull, drag)


    def setTarget(self, target):
        #print self.value, self.target
        prd = math.floor((target - self.value + 180.0)/360.0)
        if prd != 0:
            self.target = target - 360. * prd
        else:
            self.target = target


class TimeAverage(object):
    """Keeps a windowed decaying time average of a quantitiy"""
    def __init__(self, decayRate, initVal=0.0):
        super(TimeAverage, self).__init__()
        self.decayRate = decayRate
        self.updateRate = 1.0 - decayRate
        self.currValue = initVal

    def update(self, val):
        # Note: this isn't time dependent. For the window to be a consistent time
        # interval we should include a dt, but we'll assume the dt's are pretty
        # constant and punt the issue.

        self.currValue = self.updateRate * val + self.decayRate * self.currValue 
        return self.currValue
        
    def value(self):
        return self.currValue


class TimeAverage2(object):
    def __init__(self, decayRate, initValX=0.0, initValY=0.0):
        super(TimeAverage2, self).__init__()
        self.x = TimeAverage(decayRate, initValX)
        self.y = TimeAverage(decayRate, initValY)

    def update(self, xVal, yVal):
        self.x.update(xVal)
        self.y.update(yVal)

        return (self.x.currValue, self.y.currValue)

    def value(self):
        return (self.x.currValue, self.y.currValue)

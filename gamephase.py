#!python  -u

import math

import pickle
import copy
import random

import pyglet
import pyglet.gl as gl
import pyglet.window.key as key

import vector as vec
from vector import Vector as Vec

import timevars as tv
import sprites
import gameelements
import activeobjects as ao

from geoip import GeoIPData
from gameassets import GameAssets
from config import Config

class GamePhase(object):
    """ Abstract base class for one phase of a game."""
    def __init__(self,  gameElements, windowProps, evtSrc):
        super(GamePhase, self).__init__()
        # You can create all the objects you need for this game phase

    def start(self):
        # Called when game phase becomes active
        pass

    def update(self, dt, userInput):
        # Called every game-tick when active
        # Returns:
        #    Either 'None' to indicate that this phase is still active,
        #    or an instance of the next Game Phase.
        #    This implements our state machine!
        pass        

    def draw(self, window):
        # Called every draw-tick when active. 
        # Make OpenGL calls here, but leave the stack the way you found it.
        pass        

    def delete(self):
        # Called after update returns next Game Phase.
        # A chance to free up resources (OpenGL stuff?)
        pass        




class PlayPhaseBase(GamePhase):
    def __init__(self, windowProps, evtSrc ):
        #super(GamePhase, self).__init__()
        self.windowProps = windowProps
        self.evtSrc = evtSrc

        self.gameElements = gameelements.GameElements(windowProps)
        self.gameElements.populateGame( GameAssets.Instance() )

        self.shotMargin = 20

        self.viewportOrigin = [0.0, 0.0]
        self.destinationTracker = tv.TimeAverage2(0.7, *self.gameElements.ship.getPosition())

        self.shake = None

        self.endGame = None
        self.explodedMarker = ao.MarkerAO()
        self.drawFrameMarker = ao.MarkerAO()

    def start(self):
        pass

    def update(self, dt, userInput):
        ge = self.gameElements

        # Elements that evolve pretty much by themselves.
        ge.update(dt)

        # End of game display
        if self.endGame is not None:
            self.endGame.update(dt, userInput)


        # Regular game play
        # Use controls to update the ship.
        if not self.explodedMarker.done():
            if userInput.joystick is not None:
                self.joystickUpdate(dt, userInput.joystick)
            else:
                self.keyboardUpdate(dt, userInput.keys)

        if userInput.keys[key.M]:
            print ""
            for i,m  in enumerate(g.swarm.meteors):
                print "Meteor % 2d: %s" %(i,m.dump())

        if userInput.keys[key.K]:
            pass
            self.spaceShipDeath()

        # Interactions
        # We handle lazer blasts when they are created
        # What else should go here?

        # Let the viewport continue to drift even after ship destroyed 
        # instead of just freezing
        #if not self.explodedMarker.done():
        self.updateViewport(dt)

        posn = ge.ship.getPosition()
        ge.swarm.spawnNew(posn, self.viewportOrigin)
        
        hitObj, severity = self.findHit()

        if hitObj is not None:
            if severity > 0.8:
                #print "graze", severity
                pass
            elif severity > 0.28:
                # Shake
                if self.shake is None:
                    self.shake = tv.Shaker2(0.75, 10.0, 3.0)
                    self.spaceShipShake()
            else:
                # Explode
                self.spaceShipDeath()


        #self.radar.setNumItems( g.swarm.nItems())

    def findHit(self):
        # Check for hits on space ship

        ship = self.gameElements.ship 

        p1 = Vec(*ship.getPosition())
        r1 = ship.getRadius()


        prevMinD = 1000000 # infinity
        hitObj = None
        severity = 1000.0

        for o in self.gameElements.swarm.objects():
            p2 = Vec(*o.getCenter())
            r2 = o.getRadius()

            d = vec.Distance(p1, p2)
            if d < r1 + r2 and d < prevMinD:
                #print d, r1, r2
                prevMinD = d
                hitObj = o
                severity = d/(r1+r2)

        if hitObj is None:
            return None, None
            #print "Hit", severity
        else:
            return hitObj, severity

    def joystickUpdate(self, dt, joystick):
        js = joystick
        g = self.gameElements

        #g.dbgSquare1.shift(3*js.rx, -3*js.ry)
        #g.dbgSquare2.shift(3*js.rx, -3*js.ry)
        #g.dbgSquare2.xPos.target = g.dbgSquare1.xPos
        #g.dbgSquare2.yPos.target = g.dbgSquare1.yPos

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

    def keyboardUpdate(self, dt, keys):
        # Use keyboard to control ship
        g = self.gameElements

        drot = 800
        rot = g.ship.angleVar.value

        thrust = 0
        rotNew = rot

        if keys[key.LEFT]:
            rotNew +=  -drot * dt
            #g.ship.angleVar.setTarget(th - drot * dt)
            #g.ship.rot( -drot * dt)

        if keys[key.RIGHT]:
            rotNew +=  +drot * dt
            #g.ship.angleVar.setTarget(th + drot * dt)
            #g.ship.rot( drot * dt)
        
        if keys[key.UP]:
            thrust += 1.0
            #g.ship.thrust( dt, 1.0)

        # Nope, converted to increasing drag
        if keys[key.DOWN]:
            g.ship.drag( 1.0 )
            #g.ship.sprite = pyglet.sprite.Sprite(self.assets.dbgImage2)
        else:
            g.ship.drag(0.0)

        g.ship.thrust( dt, thrust)
        g.ship.angleVar.setTarget(rotNew)

        if keys[key.SPACE] :
            self.shoot()

    def shoot(self):
        ga = GameAssets.Instance()
        g = self.gameElements
        shot = g.ship.shoot(g.shotBatch)
        if Config.Instance().sound():
            ga.getSound('lazer-shot-1').play()

        if shot is not None:
            g.shots.append(shot)

            m = g.swarm.findShotHit(shot, self.shotMargin)
            
            if m is not None:
                self.processHit(m)

    def processHit(self, meteor):
        ga = GameAssets.Instance()
        g = self.gameElements

        points = meteor.getValue()
        self.score.addScore(points)
        g.swarm.explode(meteor)
        if Config.Instance().sound():
            ga.getSound('bomb-explosion-1').play()

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
        w = self.windowProps.windowWidth
        h = self.windowProps.windowHeight

        #x,y = ship.getPosition()
        #x,y = ship.getProjectedPosition(0.4)
        vx,vy = ship.getDirection()
        t = 1.3 * abs(vx) + 0.4 * abs(vy)

        x,y = self.destinationTracker.update(*ship.getProjectedPosition(t))

        border = 200
        factor = 0.8

        # Shift the viewport
        xRel = x - self.viewportOrigin[0]
        if xRel > w - border:
            self.viewportOrigin[0] += factor * (xRel - w + border)
        elif xRel < border:
            self.viewportOrigin[0] -= factor * (border - xRel)

        yRel = y - self.viewportOrigin[1]
        if yRel > h - border:
            self.viewportOrigin[1] += factor * (yRel - h + border)
        elif yRel < border:
            self.viewportOrigin[1] -= factor * (border - yRel)

        if self.shake is not None:
            self.shake.update(dt)
            (sx,sy) = self.shake.getValue()
            self.viewportOrigin[0] += sx
            self.viewportOrigin[1] += sy

            if not self.shake.alive:
                self.shake = None

    # XXX You're in the base class - remove this
    def draw(self, window):

        self.drawSpace(window)

        if self.endGame and self.drawFrameMarker.done():
            # draw "Game Done" in absolute window position
            self.endGame.draw(window)

    def drawSpace(self, window):

        gl.glPushMatrix()

        # GL matrices are applied last-added-first, so this *is* the right
        # order for pushing them.
        gl.glTranslatef(-self.viewportOrigin[0], -self.viewportOrigin[1], 0.0)

        if self.shake is not None:
            # We want to rotate around the center of the current viewport
            # vpc = view port center
            vpc_x = self.viewportOrigin[0] + self.windowProps.windowWidth//2
            vpc_y = self.viewportOrigin[1] + self.windowProps.windowHeight//2
            
            gl.glTranslatef(vpc_x, vpc_y, 0.0)
            gl.glRotatef(self.shake.getAngle(), 0, 0, 1)
            gl.glTranslatef(-vpc_x, -vpc_y, 0.0)
        
        ge = self.gameElements

        ge.starField.draw()
        ge.swarm.draw()

        if not self.explodedMarker.done():
            ge.ship.draw()

        if self.endGame and not self.drawFrameMarker.done():
            self.endGame.draw(window)

        for shot in ge.shots:
            if shot.alive:
                shot.draw()
        
        gl.glPopMatrix()


class PlayCountPhase(PlayPhaseBase):
    def __init__(self, windowProps, evtSrc ):
        super(PlayCountPhase, self).__init__( windowProps, evtSrc )

        self.score = sprites.ScoreBoard(windowProps)
        self.radar = sprites.MeteorRadar(windowProps)
        self.timer = tv.CountUpTimer(running=True)
        self.timeDisplay = sprites.TimeDisplay(windowProps)

    def update(self, dt, userInput):
        gp = super(PlayCountPhase, self).update(dt, userInput)
        if gp is not None:
            return gp

        self.score.update(dt)

        #if self.explodedMarker is None or not self.explodedMarker.done():
        if not self.explodedMarker.done():
            self.timer.update(dt)
        self.timeDisplay.setTime( self.timer.time())
        
        self.radar.setNumItems( self.gameElements.swarm.nItems())

        if self.endGame and self.endGame.done():
            # Go to the leader board
            score = self.score.value
            state = GeoIPData.Instance().state
            d = (None, state, score)
            lb = LeaderBoardPhase(self.windowProps, self.evtSrc, d)
            return lb


    def draw(self, window):
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glEnable( gl.GL_BLEND)
        window.clear()

        # Replace with call to drawSpace()
        super(PlayCountPhase, self).draw(window)

        self.score.draw()
        self.radar.draw()
        self.timeDisplay.draw()

    def spaceShipShake(self):
        self.score.addScore([-1]*4)

    def spaceShipDeath(self):
        if self.endGame:
            return

        shakeTime = 0.75
        self.shake = tv.Shaker2(shakeTime, 22.0, 8.0)
        self.score.addScore([-2]*8)
        ship = self.gameElements.ship

        # Set up end-of-game ActiveObjects

        # Position doesn't matter - it'll be updated later
        explosionSprite = sprites.MultiExplosion(0.,0., [0.0, 0.3, 0.5, 0.6, 1.0, 1.8])


        def positionExplosion(ship=self.gameElements.ship, explosion=explosionSprite):
            p = ship.getPosition()
            explosion.x = p[0]
            explosion.y = p[1]

        self.endGame = ao.SerialObjects(
            ao.DelayAO(shakeTime/2.),
            ao.FunctionWrapperAO(positionExplosion),
            self.explodedMarker,
            ao.FunctionWrapperAO(lambda: ship.drag(0.66)),
            ao.SoundWrapperAO(GameAssets.Instance().getSound('wilhelm')),
            ao.SpriteWrapperAO(explosionSprite),
            ao.FunctionWrapperAO(lambda: ship.drag(0.9)),
            self.drawFrameMarker,
            ao.DelayAO(0.2),
            ao.GameOverAO(self.windowProps)
            )

        self.endGame.start()



class PlayTimePhase(PlayPhaseBase):
    def __init__(self, windowProps, evtSrc ):
        super(PlayTimePhase, self).__init__( windowProps, evtSrc )

        #self.score = sprites.ScoreBoard(windowProps)
        #self.radar = sprites.MeteorRadar(windowProps)
        #self.timer = sprites.Timer(windowProps)
        self.timeElapsed = tv.CountUpTimer(running=True)
        self.timeElapsedDisplay = sprites.TimeDisplay(windowProps)
        
        self.timeRemaining = 20.0
        self.timeRemainingDisplay = sprites.TimeDisplay(windowProps, displayTenths = True)
        self.playing = True



    def update(self, dt, userInput):
        if self.playing:
            gp = super(PlayTimePhase, self).update(dt, userInput)
            if gp is not None:
                return gp

        if self.playing:

            self.timeElapsed.update(dt)
            self.timeElapsedDisplay.setTime( self.timeElapsed.time())

            self.timeRemaining -= dt
            if self.timeRemaining > 0.:
                self.timeRemainingDisplay.setTime(self.timeRemaining)
                return

        # Time ran out
        self.playing = False
        self.timeRemaining = 0.
        self.timeRemainingDisplay.setTime(self.timeRemaining)
               
        #self.score.update(dt)
        #self.timer.update(dt)
        #self.radar.setNumItems( self.gameElements.swarm.nItems())

    def draw(self, window):
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glEnable( gl.GL_BLEND)
        window.clear()

        super(PlayTimePhase, self).draw(window)

        self.timeElapsedDisplay.draw()
        gl.glPushMatrix()
        gl.glTranslatef(-250., 0., 0.)
        self.timeRemainingDisplay.draw()
        gl.glPopMatrix()

    def processHit(self, meteor):
        ga = GameAssets.Instance()
        g = self.gameElements

        points = meteor.getValue()
        self.timeRemaining += 1.5
        #self.score.addScore(points)
        g.swarm.explode(meteor)
        if Config.Instance().sound():
            ga.getSound('bomb-explosion-1').play()
        

    def spaceShipShake(self):
        self.timeRemaining -= 2.



class TextEntryWidget(object):
    """ Does not allow user to input an empty string. 
        Could control this with an option later, if needed.
    """
    def __init__(self, x, y, width, evtSrc):
        #super(TextEntryWidget, self).__init__()
        self.x = x
        self.y = y
        self.width = width
        self.evtSrc = evtSrc
        self.enteredText = None  # gets a value when the user hits Enter

        self.cursorBlink = tv.Blinker(1.2)

        batch = pyglet.graphics.Batch()
        self.documentBatch = batch

        self.document = pyglet.text.document.UnformattedDocument("")
        self.document.set_style(0, 0, dict(
            color=(0, 255, 0, 200),
            background_color=None,
            font_name='Orbitron',
            bold=True,
            font_size=50,
            #kerning=7,
            #underline=(0,200,35,180)
            ))


        font = self.document.get_font()
        height = font.ascent - font.descent

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width, height, multiline=False, batch=batch)
        self.layout.x = x
        self.layout.y = y

        self.caret = pyglet.text.caret.Caret(self.layout)
        self.caret.visible = False

        # Stuff for my cursor

        self.cursor = pyglet.text.Label(text="_", 
            font_name='Orbitron',  bold=True, 
            font_size=50,
            anchor_x = "left", anchor_y="top", 
            color=(0, 255, 0, 200))

        evtSrc.push_handlers(self.caret)
        evtSrc.push_handlers(on_text=self.on_text)

    def on_text(self, text):
        if self.enteredText is not None:
            return True

        if ord(text) == 13:
            if self.document.text != "":
                self.enteredText = self.document.text
                #print self.enteredText
            return True
        else:
            return False

    def update(self, dt):
        self.cursorBlink.update(dt)

    def draw(self, window):
        self.documentBatch.draw()

        p = self.layout.get_point_from_position(self.caret.position)
        self.cursor.x = p[0]+11
        self.cursor.y = p[1]+62

        if self.enteredText is None and self.cursorBlink.isOn():
            self.cursor.draw()

    def delete(self):
        self.evtSrc.pop_handlers()
        self.evtSrc.pop_handlers()
        
class LeaderBoardData(object):
    """docstring for LeaderBoardData"""
    def __init__(self):
        self.msg = ("!!!!! DO NOT LOOK IN THIS FILE !!!!!" +
            " If you do your nose will fall off." +
            " You have been warned.")
        
        # Triplets of (Name, State, Score)
        self.leaders = []

    @classmethod
    def fromFile(cls, fileName):
        try:
            with open(fileName, 'rb') as f:
                t = pickle.load(f)
        except Exception as e:                
            print "Can't load leaderboard. Starting fresh one."
            t = LeaderBoardData()   # Just return an empty one

        return t

    def write(self, fileName):
        try:
            with open(fileName, 'wb') as f:
                pickle.dump(self, f)
        except Exception as e:
            print "Error saving", e

    def __repr__(self):
        return "Msg: %s\nLeaders: %s" % (self.msg, self.leaders)

class LeaderBoardPhase(GamePhase):
    lbdFileName = 'leaderboard.dat'
    def __init__(self, windowProps, evtSrc, newData):
        self.windowProps = windowProps
        self.evtSrc = evtSrc
        self.maxNScores = 6
        
        self.done = False
        self.newData = newData  

        # newData is (None, state, score). We have to get the name.
        self.newData = newData
        _, state, newScore = newData

        self.foo = True

        self.leaderData = LeaderBoardData.fromFile( LeaderBoardPhase.lbdFileName)

        # Insert new score in the appropriate place
        ldrs = copy.deepcopy(self.leaderData.leaders)

        if self.foo:
            topScore = ldrs[0][2] if len(ldrs) > 0 else 0
            topScore = max(topScore, newScore) + random.randint(50,150)

            d = {'CA': "Superstar", 'WA': "Coby", 'MA': "Wicked"}
            taunt = d.get(state, "Mr. Jones")
            ldrs.insert(0, (taunt, 'XX', topScore))

        nLdrs = len(ldrs)
        i = 0
        while i < nLdrs and ldrs[i][2] >= newScore:
            i += 1

        iNewItem = i

        # Did we make the board?
        self.madeLeaderBoard = iNewItem < self.maxNScores
        #print newScore, self.madeLeaderBoard

        self.iNewItem = iNewItem
        self.newLdrs = newLdrs = copy.deepcopy(ldrs)
        newLdrs.insert(iNewItem, newData)

        newLdrs = newLdrs[0:self.maxNScores]

        # Create the screen objects
        staticLabels = []
        w, h = windowProps.windowWidth, windowProps.windowHeight

        over1 = 190
        over2 = w - 180
        down1 = 80
        yVal = h - 200
        color = (0, 255, 0, 200)
        fontSize = 50

        staticBatch = pyglet.graphics.Batch()
        self.staticBatch = staticBatch

        def makeLabel( x, y, text):
            l = pyglet.text.Label(text=text, 
                font_name='Orbitron',  bold=True, 
                font_size=fontSize,
                x=x, y=y,
                color=color, batch=staticBatch)

            staticLabels.append(l)
            return l

        l = makeLabel(w//2, h-20, "Leader Board")
        l.anchor_x, l.anchor_y = "center", "top"
        l.font_size = fontSize + 12

        for i, item in enumerate(newLdrs):
            name, _, score = item

            l = makeLabel(over1, yVal, str(i+1) + ". ")
            l.anchor_x, l.anchor_y = "right", "bottom"            

            if i == iNewItem:
                inputLocation = (over1+15, yVal)
            else:
                l = makeLabel(over1+15, yVal, name)
                l.anchor_x, l.anchor_y = "left", "bottom"
                
            l = makeLabel(over2, yVal, str(score))
            l.anchor_x, l.anchor_y = "right", "bottom"            

            yVal -= down1

        self.labels = staticLabels

        if self.madeLeaderBoard:
            # Create input entry
            width = over2 - over1 - 320   # 320 estimates width of the scores column
            #print width
            self.textEntry = TextEntryWidget(inputLocation[0], inputLocation[1],width, evtSrc)

        else:
            self.textEntry = None

        self.bottomBatch = pyglet.graphics.Batch()

        instText = "[ Space Bar to start new game - Ctrl-Q to quit ]"

        self.instructions = pyglet.text.Label(text=instText, 
                font_name='Orbitron',  bold=True, 
                font_size=24,
                x=w//2, y=10,
                anchor_x='center', anchor_y='bottom',
                color=color, batch=self.bottomBatch)

        if not self.madeLeaderBoard:
            scoreText = "Your Score: %d" % newScore

            self.scoreLabel = pyglet.text.Label(text=scoreText, 
                    font_name='Orbitron',  bold=True, 
                    font_size=32,
                    x=w//2, y=59,
                    anchor_x='center', anchor_y='bottom',
                    color=color, batch=self.bottomBatch)


        ga = GameAssets.Instance()
        if self.madeLeaderBoard:
            self.done = False
            self.fanfare = ga.getSound('tada')
        else:
            self.done = True
            self.fanfare = ga.getSound('ohno')

    def start(self):
        if Config.Instance().sound():
            self.fanfare.play()

    def update(self, dt, userInput):
        if self.done:
            k = userInput.keys
            if k[key.SPACE]:
                # Start a new game
                #newGe = gameelements.GameElements(self.windowProps)
                #newGe.populateGame( GameAssets.Instance() )

                gp = PlayCountPhase(self.windowProps, self.evtSrc)
                return gp

            return

        if self.textEntry:
            self.textEntry.update(dt)


        if (self.textEntry and 
            self.textEntry.enteredText is not None and 
            self.textEntry.enteredText != ""):

            #print "data entered -%s-" % self.textEntry.enteredText
            t = self.newLdrs[self.iNewItem]
            newT = (self.textEntry.enteredText, t[1], t[2])
            
            self.newLdrs[self.iNewItem] = newT
            if self.foo:
                self.newLdrs.pop(0)
            self.leaderData.leaders = self.newLdrs
            #self.leaders.leaders.append(self.textEntry.enteredText)
            self.leaderData.write(LeaderBoardPhase.lbdFileName)
            self.done = True


        #self.x.update(dt, userInput)

    def draw(self, window):
        #print "draw dbgphase"
        window.clear()
        self.staticBatch.draw()

        if self.done:
            self.bottomBatch.draw()

        if self.textEntry:
            self.textEntry.draw(window)
        #for l in self.labels:
        #    l.draw()

    def delete(self):
        if self.textEntry:
            self.textEntry.delete()


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


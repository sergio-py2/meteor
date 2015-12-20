#!python  -u

import shipsprite
import sprites
from sprites import *

import pyglet


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
        self.timer = Timer(self.props)

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


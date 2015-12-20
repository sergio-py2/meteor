#!python -u

import math

import pyglet


class GameAssets(object):
    """ Loads images, sounds, etc. from files and holds them as pyglet-compatible
        objects. """

    def __init__(self):
        super(GameAssets, self).__init__()

    def loadAssets(self):
        self.images = {}
        self.sounds = {}

        si = self.loadStdImage('spaceship.png', 'ship')
        si.anchor_x = si.width//2
        si.anchor_y = int(si.height * 0.35)

        # Yeah, this is kind of a miscellaneous thing but it makes sense to put
        # it in assets along with the image it's talking about.
        self.shipTipAboveCenter = si.height - si.anchor_y - 10 # there's a border

        fl = self.loadStdImage('spaceship_flames.png', 'flames')
        fl.anchor_x = si.anchor_x
        fl.anchor_y = si.anchor_y

        li = self.loadStdImage('lazer_shot.png', 'shot')
        li.anchor_x = 0
        li.anchor_y = li.height//2

        self.loadStdImage('red.png', 'dbg1')
        self.loadStdImage('green.png', 'dbg2')

        self.loadStdImage('asteroid-1.png', 'asteroid-1')
        self.loadStdImage('asteroid-2.png', 'asteroid-2')
        self.loadStdImage('asteroid-3.png', 'asteroid-3')
        #self.loadStdImage('asteroid1.png', 'asteroid')
        #self.loadStdImage('asteroid1.png', 'asteroid')

        self.loadStdImage('star-med-1.png', 'star-med-1')
        self.loadStdImage('star-med-2.png', 'star-med-2')

        self.loadStdImage('star-lrg-1.png', 'star-lrg-1')
        self.loadStdImage('star-lrg-2.png', 'star-lrg-2')

        self.loadStdImage('star-sml-1.png', 'star-sml-1')
        self.loadStdImage('star-sml-2.png', 'star-sml-2')
        self.loadStdImage('star-sml-3.png', 'star-sml-3')
        self.loadStdImage('star-sml-4.png', 'star-sml-4')
        self.loadStdImage('star-sml-5.png', 'star-sml-5')
        self.loadStdImage('star-sml-6.png', 'star-sml-6')

        self.loadStdImage('image_2400e-Andromeda-Galaxy-b.png', 'galaxy')


        exp = pyglet.resource.image('explosion-anim-1.png')
        nx, ny = 4, 5
        expSeq = pyglet.image.ImageGrid(exp, ny, nx)  # weird x,y ordering is right

        cx = (exp.width//nx)/2
        cy = (exp.height//ny)/2

        # You get to set the anchor point on each grid sub-image independently
        for frame in expSeq:
            frame.anchor_x = cx
            frame.anchor_y = cy

        blastTime = 0.3
        anim = pyglet.image.Animation.from_image_sequence(expSeq, blastTime/(nx*ny), False)
        self.images['explosion'] = anim

        self.loadStdSound('lazer-shot-1.mp3', 'lazer-shot-1')
        #self.pew = pyglet.resource.media('pew4.mp3', streaming=False)
        #self.pew = pyglet.resource.media('pew-js.wma', streaming=False)
        #self.loadStdSound('boom3.mp3', 'boom')
        self.loadStdSound('bomb-explosion-1.mp3', 'bomb-explosion-1')
        self.loadStdSound('wilhelm.mp3', 'wilhelm')
        self.loadStdSound('tada.mp3', 'tada')
        self.loadStdSound('oh_no.mp3', 'ohno')
        #self.loadStdSound('boom3-w-silence.mp3', 'boom3')

        # Get this font by specifying font_name='Orbitron', bold=True
        fontFile = 'Orbitron Bold.ttf'
        pyglet.resource.add_font(fontFile)

    def loadStdSound(self, fileName, tag):
        s = pyglet.resource.media(fileName)
        self.sounds[tag] = pyglet.media.StaticSource(s)
        return s

    def getSound(self, tag):
        return self.sounds[tag]


    def loadStdImage(self, fileName, tag):
        # Loads the image and puts the anchor in the center.
        # You can re-set the center if that default isn't right.
        img = pyglet.resource.image(fileName)
        img.anchor_x = img.width//2
        img.anchor_y = img.height//2
        self.images[tag] = img
        return img

    def getImage(self, tag):
        return self.images[tag]

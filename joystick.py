#!python  -u

import sys

import pyglet
import pyglet.gl as gl
import pyglet.window.mouse as mouse
import pyglet.window.key as key
import pyglet.input

#import pyglet.media

import random
import math
#print pyglet.version

show = ""

# Set up window
full = False
if full:
    window = pyglet.window.Window(fullscreen=True)
else:
    windowW, windowH = 180, 70
    window = pyglet.window.Window(width=windowW, height=windowH)
    window.set_location(20,35)

gJoyStick = None

def update(dt):
    global gJoyStick
    #print "update", dt
    readStick(gJoyStick)
    pass

@window.event
def on_key_press(symbol, modifiers):
    #print "key", symbol
    global shot
    if symbol == key.Q:
        pyglet.app.exit()


def readStick(js):
    #print js
    #print js.device.name
    #print vars(js)
    #for k,v in vars(js).iteritems():
    #    print k, v

    xyz = " x: %f  y: %f  z: %f" % (js.x, js.y, js.z)
    rxyz = "rx: %f ry: %f rz: %f" % (js.rx, js.ry, js.rz)
    hxy = "hx: %f hy: %f" % (js.hat_x, js.hat_y)

    bs = ""
    for i, b in enumerate(js.buttons):
        bs += "b%d: %d " % (i, b)

    if show == 'buttons':
        print bs, "\r",
    else:
        print xyz, rxyz, hxy, "\r",
    #print rxyz
    #print hxy



    for x in js.device.get_controls():
        #print x
        pass


def main():
    global gJoyStick
    global show

    gl.glClearColor(0.0, 0.0, 0.0, 0.0)
    gl.glEnable( gl.GL_BLEND)
    gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)


    #pyglet.clock.set_fps_limit(60)
    pyglet.clock.schedule_interval(update, 1/30.)

    window.set_vsync(True)

    for x in pyglet.input.get_joysticks():
        #readStick(x)
        pass

    gJoyStick = pyglet.input.get_joysticks()[0]
    gJoyStick.open()

    for x in gJoyStick.device.get_controls():
        #print x
        pass

    if len(sys.argv) > 1 and sys.argv[1] == '-b':
        show = 'buttons'
    else:
        show = 'axes'


    pyglet.app.run()
    print ""


if __name__ == '__main__':
    main()


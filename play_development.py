#!python  -u
#!/c/Python27/python.exe  -u

from __future__ import division

import sys

import meteorgame

if len(sys.argv) > 1 and sys.argv[1] == '-f':
    windowOpts = {'fullscreen': True}
else:
    windowOpts = {'width': 1200, 'height': 600}

meteorgame.play(windowOpts)
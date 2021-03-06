#!python

from bbfreeze import Freezer
import shutil
 
destDir = 'dist'

def main():
    #includes = ['requests',  'email.utils']
    includes = ['requests',  'email.utils']
    excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger',
                'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl', 'tk'
                'Tkconstants', 'Tkinter',]
     
    frz = Freezer(destDir, includes=includes, excludes=excludes)
     
    #frz.addScript("meteor.py", gui_only=True)

    frz.addScript("play_development.py")
    frz.addScript("play_fullscreen.py", gui_only=True)
    frz.addScript("play_windowed.py", gui_only=True)
    #frz.addScript("gameassets.py")
    #frz.addScript("geoip.py")
    #frz.addScript("shipsprite.py")
    #frz.addScript("sprites.py")
    #frz.addScript("timevars.py")
    #frz.addScript("vector.py")

     
    frz.use_compression = 0
    frz.include_py = True
    frz()

    addFile('config.json')
    addFile('avbin.dll')

    #addDir('images')
    #addDir('fonts')
    #addDir('sounds')
    addDir('themes')


def addFile(f):
    # Add a non-script file to directory.
    # Why this isn't part of bbfreeze beats me

    # Currently assumes file is in script directory. That's lazy but all 
    # I need for now.
    d = "%s/%s" % (destDir, f)
    shutil.copyfile( f, d)

def addDir(d):
    dd = "%s/%s" % (destDir, d)
    shutil.copytree( d, dd)


main()


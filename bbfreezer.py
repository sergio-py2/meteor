#!python

from bbfreeze import Freezer
import shutil
 
destDir = 'dist4'

def main():
    includes = []
    excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger',
                'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl', 'tk'
                'Tkconstants', 'Tkinter']
     
    frz = Freezer(destDir, includes=includes, excludes=excludes)
     
    #frz.addScript("meteor.py", gui_only=True)
    frz.addScript("meteor.py")
    frz.addScript("meteor_fullscreen.py")
    #frz.addScript("meteor_nosound.py")
    #frz.addScript("meteor_fullscreen_nosound.py")
     
    frz.use_compression = 0
    frz.include_py = True
    frz()

    addFile('config.json')
    addFile('avbin.dll')

    addDir('images')
    addDir('fonts')
    addDir('sounds')


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
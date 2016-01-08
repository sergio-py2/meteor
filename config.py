#!python -u

from singleton import Singleton

@Singleton
class Config(object):
    """ Configuration file. """

    def __init__(self):
        #super(GameAssets, self).__init__()
        pass

    def readFromFile(self, fileName):
        pass

    def sound(self):
        return True

    def tryJoystick(self):
        return False


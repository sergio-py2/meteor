#!python -u

import threading as thrd
import time

#import requests as rq
import urllib2
import xml.etree.ElementTree as et

from singleton import Singleton

@Singleton
class GeoIPData:
    def __init__(self):
        self.state =  None
        self.lat =  None
        self.lng =  None
        self.mapUrl =  None
        self.error =  None
        self.done = False

    def launchFetchThread(self):
        worker = GeoIPFetchThread(self)
        worker.setDaemon(True)
        worker.start()

    def getGeoData(self):
        url1 = 'http://wtfismyip.com/xml'
        yfia = 'your-fucking-ip-address'

        url2 = 'http://www.freegeoip.net/xml/%s'

        #resp1 = rq.get(url1)
        #root1 = et.fromstring(resp1.content)

        resp1 = urllib2.urlopen(url1)
        root1 = et.fromstring(resp1.read())

        #print et.tostring(root)

        ip = root1.find(yfia).text

        #print ip

        tUrl = url2 % ip
        #resp2 = rq.get(tUrl)
        #root2 = et.fromstring(resp2.content)

        resp2 = urllib2.urlopen(tUrl)
        root2 = et.fromstring(resp2.read())

        state = root2.find('RegionCode').text
        lat   = root2.find('Latitude').text
        lng   = root2.find('Longitude').text

        #print et.tostring(root2)

        #print "IP: %s State: %s lat: %s lng: %s" % (ip, state, lat, lng)

        zoom = 13
        mapUrl = 'https://www.google.com/maps/preview/@%s,%s,%dz' % (lat, lng, zoom)
        #print mapUrl


        mapUrl2 =  'http://google.com/maps/?q=%s,%s' % (lat,lng)
        #print mapUrl2

        self.state =  state
        self.lat =  lat
        self.lng =  lng
        self.mapUrl =  mapUrl



class GeoIPFetchThread(thrd.Thread):
    def __init__(self, geoIP):
        thrd.Thread.__init__(self)
        self.geoIP = geoIP

    def run(self):
        #rv = self.returnValueHolder
        #rv['state'] = None
        #rv['lat'] = None
        #rv['lng'] = None
        #rv['mapUrl'] = None
        #rv['error'] = None

        try:
            self.geoIP.getGeoData()
        except Exception as e:
            self.geoIP.error = e

        self.geoIP.done = True


def main():
    info = GeoIPData.Instance()
    info.launchFetchThread()

    while not info.done:
        time.sleep(1.0)

    print vars(info)

if __name__ == '__main__':
    main()


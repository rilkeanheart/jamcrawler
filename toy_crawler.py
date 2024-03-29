#!/usr/bin/env python

"""Web Crawler/Spider

This module implements a web crawler. This is very _basic_ only
and needs to be extended to do anything usefull with the
traversed pages.
"""

import os
import random
import re
import sys
import time
import math
import urllib2
import urlparse
import optparse
from cgi import escape
from traceback import format_exc
from Queue import Queue, Empty as QueueEmpty

from bs4 import BeautifulSoup

__version__ = "0.2"
__copyright__ = "CopyRight (C) 2008-2011 by James Mills"
__license__ = "MIT"
__author__ = "James Mills"
__author_email__ = "James Mills, James dot Mills st dotred dot com dot au"

USAGE = "%prog [options] <url>"
VERSION = "%prog v" + __version__

AGENT = "%s/%s" % (__name__, __version__)


def ADITYA_PRINT(msg):
    print '\nADITYA: %s\n' % msg


class Crawler(object):

    def __init__(self, root, depth, locked=True):
        self.root = root
        ADITYA_PRINT(self.root)
        self.depth = depth
        self.locked = locked
        self.host = urlparse.urlparse(root)[1]
        self.urls = []
        self.links = 0
        self.followed = 0

    def crawl(self):
        page = Fetcher(self.root)
        page.fetch()
        q = Queue()
        for url in page.urls:
            q.put(url)
        followed = [self.root]

        n = 0

        while True:
            try:
                url = q.get()
            except QueueEmpty:
                break

            n += 1

            if url not in followed:
                try:
                    host = urlparse.urlparse(url)[1]
                    if self.locked and re.match(".*%s" % self.host, host):
                        followed.append(url)
                        self.followed += 1
                        page = Fetcher(url)
                        page.fetch()
                        for i, url in enumerate(page):
                            if url not in self.urls:
                                self.links += 1
                                q.put(url)
                                self.urls.append(url)
                        if n > self.depth and self.depth > 0:
                            break
                except Exception, e:
                    print "ERROR: Can't process url '%s' (%s)" % (url, e)
                    print format_exc()

class Fetcher(object):

    def __init__(self, url):
        self.url = url
        self.urls = []

    def __getitem__(self, x):
        return self.urls[x]

    def _addHeaders(self, request):
        request.add_header("User-Agent", AGENT)

    def open(self):
        url = self.url
        try:
            request = urllib2.Request(url)
            handle = urllib2.build_opener()
        except IOError:
            return None
        return (request, handle)

    def fetch(self):
        request, handle = self.open()
        self._addHeaders(request)
        if handle:
            try:
                ADITYA_PRINT("URL: %s" % self.url)
                content = unicode(handle.open(request).read(), "utf-8",
                                  errors="replace")
                soup = BeautifulSoup(content)
                tags = soup('a')
            except urllib2.HTTPError, error:
                if error.code == 404:
                    print >> sys.stderr, "ERROR: %s -> %s" % (error, error.url)
                else:
                    print >> sys.stderr, "ERROR: %s" % error
                tags = []
            except urllib2.URLError, error:
                print >> sys.stderr, "ERROR: %s" % error
                tags = []
            for tag in tags:
                href = tag.get("href")
                if href is not None:
                    url = urlparse.urljoin(self.url, escape(href))
                    if url not in self:
                        self.urls.append(url)

def getLinks(url):
    page = Fetcher(url)
    page.fetch()
    for i, url in enumerate(page):
        print "%d. %s" % (i, url)

def getUrlsInPage(url):
    page = Fetcher(url)
    page.fetch()
    page_urls = [p for p in page]
    print page_urls
    return page_urls

ACCEPTABLE_IMG_EXTENSIONS = ('.jpg', '.png', '.gif')

IMG_STORE_DIR = '/var/tmp/toy_images'

def filterImageUrlsInPage(url):
    urls_in_page = getUrlsInPage(url)
    img_urls = [url for url in urls_in_page if url[-4:] in ACCEPTABLE_IMG_EXTENSIONS]
    print img_urls
    return img_urls

def downloadImage(img_url):
    try:
        imgData = urllib2.urlopen(img_url).read()
        fileName = os.path.basename(urlparse.urlsplit(img_url)[2])
        destFile = os.path.join(IMG_STORE_DIR, fileName)
        output = open(destFile,'wb')
        output.write(imgData)
        output.close()
        print "Stored image file: %s" % destFile
    except Exception as e:
        print 'EXCEPTION while downloading: %s' % e

def getImages(top_level_url, nodelay):
    print '\nTop level URL: %s\n' % top_level_url
    page = Fetcher(top_level_url)
    page.fetch()
    print '\nFetching images from all the pages below:\n'
    for i, url in enumerate(page):
        print "%d. %s" % (i, url)

        if not nodelay:
            wait_mins = random.randint(0, 5)
            print "Wait for %d mins." % wait_mins
            time.sleep(wait_mins * 60)

        img_urls = filterImageUrlsInPage(url)
        for img_url in img_urls:
            downloadImage(img_url)

def parse_options():
    """parse_options() -> opts, args

    Parse any command-line options given returning both
    the parsed options and arguments.
    """

    parser = optparse.OptionParser(usage=USAGE, version=VERSION)

    parser.add_option("-q", "--quiet",
                      action="store_true", default=False, dest="quiet",
                      help="Enable quiet mode")

    parser.add_option("-l", "--links",
                      action="store_true", default=False, dest="links",
                      help="Get links for specified url only")

    parser.add_option("-i", "--images",
                      action="store_true", default=False, dest="images",
                      help="Get images for specified url only")

    parser.add_option("-n", "--nodelay",
                      action="store_true", default=False, dest="nodelay",
                      help="Get images without interim waits.")

    parser.add_option("-d", "--depth",
                      action="store", type="int", default=30, dest="depth",
                      help="Maximum depth to traverse")

    opts, args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        raise SystemExit, 1

    return opts, args

def main():
    opts, args = parse_options()

    url = args[0]

    if opts.links:
        getLinks(url)
        raise SystemExit, 0

    if opts.images:
        getImages(url, opts.nodelay)
        raise SystemExit, 0

    depth = opts.depth

    sTime = time.time()

    print "Crawling %s (Max Depth: %d)" % (url, depth)
    crawler = Crawler(url, depth)
    crawler.crawl()
    print "\n".join(crawler.urls)

    eTime = time.time()
    tTime = eTime - sTime

    print "Found:    %d" % crawler.links
    print "Followed: %d" % crawler.followed
    print "Stats:    (%d/s after %0.2fs)" % (
        int(math.ceil(float(crawler.links) / tTime)), tTime)

if __name__ == "__main__":
    main()

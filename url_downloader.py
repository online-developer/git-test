#!/usr/bin/env python
# encoding=utf-8

from sys import argv
from urllib2 import urlopen, Request

def main():
    url = ''
    filename = url.split('/')[-1]
    with open(filename, 'wb') as f:
        f.write(urlopen(Request(url)).read())

    print 'Wrote %s' %filename


if '__name__' == '__main__':
    main()

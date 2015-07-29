#! /usr/bin/env python

# Copyright 2013 Mdgilbert

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
FOR FINAL PAPER - MAY NOT USE THIS, SEE getCoordinationEdits.py -

This script is intended to grab the details of revisions project members
make during their membership.

Membership is defined as any user who has a link to their user page from a 
project page, sub-page, or template transcluded on either of those pages 
(excluding talk pages).
"""

# Import local tools
from pycommon.util.util import *
from pycommon.db.db import db

# Make sure we're dealing with utf-8 strings
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# Allow threading
import Queue
import threading
import time

# We'll need to grab user links from Wikipedia API
import urllib2
# Need the unquote_plus function
import urllib

# And BeautifulSoup to parse the returned html
from bs4 import BeautifulSoup
# Regular expressions needed to parse user links
import re
# To print the stack trace if we error out
import traceback

# From mako
## THIS IS MAGIC I FOUND ON THE INTERNET
import re, urlparse

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts= urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts))
## END MAGIC

debug = 0
threads = 6
queue = Queue.Queue(threads)
ww = get_ww()
localDb = "reflex_relations_2014"
remoteDb = "enwiki_p_local"

class syncMemberEdits(threading.Thread):
    """ Threaded approach to syncing member edits """

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.ldb = db(localDb, self.getName())
        self.rdb = db(remoteDb, self.getName())

    def run(self):
        """
        Gets all edits project members make, recods them locally
        """

        while True:
            project = self.queue.get()


            # We're done
            out("[%s] Completed inserting member edits" % (project["p_title"]))
            self.queue.task_done()



def main():
    ldb = db(localDb)

    # Spawn a pool of threads
    for i in range(threads):
        m = syncMemberEdits(queue)
        m.setDaemon(True)
        m.start()

    # Fetch the projects we're interested in
    query = 'select * from project where p_title in ("WikiProject_Feminism", "WikiProject_Piracy", "WikiProject_Medicine", "WikiProject_Plants", "WikiProject_Chemistry", "WikiProject_Spoken_Wikipedia", "WikiProject_Countering_systemic_bias", "WikiProject_Copyright_Cleanup", "WikiProject_Missing_encyclopedic_articles", "WikiProject_Outreach")'

    lc = ldb.execute(query)
    rows = lc.fetchall()
    for row in rows:
        queue.put(row)

    # Wait on the queue until everything is done
    queue.join()

    ldb.close()

if __name__ == "__main__":
    main()


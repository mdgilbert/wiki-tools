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

""" To create page_reverts table:
CREATE TABLE `page_reverts` (
  `pr_page_id` int(11) NOT NULL,
  `pr_revert_user` int(11) NOT NULL,
  `pr_revert_rev` int(8) unsigned NOT NULL,
  `pr_revert_timestamp` varbinary(14) NOT NULL,
  `pr_reverted_by_user` int(11) NOT NULL,
  `pr_reverted_by_rev` int(8) unsigned NOT NULL,
  `pr_reverted_by_timestamp` varbinary(14) NOT NULL,
  PRIMARY KEY (`pr_page_id`,`pr_revert_rev`,`pr_reverted_by_rev`),
  KEY `pr_revert_user` (`pr_revert_user`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""

import os,sys,inspect

# Import local tools
from pycommon.util.util import *
from pycommon.db.db import db

# Allow threading
import Queue
import threading
import time
import json

queue = Queue.Queue(10)
chunkSize = 10000
db = db()
localDb = "reflex_relations_2014"
remoteDb = "enwiki_p_local"

ww = get_ww()

class syncReverts(threading.Thread):
    """ Threaded approach to update page reverts """
    lcursor = None
    rcursor1 = None
    rcursor2 = None

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.lcursor = db.getCursorForDB(localDb, self.getName())
        self.rcursor1 = db.getCursorForDB(remoteDb, self.getName())
        self.rcursor2 = db.getCursorForDB(remoteDb, self.getName())
        self.queue = queue

    def run(self):
        while True:
            # Set up our variables
            pages = self.queue.get()
            first_id = pages[0]["tp_id"]
            last_id = pages[-1]["tp_id"]
            min_revert_to = ww

            pp = []
            reverts = []
            values = []
            space = []

            for page in pages:
                if page["tp_revert_to"] < min_revert_to:
                    min_revert_to = page["tp_revert_to"]

            # If min_revert_to is equal to ww-1, we don't need to do anything
            # since the query will search for reverts between them, not inclusive.
            if min_revert_to == ww-1:
                pages = []

            if len(pages):
                # First, get all the revisions for these (up to) 200 pages that occurred more than once
                out("%s - Fetching reverted checksums for page ids %s to %s" % (self.getName(), first_id, last_id))
                query = "SELECT COUNT(rev_sha1) AS 'count', rev_sha1, MIN(rev_id) as 'min', MAX(rev_id) AS 'max', rev_page FROM revision WHERE rev_page IN (" + ",".join([str(v["tp_id"]) for v in pages]) + ") AND TIMESTAMPDIFF(WEEK, '20010101000000', rev_timestamp) > %s AND TIMESTAMPDIFF(WEEK, '20010101000000', rev_timestamp) < %s GROUP BY rev_sha1, rev_page HAVING COUNT(rev_sha1) > 1"
                self.rcursor1 = db.execute(self.rcursor1, query, (min_revert_to, ww))
                out("%s - Finished fetching reverted checksums" % (self.getName()))

                out("%s - Fetching revision span between reverts" % (self.getName()))
                # Then, go through each of the sha's, identify what was reverted by whom
                while True:
                    shas = self.rcursor1.fetchmany(1000)
                    if not shas:
                        break
                    for sha in shas:
                        #out("%s - Fetching span of reverted revisions" % (self.getName()))
                        query = "SELECT rev_id, rev_user, rev_user_text, rev_timestamp, rev_sha1 FROM revision WHERE rev_page = %s AND rev_id >= %s AND rev_id <= %s ORDER BY rev_id ASC"
                        self.rcursor2 = db.execute(self.rcursor2, query, (sha['rev_page'], sha['min'], sha['max']))
                        #out("%s - Finished fetching span of reverted revisions" % (self.getName()))
                        revs = self.rcursor2.fetchall()
                        reverted = [] # array of tuples, (reverted_user_id, reverted_user_rev, reverted_user_timestamp)

                        for rev in revs:
                            # If this is the reverted_to sha and not the min rev, add to reverts array
                            if rev['rev_id'] != sha['min'] and rev['rev_sha1'] == sha['rev_sha1']:
                                for r in reverted:
                                    reverts.append( (sha['rev_page'], r[0], r[1], r[2], rev['rev_user'], rev['rev_id'], rev['rev_timestamp']) )
                                reverted = []

                            # Otherwise, if we're not the min rev, add to reverted array
                            # (this is a change that will be reverted)
                            elif rev['rev_id'] != sha['min']:
                                reverted.append( (rev['rev_user'], rev['rev_id'], rev['rev_timestamp']) )

                            # Skip the min rev
                            # (this is the revision that all others were reverted to, currently not stored)
                            else:
                                pass

                out("%s - Finished fetching revision span" % (self.getName()))

                # Insert reverts for this page, 10,000 at a time
                #out("%s - Checking for reverts to be inserted." % (self.getName()))
                totalReverts = len(reverts)
                while len(reverts) > 0:
                    values = []
                    space = []
                    for i in range(10000):
                        if len(reverts) > 0:
                            r = reverts.pop()
                            space.append("(%s,%s,%s,%s,%s,%s,%s)")
                            values += [ r[0], r[1], r[2], r[3], r[4], r[5], r[6] ]
                        else:
                            break

                    query = "INSERT INTO page_reverts VALUES " + ','.join(space) + " ON DUPLICATE KEY UPDATE pr_page_id = pr_page_id"
                    self.lcursor = db.execute(self.lcursor, query, values=values)

                if totalReverts:
                    out("%s - Inserted %s reverts for page ids %s to %s" % (self.getName(), totalReverts, first_id, last_id))

            # Finally, update the local revert_to value for these pages
            query = "UPDATE ts_pages SET tp_revert_to = %s WHERE tp_id >= %s AND tp_id <= %s"
            self.lcursor = db.execute(self.lcursor, query, (ww-1, first_id, last_id))

            # Done with this chunk
            self.queue.task_done()

def main():
    # Add all our pages to the queue
    out("Running syncReverts.py\n\n")
    lc = db.getCursorForDB(localDb)

    #out("Fetching pages from local DB and spooling queue")
    #query = "SELECT tp_id, tp_namespace, tp_title, tp_revert_to FROM ts_pages ORDER BY tp_id ASC"
    #lcursor = db.execute(lcursor, query)

    # Spawn a pool of threads
    for i in range(10):
        u = syncReverts(queue)
        u.setDaemon(True)
        u.start()

    # Get the total number of pages we need to fetch reverts for)
    lc = db.execute(lc, "SELECT COUNT(tp_id) AS 'count' FROM ts_pages WHERE tp_revert_to < %s" % (ww-1))
    row = lc.fetchall()
    todo = row[0]["count"]
    done = 0

    # Keep fetching pages until we get them all (skip everything that's already synced to last week (ww-1),
    # since it's done, and the current week is obviously not over yet so would need to be updated /next/ week...
    i = 0
    chunk = 500
    while True:
        lc = db.execute(lc, "SELECT tp_id, tp_revert_to FROM ts_pages WHERE tp_id >= %s and tp_id < %s AND tp_revert_to < %s ORDER BY tp_id ASC" % (i * 500, (i * 500) + 500, ww-1))
        i += 1
        pages = lc.fetchall()
        done += len(pages)
        if done > 0:
            out("Fetching page ids from %s to %s (%s of %s completed)." % (i * 500, (i * 500) + 500, done, todo))
        if not pages and todo == done:
            break
        elif not pages:
            continue
        queue.put(pages)

    # Wait on the queue until everything is done
    queue.join()

    lc.close()
    out("\nsyncReverts.py run complete.\n");


if __name__ == "__main__":
    main()


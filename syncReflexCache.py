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

""" Local reflex_cache table:
CREATE TABLE `reflex_cache` (
  `rc_user_id` bigint(20) NOT NULL,
  `rc_page_id` int(11) NOT NULL,
  `rc_page_namespace` int(11) NOT NULL,
  `rc_edits` mediumint(9) NOT NULL,
  `rc_wikiweek` smallint(6) NOT NULL,
  PRIMARY KEY (`rc_user_id`,`rc_page_id`,`rc_wikiweek`),
  KEY `rc_page_id` (`rc_page_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""

# Import local tools
from pycommon.util.util import *
from pycommon.db.db import db

# Allow threading
import Queue
import threading
import time

threads = 5
queue = Queue.Queue(threads)
ww = get_ww()
out("Current week is %s, will cache everything up to (not including) this week" % (ww, ))
localDb  = 'reflex_relations_2014'
remoteDb = 'enwiki_p_local'

class syncReflexCache(threading.Thread):
    """ Threaded approach to update the reflex_cache """

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.ldb = db(localDb, self.getName())
        self.rdb = db(remoteDb, self.getName())
        self.queue = queue

    def run(self):
        totalAnon=0
        totalCache=0

        while True:
            # Grab the page from the queue
            pages = self.queue.get()
            first_id = pages[0]["tp_id"]
            last_id = pages[-1]["tp_id"]
            min_cached_to = ww

            values = []
            space  = []
            anonValues = []
            anonSpace  = []

            for page in pages:
                if page['tp_cached_to'] < min_cached_to:
                    min_cached_to = page['tp_cached_to']

            # If min_cached_to is equal to ww-1, we don't need to do anything,
            # since the query will search for edits between them, not inclusive.
            if min_cached_to == ww-1:
                pages = []

            if len(pages):
                # Fetch data for 200 pages at once
                # was ",".join(map(str,pp))
                query = "SELECT rev_page, rev_user, rev_user_text, rev_timestamp, page_namespace, COUNT(rev_user) AS 'count', TIMESTAMPDIFF(WEEK, '20010101000000', rev_timestamp) AS 'wikiweek' FROM revision JOIN page ON rev_page = page_id WHERE rev_page IN (" + ",".join([str(v["tp_id"]) for v in pages]) + ") AND TIMESTAMPDIFF(WEEK, '20010101000000', rev_timestamp) > %s AND TIMESTAMPDIFF(WEEK, '20010101000000', rev_timestamp) < %s GROUP BY wikiweek, rev_user_text, rev_page"

                rc = self.rdb.execute(query, (min_cached_to, ww))

                # Collect revisions, 20000 at a time
                while True:
                    revs = rc.fetchmany(10000)

                    if not revs:
                        break

                    #out("%s - Fetched another (up to) 10,000 rows" % (self.getName()))

                    for rev in revs:
                        i = rev['rev_user']

                        # A few users are NULL, we won't be able to distinguish between them (not in users)
                        if rev['rev_user'] == None:
                            i = 0

                        if rev['rev_user'] == 0:
                            i = ipv4_to_int(rev['rev_user_text'])
                            # if this was a 0 id that's not an ip, we'll add it to the cache, 
                            # but it won't be in the user table
                            if i != 0:
                                # Anon ids will all be negative
                                i = i - i*2
                                anonSpace.append("(%s,%s,%s)")
                                anonValues += [ str(i), str(rev['rev_user_text']), str(rev['rev_timestamp']) ]

                        space.append("(%s,%s,%s,%s,%s)")
                        values += [ str(i), str(rev['rev_page']), str(rev['page_namespace']), str(rev['count']), str(rev['wikiweek']) ]

                        # Incrementally add anon users or cache rows if we've passed 1,000 rows
                        if len(anonSpace) >= 1000:
                            self.insertAnon(anonValues, anonSpace)
                            totalAnon += len(anonSpace)
                            anonSpace = []
                            anonValues = []
                        if len(space) >= 1000:
                            self.insertCache(values, space)
                            totalCache += len(space)
                            space = []
                            values = []

            else:
                # This could happen if these pages have already been added, nothing to do
                pass

            ## Finally, add anon users and cache rows if there are any left
            if len(anonSpace):
                self.insertAnon(anonValues, anonSpace)
                totalAnon += len(anonSpace)
            if len(values):
                self.insertCache(values, space)
                totalCache += len(space)

            # And update the local db cached_to values for these pages
            query = "UPDATE ts_pages SET tp_cached_to = %s WHERE tp_id >= %s AND tp_id <= %s"
            #out("Running: UPDATE ts_pages SET tp_cached_to = %s WHERE tp_id >= %s AND tp_id <= %s" % (ww-1, first_id, last_id))
            lc = self.ldb.execute(query, (ww-1, first_id, last_id))

            out("%s - Inserted: %s cache, %s anon. Pages: %s to %s. Weeks: [%s to %s]." % (self.getName(), str(totalCache), str(totalAnon), first_id, last_id, str(min_cached_to), str(ww-1)))

            # Done with this chunk
            self.queue.task_done()


    def insertAnon(self, values, space):
        #out("%s - Inserting %s anonymous users." % (self.getName(), str(len(space))))
        query = 'INSERT INTO ts_users (tu_id, tu_name, tu_registration) VALUES ' + ','.join(space) + ' ON DUPLICATE KEY UPDATE tu_id = tu_id'
        lc = self.ldb.execute(query, values)

    def insertCache(self, values, space):
        query = 'INSERT INTO reflex_cache (rc_user_id, rc_page_id, rc_page_namespace, rc_edits, rc_wikiweek) VALUES ' + ','.join(space) + ' ON DUPLICATE KEY UPDATE rc_edits = VALUES(rc_edits)'
        lc = self.ldb.execute(query, values)

def main():

    # Fetch a list of all pages, chunk out to individual threads (this is, so far as I can tell, the
    # only way to do this without timing out)
    out("Running syncReflexCache.py\n\n")
    ldb = db(localDb)

    # Spawn a pool of threads
    for i in range(threads):
        u = syncReflexCache(queue)
        u.setDaemon(True)
        u.start()

    # Get the total number of pages we need to cache
    lc = ldb.execute("SELECT COUNT(tp_id) AS 'count' FROM ts_pages WHERE tp_cached_to < %s" % (ww-1))
    row = lc.fetchall()
    todo = row[0]["count"]
    done = 0    

    # Keep fetching pages until we get them all (skip everything that's already synced to last week (ww-1),
    # since it's done, and the current week is obviously not over yet so would need to be updated /next/ week...
    i = 0
    chunk = 500
    while True:
        lc = ldb.execute("SELECT tp_id, tp_cached_to FROM ts_pages WHERE tp_id >= %s AND tp_id < %s AND tp_cached_to < %s ORDER BY tp_id ASC" % (i * 500, (i * 500) + 500, ww-1))
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

    ldb.close()
    out("\nsyncReflexCache.py run complete.\n");    

if __name__ == "__main__":
    main()



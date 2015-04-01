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

""" Local pages table:
CREATE TABLE `ts_pages` (
  `tp_id` int(8) NOT NULL DEFAULT '0',
  `tp_title` varbinary(255) NOT NULL DEFAULT '',
  `tp_namespace` int(11) NOT NULL DEFAULT '0',
  `tp_is_redirect` tinyint(1) NOT NULL DEFAULT '0',
  `tp_cached_to` smallint(5) unsigned NOT NULL DEFAULT '0',
  `tp_revert_to` smallint(5) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`tp_id`),
  KEY `tp_title` (`tp_title`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""


# Import local tools
from pycommon.util.util import *
from pycommon.db.db import db

# Allow threading
import Queue
import threading
import time

queue = Queue.Queue(10)
chunkSize = 10000
localDb = "reflex_relations_2014"
remoteDb = "enwiki_p_local"

class syncPages(threading.Thread):
    """ Threaded approach to updating pages """

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.rdb = db(remoteDb, self.getName())
        self.ldb = db(localDb, self.getName())

    def run(self):
        while True:
            # Grab the chunk from the queue
            chunk = self.queue.get()

            # Fetch the data
            out("%s - Fetching pages between %s -> %s" % (self.getName(), chunk*chunkSize, (chunk*chunkSize)+chunkSize))
            query = """ SELECT page_id, page_title, page_namespace, page_is_redirect FROM page WHERE page_id > %s ORDER BY page_id ASC LIMIT %s """ % (chunk*chunkSize, chunkSize)
            rc = self.rdb.execute(query)
            rows = rc.fetchall()

            # Format the data
            space = []
            values = []
            for r in rows:
                space.append("(%s,%s,%s,%s)")
                values += [str(r['page_id']), r['page_title'], str(r['page_namespace']), str(r['page_is_redirect'])]

            # Insert the data
            out("%s - Inserting pages between %s -> %s" % (self.getName(), chunk*chunkSize, (chunk*chunkSize)+chunkSize))
            query = "INSERT INTO ts_pages (tp_id, tp_title, tp_namespace, tp_is_redirect) VALUES %s ON DUPLICATE KEY UPDATE tp_id=tp_id" % (','.join(space))
            lc = self.ldb.execute(query, values)

            # When processing is complete, signal to queue the job is done
            self.queue.task_done()

def main():
    # Fetch the last local page that was added
    ldb = db(localDb)
    query = "SELECT tp_id FROM ts_pages ORDER BY tp_id DESC LIMIT 1"
    lc = ldb.execute(query)
    start = 0
    row = lc.fetchone()
    if row:
        start = row['tp_id']
    ldb.close()

    # Fetch the last remote page that was created (on the toolserver)
    rdb = db(remoteDb)
    query = "SELECT page_id FROM page ORDER BY page_id DESC LIMIT 1"
    rc = rdb.execute(query)
    end = 60000000
    row = rc.fetchone()
    if row:
        end = row['page_id']
    rdb.close()

    # Spawn a pool of threads
    for i in range(10):
        u = syncPages(queue)
        u.setDaemon(True)
        u.start()

    # Populate queue with data
    s = start / chunkSize
    e = end / chunkSize
    while s <= e:
        queue.put(s)
        s += 1

    # Wait on the queue until everything is done
    queue.join()

    out("Completed syncPages.py run.")


if __name__ == "__main__":
    main()


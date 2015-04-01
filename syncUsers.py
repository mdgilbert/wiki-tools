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

""" Local users table:
CREATE TABLE `ts_users` (
  `tu_id` bigint(20) NOT NULL DEFAULT '0',
  `tu_name` varbinary(255) NOT NULL DEFAULT '',
  `tu_registration` varbinary(14) DEFAULT NULL,
  `tu_aka` varbinary(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`tu_id`),
  KEY `tu_name` (`tu_name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""

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
localDb = "reflex_relations_2014"
remoteDb= "enwiki_p_local"

class syncUsers(threading.Thread):
    """ Threaded approach to updating users """

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
            out("%s - Fetching users between %s -> %s" % (self.getName(), chunk*chunkSize, (chunk*chunkSize)+chunkSize))
            query = """ SELECT user_id, user_name, user_registration FROM user WHERE user_id > %s ORDER BY user_id ASC LIMIT %s """ % (chunk*chunkSize, chunkSize)
            rc = self.rdb.execute(query)
            rows = rc.fetchall()

            # Format the data
            space = []
            values = []
            for r in rows:
                space.append("(%s,%s,%s)")
                values += [str(r['user_id']), r['user_name'], str(r['user_registration'])]

            # Insert the data
            out("%s - Inserting users between %s -> %s" % (self.getName(), chunk*chunkSize, (chunk*chunkSize)+chunkSize))
            query = "INSERT INTO ts_users (tu_id, tu_name, tu_registration) VALUES %s ON DUPLICATE KEY UPDATE tu_id=tu_id" % (','.join(space))
            lc = self.ldb.execute(query, values)

            # When processing is complete, signal to queue the job is done
            self.queue.task_done()

def main():
    # Fetch the last local user that was added
    ldb = db(localDb)
    query = "SELECT tu_id FROM ts_users ORDER BY tu_id DESC LIMIT 1"
    lc = ldb.execute(query)
    start = 0
    row = lc.fetchone()
    if row:
        start = row['tu_id']

    # Fetch the last remote user that was added (on the toolserver)
    rdb = db(remoteDb)
    query = "SELECT user_id FROM user ORDER BY user_id DESC LIMIT 1"
    rc = rdb.execute(query)
    end = 30000000
    row = rc.fetchone()
    if row:
        end = row['user_id']

    # Spawn a pool of threads
    for i in range(10):
        u = syncUsers(queue)
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

    # Finally, update any users who have redirect pages
    out("\n\n")
    out("Updating redirect users.")
    #query = "SELECT u1.user_id AS 'user_id_to', u2.user_id AS 'user_id_from', p1.page_id AS 'page_id_to', p2.page_id AS 'page_id_from', REPLACE(rd_title, '_', ' ') AS 'redirect_to', REPLACE(p2.page_title, '_', ' ') AS 'redirect_from' FROM redirect JOIN page p1 ON p1.page_title = rd_title AND page_namespace = 2 JOIN page p2 ON p2.page_id = rd_from JOIN user u1 ON REPLACE(rd_title, '_', ' ') = u1.user_name LEFT JOIN user u2 ON REPLACE(p2.page_title, '_', ' ') = u2.user_name  WHERE rd_namespace = 2 AND p2.page_title NOT LIKE '%%/%%' GROUP BY redirect_from"
    query = "SELECT u1.user_id AS 'user_id_to', u2.user_id AS 'user_id_from', r.rd_title AS 'redirect_to', p.page_title AS 'redirect_from' FROM redirect r JOIN page p ON r.rd_from = p.page_id LEFT JOIN user u1 ON u1.user_name = REPLACE(r.rd_title, '_', ' ') LEFT JOIN user u2 ON u2.user_name = REPLACE(p.page_title, '_', ' ') WHERE rd_namespace = 2 AND r.rd_title NOT LIKE '%%/%%' AND p.page_title NOT LIKE '%%/%%'"
    rc = rdb.execute(query)
    rows = rc.fetchall()
    space = []
    values = []
    for r in rows:
        # It's possible that this user still has an ID.  If that's the case, use that one
        id_to = str(r['user_id_to'])
        if r['user_id_from']:
            id_to = str(r['user_id_from'])
        # There are also IP addresses in the redirect table with NULL ids, skip them.
        if not id_to or id_to == "None":
            continue
        space.append("(%s,%s,%s)")
        values += [id_to, r['redirect_from'], r['redirect_to']]

        # Insert every 1000 users
        if len(space) >= 1000:
            out("Inserting %s redirect users." % (len(space)))
            query = "INSERT INTO ts_users (tu_id, tu_name, tu_aka) VALUES %s ON DUPLICATE KEY UPDATE tu_id = tu_id" % (','.join(space))
            lc = ldb.execute(query, values)
            space = []
            values = []

    # If there's any values left, insert them as well
    if len(space) > 0:
        out("Inserting %s redirect users." % (len(space)))
        query = "INSERT INTO ts_users (tu_id, tu_name, tu_aka) VALUES %s ON DUPLICATE KEY UPDATE tu_id = tu_id" % (','.join(space))
        lc = ldb.execute(query, values)


    ldb.close()
    rdb.close()
    out("Finished syncUsers.py run.")


if __name__ == "__main__":
    main()

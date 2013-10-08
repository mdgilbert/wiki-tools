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

from uw_db import uw_db

# Allow threading
import Queue
import threading
import time
import sys

queue = Queue.Queue(8)

class updateReverts(threading.Thread):
    """ Updates reverts to pages """

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):

        db = uw_db()
        ldb = uw_db()
        while True:
            c1 = db.getCursorForDB("enwiki_p", self.getName())
            c2 = db.getCursorForDB("enwiki_p", self.getName())
            l1 = ldb.getCursorForDB("reflex_relations", self.getName())

            page = self.queue.get()
            reverts = [] # array of tuples to add to n_page_reverts table

            # Possible TODO: check here for the latest reverted revision in the local db to limit revs we go through
            # First grab the sums which appear for this page more than once
            # Fetching: 0 - count, 1 - sha, 2 - min, 3 - max
            print "%s - Fetching reverted checksums for page %s, id %s" % (self.getName(), page[2], page[0])
            query = "SELECT COUNT(rev_sha1) as 'count', rev_sha1, MIN(rev_id) AS 'min', MAX(rev_id) AS 'max' FROM revision WHERE rev_page = %s GROUP BY rev_sha1 HAVING COUNT(rev_sha1) > 1"
            db.execute(c1, query, (page[0], ))
            while True:
                shas = c1.fetchmany(1000)
                if not shas:
                    break
                # Go through each of the revisions, identify what was reverted by whom
                for sha in shas:
                    query = "SELECT rev_id, rev_user, rev_user_text, rev_timestamp, rev_sha1 FROM revision WHERE rev_page = %s AND rev_id >= %s AND rev_id <= %s ORDER BY rev_id ASC"
                    db.execute(c2, query, (page[0], sha[2], sha[3]))
                    revs = c2.fetchall()
                    reverted = [] # array of tuples, (reverted_user_id, reverted_user_rev, reverted_user_timestamp)

                    for rev in revs:
                        # If this is the reverted_to sha and not the min rev, add to reverts array
                        if rev[0] != sha[2] and rev[4] == sha[1]:
                            for r in reverted:
                                reverts.append( (page[0], r[0], r[1], r[2], rev[1], rev[0], rev[3]) )
                            reverted = []

                        # Otherwise, if we're not the min rev, add to reverted array (this is a change that will be reverted)
                        elif rev[0] != sha[2]:
                            reverted.append( (rev[1], rev[0], rev[3]) )
                        # Skip the min rev (this is the revision that all others were reverted to, currently not stored)
                        else:
                            pass

                    # Insert reverts for this sha
                    #l1.executemany("INSERT INTO n_page_reverts VALUES (%s,%s,%s,%s,%s,%s,%s)", reverts)

            # Insert reverts for this page, 10000 at a time
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

                print "%s - Inserting %s reverts for page %s, id %s" % (self.getName(), str(len(space)), page[2], page[0])
                query = "INSERT INTO n_page_reverts VALUES " + ','.join(space) + " ON DUPLICATE KEY UPDATE pr_page_id = pr_page_id"
                ldb.execute(l1, query, values = values)

            c1.close()
            c2.close()
            l1.close()
            self.queue.task_done()

def main():

    # Setup the DB connection for the main thread
    db = uw_db()
    cursor = db.getCursorForDB("enwiki_p", "this")

    # Spawn a pool of threads
    for i in range(8):
        u = updateReverts(queue)
        u.setDaemon(True)
        u.start()

    # TODO: use the history module to improve concurrent runs

    # Load the pages we're going through
    #query = "SELECT page_id, page_namespace, page_title FROM page WHERE page_id = 22419013 AND page_namespace = 0 ORDER BY page_id ASC"
    #query = "SELECT page_id, page_namespace, page_title FROM page ORDER BY page_id ASC"
    inc = 0
    while True:
        query = "SELECT page_id, page_namespace, page_title FROM page WHERE page_id > 3550300 ORDER BY page_id ASC LIMIT %s,1000" % (inc*1000,)
        db.execute(cursor, query)
        pages = cursor.fetchall()
        if not pages:
            break

        # Populate the queue (the max limit given on queue initialization should block until there is space in the queue)
        for page in pages:
            queue.put(page)

        inc += 1

    # Wait on the queue until everything is finished
    queue.join()

if __name__ == "__main__":
    main()



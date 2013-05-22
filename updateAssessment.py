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

import wiki_categories
import wiki_projects
import wiki_history
from uw_db import uw_db

# Allow threading
import Queue
import threading
import time
import sys

queue = Queue.Queue(3)
history = wiki_history.localHistory("assessment")

class updateAssessments(threading.Thread):
    """ Threaded approach to updating article assessments """

    cursor = None
    category = None

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get the assessmet we're fetching
            qual = self.queue.get()
            self.category = qual

            print "%s - Looking up articles with category: %s." % (self.getName(), qual)
            wiki_categories.wikiCat().getPagesInCategory(qual, callback = self.insertAssessments, thread = self.getName(), includeTitle = True)

            print "%s - Finished loading pages with category: %s." % (self.getName(), qual)
            self.queue.task_done()
            history.setComplete(qual, thread = self.getName())

    def insertAssessments(self, pages, id):
        db = uw_db()
        self.cursor = db.getCursorForDB("reflex_relations", self.getName())

        # Pages returned will be identified by the talk page id.  We need to add in the
        # article page id to the local db.
        # ie, insert into n_page_assessments (pa_id, pa_assessment) values ( (select tp_id from ts_pages where tp_title = "AC/DC" AND tp_namespace = 0), "featured");
        values = []
        space = []
        for p in pages:
            space.append(" tp_title = %s ")
            values.append(p[3].decode("utf-8", "replace"))
        #self.cursor.execute('SELECT tp_id, tp_title FROM ts_pages WHERE tp_namespace = 0 AND (' + ' OR '.join(space) + ')', values)
        query = 'SELECT tp_id, tp_title FROM ts_pages WHERE tp_namespace = 0 AND (' + ' OR '.join(space) + ')'
        db.execute(self.cursor, query, values)
        rows = self.cursor.fetchall()
        lookup = {}
        for row in rows:
            lookup[row[1]] = row[0]

        # Prep the insert array
        values = []
        space = []
        for p in pages:
            if p[3] in lookup:
                try:
                    #values += [lookup[p[3].decode("utf-8", "replace")], p[1].decode("utf-8", "replace")]
                    values += [lookup[p[3]], self.category]
                except:
                    print "Error with first or second value: " + p[3]
                    print "Error with second value: " + self.category
                    print "Error: ", str(sys.exc_info()[0])
                    raise
            else:
                #values += [0, p[1].decode("utf-8", "replace")]
                values += [0, self.category]
            space.append("(%s,%s)")

        if len(pages):
            print "%s - Inserting %s pages with assessment: %s." % (self.getName(), str(len(pages)), self.category)
            query = 'INSERT INTO n_page_assessments (pa_id, pa_assessment) VALUES ' + ','.join(space) + ' ON DUPLICATE KEY UPDATE pa_id = pa_id'
            db.execute(self.cursor, query, values = values)

        self.cursor.close()

def main():
    # Clear out the old data

    # Clear the history
    history.clearHistory(keepDays = 30).getHistory()

    # Spawn a pool of threads
    for i in range(3):
        u = updateAssessments(queue)
        u.setDaemon(True)
        u.start()

    # Populate queue with data
    for assessment in ["Wikipedia_featured_articles", "Wikipedia_good_articles", "Wikipedia_stubs", "Stub_categories"]:
        if not history.isComplete(assessment):
            queue.put(assessment)
        else:
            print "Skipping assessment category: " + assessment

    # Wait on the queue until everything is finished
    queue.join()

main()



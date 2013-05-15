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
from uw_db import uw_db

# Allow threading
import Queue
import threading
import time

queue = Queue.Queue(10)

class updateAssessments(threading.Thread):
    """ Threaded approach to updating article assessments """

    cursor = None

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get the assessmet we're fetching
            qual = self.queue.get()

            print "%s - Looking up articles with category: %s." % (self.getName(), qual)
            wiki_categories.wikiCat().getPagesInCategory(qual, callback = self.insertAssessments, includeTitle = True)

            print "%s - Finished loading pages with category: %s." % (self.getName(), qual)
            self.queue.task_done()

    def insertAssessments(self, pages, id):
            self.cursor = uw_db().getCursorForDB("reflex_relations", self.getName())

            # Pages returned will be identified by the talk page id.  We need to add in the
            # article page id to the local db.
            # ie, insert into n_page_assessments (pa_id, pa_assessment) values ( (select tp_id from ts_pages where tp_title = "AC/DC" AND tp_namespace = 0), "featured");

            # Prep the insert array
            values = []
            space = []
            for p in pages:
                values += ["(SELECT tp_id FROM ts_pages WHERE tp_title = '%s' AND tp_namespace = 0)" % p[3], unicode(p[1])]
                space.append("(%s,%s)")

            if len(pages):
                print "%s - Inserting %s pages with assessment: %s." % (self.getName(), str(len(pages)), qual)
                self.cursor.execute('INSERT INTO n_page_assessments (pa_id, pa_assessment) VALUES ' + ','.join(space) + ' ON DUPLICATE KEY UPDATE pa_id = pa_id', values)

            self.cursor.close()

def main():
    # Clear out the old data

    # Spawn a pool of threads
    for i in range(3):
        u = updateAssessments(queue)
        u.setDaemon(True)
        u.start()

    # Populate queue with data
    for assessment in ["Wikipedia_featured_articles", "Wikipedia_good_articles", "Wikipedia_stubs", "Stub_categories"]:
        queue.put(assessment)

    # Wait on the queue until everything is finished
    queue.join()

main()



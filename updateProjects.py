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

class updateProjects(threading.Thread):
    """ Threaded approach to updating projects """
    cursor = None
    project = None

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Grab the project from the queue
            project = self.queue.get()
            self.project = project[1]

            print "%s - [%s] Getting pages for project: %s" % (self.getName(), self.project, project[1])
            wiki_projects.wikiProj().getProjectPages(project[1], callback = self.insertPages, id = project[0], thread = self.getName())

            # When processing is complete, signal to queue the job is done
            print "%s - [%s] Finished getting pages for project: %s" % (self.getName(), self.project, project[1])
            self.queue.task_done()

    def insertPages(self, pages, id):
        self.cursor = uw_db().getCursorForDB("reflex_relations", self.getName())

        values = []
        space = []
        for p in pages:
            values += [str(p[0]), str(id), unicode(p[1]), str(p[2])]
            space.append("(%s,%s,%s,%s)")

        # Insert the pages
        if len(pages):
            print "%s - [%s] Inserting %s pages." % (self.getName(), self.project, str( len(pages) ))
            self.cursor.execute('INSERT INTO n_project_pages (pp_id, pp_project_id, pp_parent_category, pp_parent_category_id) VALUES ' + ','.join(space) + ' ON DUPLICATE KEY UPDATE pp_id = pp_id', values)

        self.cursor.close()

start = time.time()
def main():
    # Clear old data from the tables
    #print "Clearing previous project and page data."
    #wiki_projects.localProj().clearProjects()

    # Load all the projects from the Toolserver
    #print "Fetching project data"
    #projects = wiki_projects.wikiProj().getProjects()

    projects = wiki_projects.localProj().getProjects()
    print "Loaded " + str( len(projects) ) + " projects."

    # Insert all the projects
    #print "Inserting %s projects" % (str(len(projects)),)
    #wiki_projects.localProj().insertProjects(projects)

    # Spawn a pool of threads
    for i in range(10):
        u = updateProjects(queue)
        u.setDaemon(True)
        u.start()

    # Populate queue with data
    for project in projects:
        queue.put(project)

    # Wait on the queue until everything is finished
    queue.join()

main()


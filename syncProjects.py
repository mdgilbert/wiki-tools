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

""" Project table:
CREATE TABLE `project` (
  `p_id` int(11) NOT NULL,
  `p_title` varbinary(255) NOT NULL,
  `p_created` varbinary(14) DEFAULT NULL,
  PRIMARY KEY (`p_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""
""" Project pages table:
CREATE TABLE `project_pages` (
  `pp_id` int(11) NOT NULL,
  `pp_project_id` int(11) NOT NULL,
  `pp_parent_category` varbinary(255) NOT NULL,
  `pp_parent_category_id` int(11) NOT NULL,
  PRIMARY KEY (`pp_id`,`pp_project_id`)
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

class syncProjects(threading.Thread):
    """ Threaded approach to updating project pages """
    lcursor = None
    rcursor = None
    project = ""

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.rdb = db(remoteDb, self.getName())
        self.ldb = db(localDb, self.getName())

    def run(self):
        while True:
            # Grab our project from the queue
            project = self.queue.get()
            p_id    = project[0]
            p_name  = project[1]
            self.project = p_name

            # Get the project pages
            out("%s - Fetching pages for project: %s" % (self.getName(), p_name))
            self.getPagesInCategory(p_name, p_id, depth=1)

            # When processing is complete, signal to queue the job is done
            out("%s - Finished inserting pages for project: %s" % (self.getName(), p_name))
            self.queue.task_done()

    def getPagesInCategory(self, category, cat_id, depth=4):
        """
        Returns pages in a given category
        Inputs:
            category - the category we want to get pages for
            depth - the amount of subcategories we will traverse.  Set to -1 for no limit (probably a bad idea?)
        Returns:
            Nuffing.
        """
        pages = ()

        # Get basic category information
        query = 'SELECT cat_id, cat_title, cat_pages, cat_subcats FROM category WHERE category.cat_title = %s'
        rc = self.rdb.execute(query, (category,))
        parent = rc.fetchone()
        if parent:
            # Get the sub-pages
            query = 'SELECT cl_from as "page_id", %s as "parent_category", %s as "parent_category_id" FROM categorylinks WHERE cl_to = %s'
            rc = self.rdb.execute(query, (parent['cat_title'], parent['cat_id'], category))

            # Insert sub-pages by bucket
            while True:
                pages = rc.fetchmany(10000)
                if not pages:
                    break
                self.insertPages(pages, cat_id)

            # If this category has sub-categories, append all their pages as well
            if parent['cat_subcats'] > 0 and depth != 0:
                query = 'SELECT page.page_title as "parent_category" FROM categorylinks INNER JOIN page ON page.page_id = categorylinks.cl_from WHERE categorylinks.cl_to = %s AND page.page_namespace = 14'
                rc = self.rdb.execute(query, (parent['cat_title'],))
                subcats = rc.fetchall()
                for subcat in subcats:
                    self.getPagesInCategory(subcat['parent_category'], cat_id, depth = depth-1)

        #rc.close()
        return None

    def insertPages(self, pages, cat_id):
        # Format the data
        values = []
        space  = []
        for p in pages:
            space.append("(%s,%s,%s,%s)")
            values += [ str(p['page_id']), str(cat_id), p['parent_category'], str(p['parent_category_id']) ]

        # Insert the pages
        if len(pages):
            out("%s - [%s] Inserting %s pages." % (self.getName(), self.project, str( len(pages) )))
            query = 'INSERT INTO project_pages (pp_id, pp_project_id, pp_parent_category, pp_parent_category_id) VALUES ' + ','.join(space) + ' ON DUPLICATE KEY UPDATE pp_id = pp_id'
            lc = self.ldb.execute(query, values)
            #lc.close()

def main():
    # First, clear out projects and project pages
    ldb = db(localDb)
    rdb = db(remoteDb)

    out("Clearing old projects and project pages from local DB")
    query = 'DELETE FROM project; DELETE FROM project_pages;'
    lc = ldb.execute("DELETE FROM project")
    lc = ldb.execute("DELETE FROM project_pages")

    # Then, fetch current projects from the toolserver
    out("Fetching projects from labs server")
    query = '(SELECT page.page_id, page.page_title, revision.rev_timestamp FROM page INNER JOIN category ON page.page_title = category.cat_title LEFT JOIN revision ON rev_page = page_id WHERE page_namespace = 4 AND page_title LIKE "WikiProject_%%" GROUP BY page_id) UNION (SELECT page.page_id, page.page_title, revision.rev_timestamp FROM page INNER JOIN categorylinks ON page.page_id = categorylinks.cl_from LEFT JOIN revision on rev_page = page_id WHERE categorylinks.cl_to = "Active_WikiProjects" AND page.page_namespace = 4 AND page.page_title NOT LIKE "WikiProject_%%" GROUP BY page_id) ORDER BY page_title ASC'
    rc = rdb.execute(query)
    rows = rc.fetchall()

    # Format the data
    values = []
    space = []
    projects = []
    for r in rows:
        space.append("(%s,%s,%s)")
        values += [str(r['page_id']), r['page_title'], str(r['rev_timestamp'])]
        projects.append( [r['page_id'], r['page_title']] )

    # Insert WP projects into local DB
    query = 'INSERT INTO project (p_id, p_title, p_created) VALUES ' + ','.join(space) + ' ON DUPLICATE KEY UPDATE p_id = p_id'
    out("Inserting projects in local db")
    lc = ldb.execute(query, values)

    # Finally, populate pages for current projects in local db
    for i in range(10):
        u = syncProjects(queue)
        u.setDaemon(True)
        u.start()

    # Populate queue with projects
    for project in projects:
        queue.put( project )

    # Wait on the queue until everything is finished
    queue.join()

    ldb.close()
    rdb.close()

if __name__ == "__main__":
    main()



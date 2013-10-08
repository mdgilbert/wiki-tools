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

import wiki_projects
from uw_db import uw_db

# Allow threading
import Queue
import threading
import datetime
import sys

queue = Queue.Queue(10)

class populateProjectEdits(threading.Thread):
    """ Script to grab all edit counts to all project pages over time """

    cursor = None
    project = None
    project_id = None

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            db = uw_db()
            self.cursor = db.getCursorForDB("reflex_relations", self.getName())

            # Get the assessmet we're fetching
            self.project = self.queue.get()

            # Get the project talk page id
            query = "SELECT tp_id FROM ts_pages WHERE tp_title = %s AND tp_namespace = 5"
            db.execute(self.cursor, query, (self.project[1], ))
            row = self.cursor.fetchone()
            talk_id = 0
            if not (row == None or len(row) == 0):
                talk_id = row[0]

            print self.getName() + " - Project: " + self.project[1]

            # Then get all the edits to the project and project talk pages
            # | pp_id    | pp_project_id | pp_parent_category                     | pp_parent_category_id | rc_user_id | rc_page_id | rc_page_namespace | rc_edits | rc_wikiweek | tug_uid  | tug_group                    
            # select * from n_project_pages join reflex_cache on pp_id = rc_page_id LEFT JOIN ts_users_groups ON tug_uid = rc_user_id where pp_project_id = 4766818 and rc_wikiweek = 507 AND (tug_group NOT LIKE 'bot%' OR tug_group IS NULL);
            query = "SELECT rc_user_id, rc_edits, rc_wikiweek FROM reflex_cache LEFT JOIN ts_users_groups ON tug_uid = rc_user_id WHERE rc_page_id in (%s, %s) AND rc_user_id > 0 AND (tug_group NOT LIKE 'bot%%' OR tug_group IS NULL) ORDER BY rc_wikiweek ASC"
            self.cursor.execute(query, (self.project[0], talk_id))
            edits = 0
            editors = {}
            last_quarter = 0
            while True:
                rows = self.cursor.fetchmany(1000)
                if not rows:
                    break
                for row in rows:
                    quarter = convertWeekToQuarter(row[2])
                    if quarter != last_quarter and last_quarter != 0:
                        # insert the row and reset
                        print self.getName() + " - Inserting rows for project " + self.project[1] + " for quarter " + str(last_quarter)
                        c1 = db.getCursorForDB("reflex_relations", self.getName() + "_insert")
                        c1.execute('INSERT INTO cscw_project_edits_pp (cpe_project_id, cpe_project_page_edits, cpe_project_page_editors, cpe_quarter) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE cpe_project_id = cpe_project_id', (self.project[0], edits, len(editors), last_quarter))
                        edits = 0
                        editors = {}
                        
                    edits += row[1]
                    editors[row[0]] = 1
                    last_quarter = quarter

            self.queue.task_done()

def convertWeekToQuarter(week):
    """ Utility function to convert wikiweeks to wikiquarters """
    start = datetime.datetime(2001, 1, 1, 0, 0)
    diff = datetime.timedelta(weeks=week)
    end = start + diff
    month_diff =  (end.year - start.year)*12 + end.month - start.month
    quarters = month_diff / 3
    return quarters + 1

def main():
    # Load all the projects
    projects = wiki_projects.localProj().getProjects()
    print "Loaded " + str( len(projects) ) + " projects."

    # Spawn a pool of threads
    for i in range(10):
        u = populateProjectEdits(queue)
        u.setDaemon(True)
        u.start()

    # Populate queue with data
    for project in projects:
        queue.put(project)

    # Wait on the queue until everything is finished
    queue.join()

main()




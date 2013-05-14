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

import re

import wiki_categories
import uw_settings
from uw_db import uw_db

class wikiProj(object):
    """Class for fetching project data from the toolserver"""
    cursor = None
    wikiDB = "enwiki_p"

    def __init__(self):
        """
        Initialize the object
        """
        # Setup the database connection
        #self.cursor = uw_db().getCursorForDB(self.wikiDB)
        pass


    ## Query to get all WikiProjects (seems to work fairly well, returned 2083 rows in 1m46s)
    ## select page_id, page_title from page inner join category on page_title = cat_title where page_namespace = 4 and page_title like "WikiProject\_%";
    ## Query to get other "Active WikiProject" pages potentially missed by the previous query
    ## select page_id, page_title from page inner join categorylinks on page_id = cl_from where cl_to = "Active_WikiProjects" and page_namespace = 4 and page_title NOT LIKE "WikiProject_%";

    def getProjects(self, filter = None):
        """
        Fetches project information from the Toolserver DB.
        Input:
            filter - a SQL expression limiting the projects that will be returned (suitable for a WHERE clause).
        Returns:
            A sequence of projects including (<page id>, <project title>)
        """
        self.cursor = uw_db().getCursorForDB(self.wikiDB)

        f = " AND page_title LIKE '%%" + filter + "%%' " if filter else ""
        self.cursor.execute('''(SELECT page.page_id, page.page_title FROM %s.page INNER JOIN %s.category ON page.page_title = category.cat_title WHERE page_namespace = 4 AND page_title LIKE "WikiProject\_%%" %s GROUP BY page_id) UNION (SELECT page.page_id, page.page_title FROM %s.page INNER JOIN %s.categorylinks ON page.page_id = categorylinks.cl_from WHERE categorylinks.cl_to = "Active_WikiProjects" AND page.page_namespace = 4 AND page.page_title NOT LIKE "WikiProject_%%" %s GROUP BY page_id) ORDER BY page_id ASC''' % (self.wikiDB, self.wikiDB, f, self.wikiDB, self.wikiDB, f))

        rows = self.cursor.fetchall()
        self.cursor.close()
        return rows

    def getProjectPages(self, project):
        """
        Fetches all the pages that are in a given project
        """
        return wiki_categories.wikiCat().getPagesInCategory(project)

    def testPrintProject(self, project):
        """
        Test function to print project information from Toolserver DB
        """
        pass

class localProj(object):
    """Class for fetching and/or updating project data on our local server"""
    cursor = None
    localDB = "reflex_relations"

    def __init__(self):
        """
        Initialize the object
        """
        #self.cursor = uw_db().getCursorForDB(self.localDB)
        pass

    def getProjects(self, query = None):
        """
        Fetches project data from the UW DB
        """
        pass

    def clearProjects(self):
        """
        Clears out all project data from the local DB
        """
        self.cursor = uw_db().getCursorForDB(self.localDB)
        self.cursor.execute('''DELETE FROM %s.n_project''' % (self.localDB,))
        self.cursor.execute('''DELETE FROM %s.n_project_pages''' % (self.localDB,))
        self.cursor.close()

    def insertProjects(self, projects):
        """
        Populates the project table.
        Input: 
            projects - a sequence of projects of the form ((<project id>, <project title>), )
        """
        self.cursor = uw_db().getCursorForDB(self.localDB)

        values = []
        space = []
        for p in projects:
            values += [str(p[0]), p[1]]
            space.append("(%s,%s)")
        self.cursor.execute('INSERT INTO n_project (p_id, p_title) VALUES ' + ','.join(space), values)
        self.cursor.close()

    def updateProjects(self):
        """
        Updates the UW DB with project data from the Toolserver
        """
        self.cursor = uw_db().getCursorForDB(self.localDB)

        # 1, clear project data
        self.clearProjects()

        # 2, fetch projects from the Toolserver category tables
        #wiki_categories.wikiCat().getPagesInCategory(project)
        print "Fetching projects."
        #projects = wikiProj().getProjects()
        #projects = ((33633, "WikiProject_Sports"), )
        projects = ((488347, '"Template:Football_kit"_materials'), )
        self.insertProjects(self, projects)

        # 3, for each project, fetch the member pages
        i = 0
        for project in projects:
            i += 1
            print "(" + str(i) + " of " + str(len(projects)) + ") Fetching pages for project: " + project[1]
            pages = wikiProj().getProjectPages(project[1])
            values = []
            space = []
            for p in pages:
                #values.append("(" + str(p[0]) + "," + str(project[0]) + ",\"" + re.escape(str(p[1])) + "\"," + str(p[2]) + ")")
                values += [str(p[0]), str(project[0]), str(p[1]), str(p[2])]
                space.append("(%s,%s,%s,%s)")

            # 4, insert the page rows
            if len(pages):
                print "  Inserting " + str( len(pages) ) + " pages."
                self.cursor.execute('INSERT INTO n_project_pages (pp_id, pp_project_id, pp_parent_category, pp_parent_category_id) VALUES ' + ','.join(space) + ' ON DUPLICATE KEY UPDATE pp_id = pp_id', values)

        self.cursor.close()


if __name__ == "__main__":
    #print "Updating project list in local database from toolserver"
    #localProj().updateProjects()

    #localProj().testPrintProject("WikiProject_ACC")
    """
    pages = wikiProj().getProjectPages("WikiProject_Zoo");
    print pages
    print "Total pages found: " + str( len(pages) )
    """
    """
    projects = wikiProj().getProjects()
    print projects
    print "Total projects found: " + str( len(projects) )
    """
    localProj().updateProjects()


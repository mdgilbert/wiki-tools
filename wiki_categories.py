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

import uw_settings
from uw_db import uw_db

class wikiCat(object):
    """Manages category requests from the Toolserver DB"""
    cursor = None
    wikiDB = "enwiki_p"

    def __init__(self):
        """
        Initialize the object
        """
        #self.cursor = uw_db().getCursorForDB(self.wikiDB)
        pass

    def getCategories(self, query = None):
        """
        Fetch categories
        """
        pass

    ## Query to get subcategories (ex is for WikiProject_Zoo) - Will return subcategories of a desired category and page counts
    ## under that category.  Should call recursively limited by depth to get /all pages/ under a given category.
    ## select page.page_title as categories FROM enwiki_p.categorylinks INNER JOIN enwiki_p.page ON page.page_id = categorylinks.cl_from WHERE categorylinks.cl_to = "WikiProject_Zoo" AND page.page_namespace = 14;
    ## Then, after getting the above list call the same function again 

    def getPagesInCategory(self, category, depth = 4, callback = None):
        """
        Returns pages in a given category
        Inputs:
            category - the category we want to get pages for
            depth - the amount of subcategories we will traverse to find all pages.  Set to -1 for no limit (probably a bad idea?)
            callback - If given, this callback function will be called for each chunk of data returned.  Used to 
                allow bucketing inserts to avoid out of memeory issues
        Returns:
            A sequence of pages containing subpages, containing: (<page id>, <parent cat>, <parent cat id>)
            Where, project id is the toolserver  page id for the project page, and parent cat and parent cat id are
            the Toolserver category id and title for the parent.  Parent cat and parent cat id are passed to allow users
            to recreate the hierarchical category structure if desired.
        """
        self.cursor = uw_db().getCursorForDB(self.wikiDB)

        pages = ()

        # First, get basic information for the category
        #print "Fetching category information for " + category
        self.cursor.execute('''SELECT cat_id, cat_title, cat_pages, cat_subcats FROM category WHERE category.cat_title = %s''', (category,))
        parent = self.cursor.fetchone()

        if parent:
            # Get sub-pages
            #if category == '"Template:Football_kit"_materials':
            if 1:
                #print "Fetching sub-pages for category: " + category + ", depth: " + str(depth)
                self.cursor.execute('''SELECT cl_from as "page_id", %s as "parent_category", %s as "parent_category_id" FROM categorylinks WHERE cl_to = %s''', (parent[1], parent[0], category))
                pages = self.cursor.fetchall();
                #while pages = self.cursor.fetchmany(10000) and pages:

            # If this category has sub-categories, append all their pages as well
            if parent[3] > 0 and depth != 0:
                #print "Fetching sub-categories for category: " + category + ", depth: " + str(depth)
                self.cursor.execute('''SELECT page.page_title as "parent_category" FROM categorylinks INNER JOIN page ON page.page_id = categorylinks.cl_from WHERE categorylinks.cl_to = %s AND page.page_namespace = 14''', (parent[1]))
                subcats = self.cursor.fetchall()
                for subcat in subcats:
                    pages += self.getPagesInCategory(subcat[0], depth = depth - 1)

        self.cursor.close()
        return pages

class localCat(object):
    """Manages category requests from the UW db"""
    cursor = None
    localDB = "reflex_relations"

    def __init__(self):
        """
        Initialize the object
        """
        #self.cursor = uw_db().getCursorForDB(self.localDB)
        pass

    def getCategories(self):
        """
        Fetch categories from the UW DB
        """
        pass

    def getPagesWithCategory(self, category):
        """
        Returns pages in a given category
        """
        pass

    def testPrintCat(self, category):
        """
        Test function, prints info for a given category
        """
        self.cursor = uw_db().getCursorForDB(self.localDB)
        self.cursor.execute('''SELECT * FROM project LIMIT 1''')
        row = self.cursor.fetchone()
        if row:
            print "Project fetched: "
            print row
            print "First index: " + str(row[0])

        self.cursor.close()

if __name__ == "__main__":
    #print "Updating category list in local database from the Toolserver"
    #localCat().updateCategories()
    localCat().testPrintCat("WikiProject_24_articles");


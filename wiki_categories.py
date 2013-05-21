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

db = uw_db()

class wikiCat(object):
    """Manages category requests from the Toolserver DB"""
    cursor = None
    wikiDB = "enwiki_p"

    def __init__(self):
        """
        Initialize the object
        """
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

    def getPagesInCategory(self, category, depth = 4, callback = None, id = None, thread = None, includeTitle = None):
        """
        Returns pages in a given category
        Inputs:
            category - the category we want to get pages for
            depth - the amount of subcategories we will traverse to find all pages.  Set to -1 for no limit (probably a bad idea?)
            callback - Required, this callback function will be called for each chunk of data returned.  Used to 
                allow bucketing inserts to avoid out of memeory issues
        Returns:
            Returns nothing - a function that handles page data should be passed in as a callback.  This 
            will be called for every 1000 pages.
        """
        self.cursor = db.getCursorForDB(self.wikiDB, thread)

        pages = ()

        # First, get basic information for the category
        #print "Fetching category information for " + category
        #self.cursor.execute('''SELECT cat_id, cat_title, cat_pages, cat_subcats FROM category WHERE category.cat_title = %s''', (category,))
        query = 'SELECT cat_id, cat_title, cat_pages, cat_subcats FROM category WHERE category.cat_title = %s'
        db.execute(self.cursor, query, (category,))
        parent = self.cursor.fetchone()

        if parent:
            # Get sub-pages
            #if category == '"Template:Football_kit"_materials':
            if 1:
                #print "Fetching sub-pages for category: " + category + ", depth: " + str(depth)
                if includeTitle:
                    #self.cursor.execute('''SELECT cl_from as "page_id", %s as "parent_category", %s as "parent_category_id", page_title FROM categorylinks JOIN page ON cl_from = page_id WHERE cl_to = %s''', (parent[1], parent[0], category))
                    query = 'SELECT cl_from as "page_id", %s as "parent_category", %s as "parent_category_id", page_title FROM categorylinks JOIN page ON cl_from = page_id WHERE cl_to = %s'
                    db.execute(self.cursor, query, (parent[1], parent[0], category))
                else:
                    #self.cursor.execute('''SELECT cl_from as "page_id", %s as "parent_category", %s as "parent_category_id" FROM categorylinks WHERE cl_to = %s''', (parent[1], parent[0], category))
                    query = 'SELECT cl_from as "page_id", %s as "parent_category", %s as "parent_category_id" FROM categorylinks WHERE cl_to = %s'
                    db.execute(self.cursor, query, (parent[1], parent[0], category))
                while True:
                    pages = self.cursor.fetchmany(1000)
                    if not pages:
                        break
                    callback(pages, id)

            # If this category has sub-categories, append all their pages as well
            if parent[3] > 0 and depth != 0:
                #print "Fetching sub-categories for category: " + category + ", depth: " + str(depth)
                #self.cursor.execute('''SELECT page.page_title as "parent_category" FROM categorylinks INNER JOIN page ON page.page_id = categorylinks.cl_from WHERE categorylinks.cl_to = %s AND page.page_namespace = 14''', (parent[1]))
                query = 'SELECT page.page_title as "parent_category" FROM categorylinks INNER JOIN page ON page.page_id = categorylinks.cl_from WHERE categorylinks.cl_to = %s AND page.page_namespace = 14'
                db.execute(self.cursor, query, (parent[1],))
                subcats = self.cursor.fetchall()
                for subcat in subcats:
                    self.getPagesInCategory(subcat[0], depth = depth - 1, callback = callback, id = id, thread = thread, includeTitle = includeTitle)

        self.cursor.close()
        return None

class localCat(object):
    """Manages category requests from the UW db"""
    cursor = None
    localDB = "reflex_relations"

    def __init__(self):
        """
        Initialize the object
        """
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


if __name__ == "__main__":
    #print "Updating category list in local database from the Toolserver"
    #localCat().updateCategories()
    localCat().testPrintCat("WikiProject_24_articles");


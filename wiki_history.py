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

import uw_settings
from uw_db import uw_db
from time import localtime, mktime, strftime

db = uw_db()

class localHistory(object):
    """ Manages the history of previous index actions to avoid work duplication """
    cursor = None
    localDB = "reflex_relations"
    index_type = None
    thread = None
    history = {}    

    def __init__(self, index_type = None, thread = ''):
        """ Initialize """
        self.index_type = index_type
        self.thread = self.__class__.__name__ + "-" + thread

    def setIndexType(self, index_type):
        self.index_type = index_type

    def getHistory(self):
        """ Fetches the history for a given index_type (ie, updateProjects, updateAssessments, etc) """
        self.cursor = db.getCursorForDB(self.localDB, thread = self.thread)
        if self.index_type == None:
            raise Exception("NoIndexType", "Must run setIndexType or initialize with index_type")

        self.history[self.index_type] = {}
        query = 'SELECT h_index_type, h_indexed FROM n_history WHERE h_index_type = %s'
        db.execute(self.cursor, query, (self.index_type, ))
        rows = self.cursor.fetchall()
        for row in rows:
            self.history[self.index_type][row[1]] = 1
        self.cursor.close()

        return self.history

    def isComplete(self, cat):
        """ Checks if a given category is complete for an index type """
        if self.index_type == None:
            raise Exception("NoIndexType", "Must run setIndexType or initialize with index_type")
        if len(self.history) == 0:
            self.getHistory()
        if cat in self.history[self.index_type]:
            return True
        return False

    def setComplete(self, cat, thread = None):
        """ Sets an action complete in the DB and local dict """
        local_thread = thread if thread else self.thread
        self.cursor = db.getCursorForDB(self.localDB, thread = local_thread)
        if self.index_type == None:
            raise Exception("NoIndexType", "Must run setIndexType or initialize with index_type")
        if len(self.history[self.index_type]) == 0:
            self.history[self.index_type] = {}
        self.history[self.index_type][cat] = 1
        query = 'INSERT INTO n_history (h_index_type, h_indexed, h_completed) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE h_index_type = h_index_type'
        db.execute(self.cursor, query, (self.index_type, cat, strftime('%Y%m%d%H%M%S')))
        return True

    def clearHistory(self, keepDays = 0):
        """ Clears prior history for a given index_type """
        self.cursor = db.getCursorForDB(self.localDB, thread = self.thread)
        if self.index_type == None:
            raise Exception("NoIndexType", "Must run setIndexType or initialize with index_type")
        past_str = ''
        if keepDays:
            past = mktime(localtime()) - (60 * 60 * 24 * keepDays)
            past_str = " AND h_completed < " + str( strftime('%Y%m%d%H%M%S', localtime(past)) )
        query = 'DELETE FROM n_history WHERE h_index_type = %s ' + past_str
        db.execute(self.cursor, query, (self.index_type, ))
        self.history[self.index_type] = {}
        return self


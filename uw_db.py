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

import MySQLdb
import uw_settings
import time
import sys

class uw_db:
    """Manages database connections for our local tools"""
    conn = {}
    thread = None
    db = None

    def __init__(self):
        """
        Initialize the object
        """
        pass

    def getCursorForDB(self, db, thread):
        """
        Returns a cursor for a given database
        """

        # Connect to the database if required
        self.thread = thread
        self.db = db
        key = db + "-" + thread
        if key not in self.conn:
            self.conn[key] = MySQLdb.connect(host = uw_settings.db[db]['host'], db = uw_settings.db[db]['db'], user = uw_settings.db[db]['user'], passwd = uw_settings.db[db]['pass'], use_unicode=True, charset="utf8")

        return self.conn[key].cursor()

    def renewConnection(self):
        """
        Renews a potentially closed DB connection
        """
        key = self.db + "-" + self.thread
        # Attempt to close the previous connection
        try:
            self.conn[key].close()
        except:
            pass
        if key in self.conn:
            del self.conn[key]
        return self.getCursorForDB(self.db, self.thread)

    def execute(self, cursor, query, values = (), count = 4):
        """
        Executes a query with a given cursor.  If the DB connection is lost, will retry <count> times
        """
        if count > 0:
            try:
                #print "Query: " + query
                cursor.execute(query, values)
            except:
                print "DB query failed: " + str(sys.exc_info()[1])
                print "Trying with new connection in 20..."
                time.sleep(20)
                cursor = self.renewConnection()
                self.execute(cursor, query, values = values, count = count-1)
        else:
            print "Exceeded failure count for this query.  Exiting."
            raise Exception("MaxFailuresReached", "Multiple failures attempting to execute query.")


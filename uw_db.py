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

class uw_db:
    """Manages database connections for our local tools"""
    conn = {}

    def __init__(self):
        """
        Initialize the object
        """
        pass

    def getCursorForDB(self, db):
        """
        Returns a cursor for a given database
        """
        # Connect to the database if required
        if db not in self.conn:
            self.conn[db] = MySQLdb.connect(host = uw_settings.db[db]['host'], db = uw_settings.db[db]['db'], user = uw_settings.db[db]['user'], passwd = uw_settings.db[db]['pass'], use_unicode=1, charset="utf8")

        return self.conn[db].cursor()



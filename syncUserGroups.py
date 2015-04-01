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

""" Local user groups table:
CREATE TABLE `ts_users_groups` (
  `tug_uid` int(10) unsigned DEFAULT NULL,
  `tug_group` varbinary(128) DEFAULT NULL,
  KEY `tug_uid` (`tug_uid`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""

# Import local tools
from pycommon.util.util import *
from pycommon.db.db import db

db = db()
localDb = 'reflex_relations_2014'

def main():
    """ Drop the old user groups, re-import the new """
    lc = db.getCursorForDB(localDb)
    rc = db.getCursorForDB("enwiki_p")

    # Drop the old groups
    query = "DELETE FROM ts_users_groups"
    out("Deleting old user groups")
    lc = db.execute(lc, query)

    # Fetch the updated groups
    query = "SELECT * FROM user_groups"
    out("Selecting user groups")
    rc = db.execute(rc, query)
    rows = rc.fetchall()
    space = []
    values = []
    for r in rows:
        space.append("(%s,%s)")
        values += [str(r["ug_user"]), str(r["ug_group"])]

    # Add them to the local table
    query = "INSERT INTO ts_users_groups (tug_uid, tug_group) VALUES %s" % (','.join(space))
    out("Inserting user groups")
    lc = db.execute(lc, query, values)

if __name__ == "__main__":
    main()



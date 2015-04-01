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

""" Local project_activity table:
CREATE TABLE `project_activity` (
  `pa_project_id` int(8) NOT NULL,
  `pa_page_id` int(8) NOT NULL,
  `pa_ww_from` smallint(5) unsigned NOT NULL,
  `pa_edits` mediumint(9) unsigned NOT NULL,
  PRIMARY KEY (`pa_project_id`, `pa_page_id`, `pa_ww_from`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
"""

from pycommon.util.util import *
from pycommon.db.db import db

ww = get_ww()
localDb = 'reflex_relations_2014'

def main():
    out("Syncing active WikiProject data.")

    # This is an absurdly simple sync script.  In fact, it's just one query.
    ldb = db(localDb)
    query = "INSERT INTO project_activity (pa_project_id, pa_page_id, pa_page_namespace, pa_ww_from, pa_edits) SELECT pp_project_id AS 'pa_project_id', rc_page_id AS 'pa_page_id', rc_page_namespace AS 'pa_page_namespace', '%s' AS 'pa_ww_from', SUM(rc_edits) AS 'pa_edits'  FROM reflex_cache JOIN project_pages ON pp_id = rc_page_id WHERE rc_wikiweek >= %s GROUP BY rc_page_id, pa_project_id ON DUPLICATE KEY UPDATE pa_edits = pa_edits" % (ww-4, ww-4)
    lc = ldb.execute(query)

    # Final output message
    out("Finished caching all active wikiprojects from wikiweek starting %s (ww-4)" % (ww-4))

if __name__ == "__main__":
    main()

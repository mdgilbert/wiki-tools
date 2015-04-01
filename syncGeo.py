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


from pycommon.util.util import *
from pycommon.db.db import db
import socket, struct
import csv

db = db()
lc = db.getCursorForDB("reflex_relations_2014", "this")

# Geo location information downloaded from 
# http://dev.maxmind.com/geoip/legacy/geolite/
files = ['GeoIPASNum2.csv', 'GeoLiteCity-Blocks.csv', 'GeoLiteCity-Location.csv']
dbs   = ['geo_asn', 'geo_blocks', 'geo_location']

files = ['GeoLiteCity-Blocks.csv']
dbs   = ['geo_blocks']

# Open the file
idb = 0
for geo_csv in files:
    out("Reading csv file: " + geo_csv)
    with open(geo_csv, 'rb') as f:
        f_read = csv.reader(f, delimiter=',', quotechar='"')
        values = []
        space  = []
        i = 0
        for r in f_read:
            if len(r) == 3:
                space.append("(%s,%s,%s,%s,%s,%s)")
                values += [socket.inet_ntoa(struct.pack('!L', long(r[0]))), socket.inet_ntoa(struct.pack('!L', long(r[1]))), str(r[0]), str(r[1]), str(r[2]), 1]
            elif len(r) == 9:
                space.append("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                values += [str(r[0]), r[1], r[2], r[3], str(r[4]), str(r[5]), str(r[6]), str(r[7]), str(r[8]), 1]

            # Insert every 10000 rows
            if len(space) >= 10000:
                out("Inserting chunk %i" % (i,))
                query = "INSERT INTO %s VALUES %s ON DUPLICATE KEY UPDATE dummy=1" % (dbs[idb], ','.join(space))
                lc = db.execute(lc, query, values)
                values = []
                space  = []
                i += 1

        # Insert
        if len(space):
            out("Final insert for csv file: " + geo_csv)
            query = "INSERT INTO %s VALUES %s ON DUPLICATE KEY UPDATE dummy=1" % (dbs[idb], ','.join(space))
            lc = db.execute(lc, query, values)

lc.close()
out("Done!")


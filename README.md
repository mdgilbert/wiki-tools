wiki-tools
==========

Tools for parsing Wikipedia data.

These are being fairly consistently updated and improved as time allows. The basic steps to get everything setup are as follows:


1. Install the database schema - This is included in schema.sql. You can restore the database structure by downloading this file and running `mysql -u <user> -p <database name> < schema.sql` from the command line. Currently I've only used MySQL for the data, but this could be updated if needed.
2. Download shared functions from https://github.com/mdgilbert/pycommon and add the directory that's downloaded to to your PYTHONPATH environment variable.
3. Copy the `pycommon/db/db_settings_example.py` file to `db_settings.py` and update with your database information, including information to connect to the MediaWiki Labs database.
4. Verify that basic connections are working by running the syncUsers.py script (this should succeed or error out fairly quickly so you'll have an idea of what's either working or not).
5. If the syncUsers.py script succeeded, the remaining _should_ as well. If not, let me know or suggest a fix.

Thanks, and I hope these prove useful to folks in some way or another.


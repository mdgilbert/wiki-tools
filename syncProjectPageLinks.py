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

"""
FOR FINAL PAPER

This script is intended to get all USER LINKS to on project pages, sub-pages, and templates
transcluded on either of the above, as well as all corresponding talk pages.
"""

# Import local tools
from pycommon.util.util import *
from pycommon.db.db import db

# Make sure we're dealing with utf-8 strings
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# Allow threading
import Queue
import threading
import time

# We'll need to grab user links from Wikipedia API
import urllib2
# Need the unquote_plus function
import urllib

# And BeautifulSoup to parse the returned html
from bs4 import BeautifulSoup
# Regular expressions needed to parse user links
import re
# To print the stack trace if we error out
import traceback

# From mako
## THIS IS MAGIC I FOUND ON THE INTERNET
import re, urlparse

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts= urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts))
## END MAGIC

debug = 0
threads = 8
queue = Queue.Queue(threads)
ww = get_ww()
localDb = "reflex_relations_2014"
remoteDb = "enwiki_p_local"
user_cache = {}
page_cache = {}

class syncUserLinks(threading.Thread):
    """ Threaded approach to syncing user links """

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.ldb = db(localDb, self.getName())
        self.rdb1 = db(remoteDb, self.getName())
        #self.rdb2 = db(remoteDb, self.getName())
        self.p_id = ""
        self.p_title = ""

    def run(self):
        """ 
        The meat of the script, gets all member pages of the project (including pages, sub-pages,
        and all pages transcribed on either of the above, and the corresponding talk pages for
        each), and fetches links to user pages for each.
        """

        while True:
            # Project row:  p_id, p_title, p_created, p_member_to
            project = self.queue.get()
            self.p_id = project["p_id"]
            self.p_title = project["p_title"]

            # First, update the project_and_template_pages for this project (will
            # include all project pages, sub pages, templates/modules transcluded
            # on those pages, and corresponding talk pages)
            project_pages = self.updateProjectAndTemplatePages(project)

            # Then, for each page, grab user links after the last sync'd revision
            i = 0
            for page_id in project_pages:
                i += 1
                query = "SELECT cplh_revision FROM coord_project_links_history WHERE cplh_page_id = %s"
                lc = self.ldb.execute(query, (page_id))
                row = lc.fetchone()
                synced_to = 0
                if row:
                    synced_to = row["cplh_revision"]

                # Next, check for more recent revisions than the last recorded revision
                out("[%s] %s - Page %s of %s, searching for user links after revision %s (%s:%s)." % (project["p_title"], self.getName(), i, len(project_pages), synced_to, project_pages[page_id]["page_namespace"], project_pages[page_id]["page_title"]))

                query = "SELECT rev_id, rev_page, rev_user, rev_user_text, rev_timestamp FROM revision WHERE rev_page = %s AND rev_id > %s"
                rc = self.rdb1.execute(query, (page_id, synced_to))

                while True:
                    revs = rc.fetchmany(1000)
                    if not revs:
                        break
                    values = []
                    space = []
                    for rev in revs:
                        # For each revision, get any user links that were added
                        links = self.getPageLinksFromRevision(rev)
                        values += links
                        space  += ["(%s,%s,%s,%s,%s,%s,%s,%s)"] * (len(links) / 8)

                        # Insert links from this revision, if any were found
                        if len(space) > 0:
                            out("[%s] %s Links: %s, Date: %s, Page: %s:%s" % (project["p_title"], self.getName(), len(space), rev["rev_timestamp"][:8], project_pages[page_id]["page_namespace"], project_pages[page_id]["page_title"]))
                            query = "INSERT INTO coord_project_links (cpl_link_page_id, cpl_link_page_text, cpl_link_page_namespace, cpl_link_rev, cpl_link_date, cpl_rev_user, cpl_rev_user_name, cpl_page_id) VALUES %s ON DUPLICATE KEY UPDATE cpl_link_page_id = cpl_link_page_id" % (",".join(space))
                            lc = self.ldb.execute(query, values)
                            values = []
                            space = []

                        # Update page_links_history for this page
                        query = "INSERT INTO coord_project_links_history (cplh_page_id, cplh_revision) VALUES (%s,%s) ON DUPLICATE KEY UPDATE cplh_revision = %s"
                        lc = self.ldb.execute(query, (page_id, rev["rev_id"], rev["rev_id"]))

            # Aaaaand, we're done
            out("[%s] %s - Completed inserting user links" % (project["p_title"], self.getName()))
            self.queue.task_done()

    def updateProjectAndTemplatePages(self, project):
        project_pages = {}

        out("[%s] %s - Fetching pages and transclusions for project." % (project["p_title"], self.getName()))
        #query = "UPDATE project_and_template_pages SET ptp_removed = 1 WHERE ptp_project_id = %s"
        #lc = self.ldb.execute(query, (project["p_id"]))

        # Fetch project pages and sub-pages
        query = "SELECT page_id, page_title, page_namespace, page_is_redirect FROM page WHERE page_namespace IN (4,5) AND (page_title = %s OR page_title LIKE %s) ORDER BY page_title ASC"
        rc1 = self.rdb1.execute(query, (project["p_title"], project["p_title"] + "/%%"))
        pages = rc1.fetchall()
        values = []
        space = []
        for page in pages:
            # If this page is a redirect grab the target page
            if page["page_is_redirect"] == 1:
                page = self.getRedirectTo(page)
            # If we couldn't find a target page for a redirect, skip this page
            if page["page_is_redirect"] == -1:
                continue
            # Add the page to our hash
            project_pages[page["page_id"]] = page
            values += [project["p_id"], page["page_id"], 0]
            space += ["(%s,%s,%s)"]

            # We'll also want to grab all templates/modules transcluded on this page,
            # which we'll go through after these pages
            # Note: templatelinks table tl_from should be the id of the project or sub-page, 
            # tl_namespace and tl_title will be what we want to see if bots edited, 
            # as /that's/ what's going to show up in the tl_from page (the WP page).
            # So, first get all the templates that are transcluded on project pages

            # Note #2: We won't know /when/ the template was added to the project page, 
            # so we'll add all revisions to that template.  This means that it's possible 
            # that user links may be over-reported, in that we'll include links that were 
            # added to a template before that template was added to the project page.
            query = "SELECT t.page_id, t.page_title, t.page_namespace, t.page_is_redirect FROM templatelinks JOIN page AS p ON tl_from = p.page_id JOIN page AS t ON tl_title = t.page_title AND tl_namespace = t.page_namespace WHERE tl_from = %s GROUP BY page_id"
            rc2 = self.rdb1.execute(query, (page["page_id"]))
            templates = rc2.fetchall()
            for template in templates:
                # Also grab potential redirects from transcluded pages
                if template["page_is_redirect"] == 1:
                    template = self.getRedirectTo(template)
                # If we couldn't find a target page for a redirect, skip this template
                if template["page_is_redirect"] == -1:
                    continue
                # Add the page to our hash
                project_pages[template["page_id"]] = template
                values += [project["p_id"], template["page_id"], 0]
                space += ["(%s,%s,%s)"]

        # Add all the project and template pages to the local db
        #query = "INSERT INTO project_and_template_pages (ptp_project_id,ptp_page_id,ptp_removed) VALUES %s ON DUPLICATE KEY UPDATE ptp_page_id = ptp_page_id" % (",".join(space))
        #lc = self.ldb.execute(query, values)

        # Remove outdated pages from project_and_template_pages
        #query = "DELETE FROM project_and_template_pages WHERE ptp_removed = 1"
        #lc = self.ldb.execute(query)

        # Finally, return the pages
        return project_pages

    def getRedirectTo(self, page):
        query = "SELECT page_id, page_namespace, page_title, page_is_redirect FROM redirect JOIN page ON rd_title = page_title AND rd_namespace = page_namespace WHERE rd_from = %s"
        rc = self.rdb1.execute(query, (page["page_id"]))
        row = rc.fetchone()
        # If we couldn't find the redirect page we'll need to skip this page
        if not row:
            page["page_is_redirect"] == -1
            row = page
        elif row["page_is_redirect"] == 1:
            return self.getRedirectTo(row)
        return row

    # The new form of this function will view the full rendered text of a wikipage, and will
    # return all user links that exist on that page for each revision -
    # (further parsing can be handled client side).
    def getPageLinksFromRevision(self, rev, err_time=60):
        # Setup the url
        #wp_api_base = "http://en.wikipedia.org/w/index.php?curid=%s&diff=prev&oldid=%s&diffonly=1"
        #wp_api_url = wp_api_base % (rev["rev_page"], rev["rev_id"])
        wp_api_base = "https://en.wikipedia.org/w/index.php?curid=%s&oldid=%s"
        wp_api_url = wp_api_base % (rev["rev_page"], rev["rev_id"])
        if debug == 1:
            out("    Revision url: %s" % (wp_api_url))
        # Call the url - the first line opens the url but also handles unicode urls
        try:
            call = urllib2.urlopen(iriToUri(wp_api_url))
        except urllib2.HTTPError, e:
            out("[%s]   %s - Failed to request revision diff with error %s" % (self.p_title, self.getName(), e.code))
            out("[%s]   URL: %s" % (self.p_title, wp_api_url))
            out("[%s]   Error: %s" % (self.p_title, traceback.format_exc()))
            # If this is a service unavailable error, try again in increasing increments
            if e.code == 503:
                out("[%s]   Will attempt to fetch user links after %s second pause..." % (self.p_title, err_time))
                time.sleep(err_time)
                return self.getPageLinksFromRevision(rev, err_time*2)
            else:
                self.queue.task_done()
                #raise
        else:
            api_answer = call.read()
            api_answer = unicode(api_answer, "UTF-8")

            # api_answer will be the response from the Wikipedia API - we'll need to pull out all
            # links to user pages, get the user ID of that link, format and return.
            soup = BeautifulSoup(api_answer)

            # The full text of the page at the current revision will be in a div
            # with the id "mw-content-text". Grab that and pull all user links out.
            # Also, make sure we don't include automatic documentation in page text
            # (For example, look at Template:User - we would only want to return the
            # result of the /actual/ template, since that's what would be transcluded).
            full = soup.find(id="mw-content-text")
            if full.find(id="template-documentation") is not None:
                full.find(id="template-documentation").extract()
            links = full.find_all("a")
            page_links = []
            for link in links:
                # For this script, we'll include all links to base pages (i.e., we /will/
                # include /wiki/User:test, but /won't/ include links to /wiki/User:test/sub).
                # Additionally, we'll include /all/ links within /wiki, including those to
                # User pages, Wikipedia pages, Article pages, etc.
                url = link.get("href")
                # Make sure it's a link to Wikipedia, no red links
                if url[0:6] == "/wiki/":
                    if debug == 1:
                        out("        Found link: %s" % (url))
                    namespace = ""
                    namespace_id = 0
                    page_title = url[6:]
                    # Handle links to different namespaces
                    if url[6:].find(":") != -1:
                        index = url[6:].find(":")
                        namespace = url[6:][:index]
                        namespace_id = namespace_to_id(namespace)
                        page_title = url[6:][index+1:]
                        if namespace_id == -1:
                            #out("        Couldn't parse namespace from url %s" % (url))
                            continue
                    # Find the page id linked to
                    pid = self.getPageId(page_title, namespace_id)
                    if pid == -1:
                        continue
                    # Finally, add it to the page_links array
                    page_links += [pid, page_title, namespace_id, rev["rev_id"], rev["rev_timestamp"], rev["rev_user"], rev["rev_user_text"], rev["rev_page"]]


            # Once we've parsed all the links for the revision, 
            # return the array suitable for inserting into db
            return page_links
        # Or, if we failed to request the page, just return an empty array
        return []

    def getPageId(self, page, namespace_id):
        t_page = page
        try:
            t_page = page.encode("utf8")
        except:
            pass
        page = t_page
        if page in page_cache:
            return page_cache[page]

        #
        # Next, try to get the page id from local page table
        query = "SELECT * FROM ts_pages WHERE tp_title = %s AND tp_namespace = %s"
        lc = self.ldb.execute(query, (self.ldb.escape_string(page), namespace_id))
        row = lc.fetchone()
        if row:
            page_cache[page] = row["tp_id"]
            return row["tp_id"]

        #
        # That's it. If we can't find the page, return -1
        return -1

    def getUserId(self, user):
        # Clean characters from the user string
        user = user.replace("_", " ").strip().strip("_").strip("<").strip(">")
        # And make sure the user is in the proper format
        t_user = user
        try:
            t_user = user.encode("utf8")
        except:
            pass
        user = t_user
        # First, if we've already found this user's id just return it from the local variable
        if user in user_cache:
            return user_cache[user]

        #
        # Next, try to get the user's id from our local user table
        user_under = user.replace(" ", "_")
        user_space = user.replace("_", " ")
        query = "SELECT tu_id FROM ts_users WHERE tu_name = %s OR tu_name = %s"
        try:
            lc = self.ldb.execute(query, (self.ldb.escape_string(user_under), self.ldb.escape_string(user_space)))
        except:
            print("\n\nERROR: user type = "+str(type(user))+", user_under type = " + str(type(user_under)) + "\n")
            out("[%s]   Failed to parse string: %s, %s" % (self.p_title, user_under, user_space))
            out("[%s]   Error: %s" % (self.p_title, traceback.format_exc()))
            self.queue.task_done()
            raise Exception('bad', 'bad')

        row = lc.fetchone()
        if row:
            user_cache[user] = row["tu_id"]
            return row["tu_id"]

        #
        # Second, if we can't find in the local db try to find via a web request
        out("[%s]   Checking user page for user %s" % (self.p_title, user))
        wp_user_url = "https://en.wikipedia.org/wiki/User:%s" % (user)
        # Don't throw an exception if we can't find the user or parse the uri
        try:
            call = urllib2.urlopen(iriToUri(wp_user_url))
        except urllib2.HTTPError, e:
            out("[%s]   Failed to request user page for user %s with error %s" % (self.p_title, user, e.code))
            out("[%s]   Error: %s" % (self.p_title, traceback.format_exc()))
        except UnicodeDecodeError, e:
            out("[%s]   Failed to parse url for user %s with error %s" % (self.p_title, user, e.reason))
            out("[%s]   Error: %s" % (self.p_title, traceback.format_exc()))
        else:
            # If we found a user page, parse for the user id and search in the local table again
            api_answer = call.read()
            #encoding = call.headers['content-type'].split('charset=')[-1]
            encoding = "UTF-8"
            api_answer = unicode(api_answer, encoding)
            soup = BeautifulSoup(api_answer)
            page_user = re.findall("User[^:]*?:(.+) - Wikipedia, the free encyclopedia", soup.title.text)
            if len(page_user) > 0:
                u = page_user[0]
                user_under = u.replace(" ", "_")
                user_space = u.replace("_", " ")
                query = "SELECT tu_id FROM ts_users WHERE tu_name = %s or tu_name = %s"
                lc = self.ldb.execute(query, (self.ldb.escape_string(user_under), self.ldb.escape_string(user_space)))
                row = lc.fetchone()
                if row:
                    user_cache[u] = row["tu_id"]
                    user_cache[user] = row["tu_id"]
                    out("[%s]   Found name from user page '%s'" % (self.p_title, u))
                    return row["tu_id"]
                else:
                    user_cache[u] = 0

        # If we /still/ can't find the user id it might be a mis-type. Assign the user to 0
        out("[%s]   Failed to find user id for %s, assigning to 0." % (self.p_title, user))
        user_cache[user] = 0
        return 0

def main():
    ldb = db(localDb)

    # Spawn a pool of threads
    for i in range(threads):
        u = syncUserLinks(queue)
        u.setDaemon(True)
        u.start()

    # Fetch all the projects
    """ Sample projects:
    Chemisrty: 161220
    Running: 4224987
    Books: 6235048
    Food_and_drink: 258844
    Freemasonry: 5633357
    Cats: 4766818

    (161220, 4224987, 6235048, 258844, 5633357)

    Women's health: 46768646
    Human Computer Interaction: 42114934
    Bibliographical Database: 33107712
    """
    #query = "SELECT * FROM project ORDER BY p_title ASC"
    #query = "SELECT * FROM project WHERE p_id IN (33107712, 42114934)"
    query = 'select * from project where p_title in ("WikiProject_Feminism", "WikiProject_Piracy", "WikiProject_Medicine", "WikiProject_Plants", "WikiProject_Chemistry", "WikiProject_Spoken_Wikipedia", "WikiProject_Countering_systemic_bias", "WikiProject_Copyright_Cleanup", "WikiProject_Missing_encyclopedic_articles", "WikiProject_Outreach")'

    #query = "SELECT * FROM project WHERE p_title IN ('WikiProject_Plants')"

    lc = ldb.execute(query)
    rows = lc.fetchall()
    for row in rows:
        # If we've already synced all projects to the prior week, skip this project.  Otherwise, add to queue.
        # NM, can't do this since templates can be added to a project /after/ they've had user links.. We'll
        # check this in the query above.
        #if row["p_member_to"] < ww-1:
        queue.put(row)

    # Wait on the queue until everything is done
    queue.join()

    ldb.close()
    out("Completed syncProjectUserLinks.py")

if __name__ == "__main__":
    main()



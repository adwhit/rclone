from requests import post
from lxml import etree
from io import StringIO
from datetime import datetime
import sys
import gzip

uri = "http://rosettacode.org/mw/index.php?title=Special:Export&action=submit"

def gettasks():
    print "Retrieving tasklist"
    gettasks = {"catname":"Programming_Tasks", "addcat":"Add", "pages":"", "curonly":"1", "wpDownload":"1"}

    response = post(uri, gettasks)
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(response.text), parser)
    tasklist = tree.xpath("//textarea")[0].text
    return tasklist

def getpages(tasks, take_n):
    tasklist = tasks.split("\n")
    ntasks = len(tasklist)
    if take_n:
        tasks = "\n".join(tasklist[:take_n+1])
        ntasks = take_n
    now = datetime.now()
    getpages = {"catname":"", "pages":tasks, "curonly":"1"}
    print "Retrieving pages"
    response = post(uri, getpages)

    fname = "data/rip%d.%s.xml.gz" % (ntasks, now.strftime("%Y-%m-%dT%H%M"))
    print "Saving to file %s " % fname
    with gzip.open(fname, "wb") as f:
        f.write(response.text.encode("utf8"))

def main(ntasks=None):
    getpages(gettasks(), ntasks)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(int(sys.argv[1]))
    else:
        main()

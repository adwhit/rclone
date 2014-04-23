from requests import post
from lxml import etree
from io import StringIO
from datetime import datetime
import gzip

now = datetime.now()

uri = "http://rosettacode.org/mw/index.php?title=Special:Export&action=submit"



gettasks = {"catname":"Programming_Tasks", "addcat":"Add", "pages":"", "curonly":"1", "wpDownload":"1"}
getpages = {"catname":"", "pages":"", "curonly":"1"}

print "Retrieving tasklist"
r = post(uri, gettasks)
parser = etree.HTMLParser()
tree = etree.parse(StringIO(r.text), parser)
tasklist = tree.xpath("//textarea")[0].text
getpages["pages"] = tasklist

print "Retrieving pages"
r2 = post(uri, getpages)

fname = "data/rip%s.xml.gz" % now.strftime("%Y-%m-%dT%H%M")


print "Saving to file %s " % fname
with gzip.open(fname, "wb") as f:
    f.write(r2.text.encode("utf8"))






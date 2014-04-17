import sys
from lxml import etree
import re
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from subprocess import Popen, PIPE, STDOUT

### DB INIT STUFF

engine = create_engine("sqlite:///data.sqlite", echo=False)
Base = declarative_base(bind=engine)
Session = scoped_session(sessionmaker(bind=engine))

class Code(Base):
    __tablename__ = "code"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String())
    language = Column(String(), ForeignKey("language.name"))
    task = Column(String(), ForeignKey("task.name"))

    relationship("Lang", backref = "codes")
    relationship("Task", backref = "codes")

    def __repr__(self):
        return "<Code:{:s}/{:s}>".format(self.task, self.language)

class Lang(Base):
    __tablename__ = "language"
    name = Column(String(), primary_key=True)

    def __repr__(self):
        return "<Lang:{:s}>".format(self.name)

class Task(Base):
    __tablename__ = "task"
    name = Column(String(), primary_key=True)
    description = Column(String())

    def __repr__(self):
        return "<Task:{:s}>".format(self.name)

def cleanstr(s):
    """Clean string for use as filename etc"""
    arr = []
    for c in s.lower().strip():
        if c.isalnum():
            arr.append(c)
    return "\n".join(arr)

def newdb():
    Base.metadata.create_all()

class Scraper():
    tagbase = "{http://www.mediawiki.org/xml/export-0.7/}"
    rarestring = "%Z%Z%"

    def __init__(self, datapath):
        """Class to download and parse data from Rossetta Code website"""
        if not (datapath.endswith('.gz') or datapath.endswith('.xml')):
            print "Error: invalid file type ", datapath
            sys.exit(1)
        self.datapath = datapath
        self.tree = None
        self.root = None
        self.pages = {}
        self.htmlpages = {}

    def xml2dict(self, root):
        pagedict = {}
        for page in root:
            title = page.find(Scraper.tagbase + "title")
            if title is not None:
                text = page.find(Scraper.tagbase + "revision").find(
                        Scraper.tagbase + "text").text
                pagedict[title.text] = text
        return pagedict

    def getdata(self):
        if self.datapath.endswith(".gz"):
            import gzip
            tree = etree.parse(gzip.open(self.datapath))
        else:
            tree = etree.parse(self.datapath)
        root = tree.getroot()
        return tree, root

    def splitcode(self, pagekey):
        r = Scraper.rarestring
        """Split code from description"""
        langarr = re.findall(r+"(.*)"+r, self.htmlpages[pagekey])
        sections = re.split(r+".*"+r, self.htmlpages[pagekey])
        print len(langarr)
        print len(sections)
        assert(len(sections) == len(langarr) + 1)
        description = sections[0]
        codedict = {}
        codedict = dict(zip(langarr,sections[1:]))
        return description, codedict

    def parse(self):
        self.tree, self.root = self.getdata()
        self.pages = self.xml2dict(self.root)
        self.htmlpages = dict2html(self.pages)

def mw2html(mwstring):
    p = Popen(["pandoc","-f", "mediawiki","-t", "html"], 
            stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    return p.communicate(input=mwstring.encode('utf8'))[0]

def dict2html(d):
    h = {}
    for k,v in d.iteritems():
        print k
        txt = substitute_tag(v)
        h[k] = mw2html(txt).decode('utf8')
    return h
    
def substitute_tag(txt):
    r = Scraper.rarestring
    tmp1 = re.sub("=={{header\|(.*)}}==",r+"\g<1>"+r,txt)
    tmp2 =  re.sub("<lang ([^>]*)>", "<syntaxhighlight lang=\g<1>>", tmp1)
    return re.sub("</lang>", "</syntaxhighlight>", tmp2)


def build_sql_objects(scraper):
    langset = set()
    tasks = []
    langs = []
    codes = []

    for task, pagetext in scraper.htmlpages.items():
        description, codedict = scraper.splitcode(task)
        tasks.append(Task(name=task, description=description))
        for (lang, text) in codedict.items():
            langset.add(lang)
            codes.append(Code(text=text, language=lang, task=task))

    for lang in langset:
        langs.append(Lang(name=lang))
    return tasks, langs, codes

def create_db(datapath):
    #parse xml
    scraper = Scraper(datapath)
    scraper.parse()

    #make db
    newdb()
    session = Session()

    #obtain data
    tasks, langs, codes = build_sql_objects(scraper)

    #add
    session.add_all(tasks)
    print("Found {:d} tasks".format(len(tasks)))
    session.add_all(langs)
    print("Found {:d} langs".format(len(langs)))
    session.add_all(codes)
    print("Found {:d} snippets".format(len(codes)))

    session.commit()


def main(datapath):
    create_db(datapath)



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Please supply database file in XML or XML.GZ format"
        sys.exit()
    main(sys.argv[1])

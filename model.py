import sys
import os.path
import re
import argparse
from lxml import etree
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, Index
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from subprocess import Popen, PIPE, STDOUT

Base = declarative_base()

class Code(Base):
    __tablename__ = "code"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String())
    language = Column(String(), ForeignKey("language.name"))
    task = Column(String(), ForeignKey("task.name"))
    __table_args__ = (Index("tasklangind", "task", "language"),)

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
    raw = Column(String())  #raw markdown output
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

def newdb(engine):
    Base.metadata.create_all(engine)

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
                pagedict[title.text.title()] = text
        return pagedict

    def getdata(self):
        if self.datapath.endswith(".gz"):
            import gzip
            tree = etree.parse(gzip.open(self.datapath))
        else:
            tree = etree.parse(self.datapath)
        root = tree.getroot()
        return tree, root

    def parse(self):
        self.tree, self.root = self.getdata()
        self.pages = self.xml2dict(self.root)

def splitcode(task, text):
    r = Scraper.rarestring
    """Split code from description"""
    langarr = re.findall(r+"(.*?)"+r, text)
    sections = re.split(r+".*?"+r, text)
    if (len(langarr) == 0):
        print "WARNING: splitting failed for page:", task
    if (len(sections) != len(langarr) + 1):
        print "WARNING: wrong number of sections for page:", task
        print "N sections:", len(sections)
        print "N langarr:", len(langarr)
    description = sections[0]
    codedict = {}
    codedict = dict(zip(langarr,sections[1:]))
    return description, codedict

def mw2html(task, mwstring):
    prepped = preprocess(mwstring)
    p = Popen(["pandoc","-f", "mediawiki","-t", "html"], 
            stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    return postprocess(p.communicate(input=prepped.encode('utf8'))[0])


def sub_tag_to_token(txt):
    r = Scraper.rarestring
    # XXX how to capture "=={{header|C}} / {{header|C++}}==" ?
    # ideally want to create two separate entries
    # the below match will completely miss it
    tmp1 = re.sub("=={{header\|([^}]*)}}==",r+"\g<1>"+r,txt)
    tmp2 =  re.sub("<lang\s*([^>]*)>", "<syntaxhighlight lang=\g<1>>", tmp1)
    return re.sub("</lang>", "</syntaxhighlight>", tmp2)

def sub_wp_to_links(txt):
    return re.sub('a href="wp:(.*?)"', 'a href="http://en.wikipedia.org/wiki/\g<1>"', txt)

def postprocess(html):
    return sub_wp_to_links(html)

def preprocess(mwstring):
    return sub_tag_to_token(mwstring)

def page2ORM(task, mwtext):
    htmltext = mw2html(task, mwtext).decode("utf8")
    description, codedict = splitcode(task, htmltext)
    ormtask = Task(name=task, description=description, raw=mwtext)
    ormcodes = []
    ormlangs = []
    for (lang, text) in codedict.items():
        ormcodes.append(Code(text=text, language=lang, task=task))
        ormlangs.append(Lang(name=lang))
    return ormtask, ormlangs, ormcodes

def create_db(datapath, dbpath):
    #parse xml
    scraper = Scraper(datapath)
    scraper.parse()

    #make db
    engine, Session = connect_to_db(dbpath)
    newdb(engine)
    session = Session()

    #obtain data
    for task, mwtext in scraper.pages.items():
        print "Processing task:  ",task
        task, langs, codes = page2ORM(task, mwtext)
        session.add(task)
        session.add_all(codes)
        session.add_all(langs)
        session.commit()

def connect_to_db(dbpath):
    engine = create_engine("sqlite:///"+ dbpath, echo=False)
    return engine, scoped_session(sessionmaker(bind=engine))

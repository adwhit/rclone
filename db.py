from lxml import etree
import re
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

### DB INIT STUFF

engine = create_engine("sqlite:///data.sqlite", echo=False)
Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)

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
    return "".join(arr)

def newdb():
    Base.metadata.create_all()

class Scraper():
    tagbase = "{http://www.mediawiki.org/xml/export-0.7/}"
    xmlpath = "data/Rosetta+Code-20140302015523.xml"

    def __init__(self, xmlpath = None):
        """Class to download and parse data from Rossetta Code website"""
        if xmlpath is None:
            self.xmlpath = Scraper.xmlpath
        else:
            self.xmlpath = xmlpath
        self.tree = None
        self.root = None
        self.pages = {}

    def xml2dict(self, root):
        pagedict = {}
        for page in root:
            title = page.find(Scraper.tagbase + "title")
            if title is not None:
                text = page.find(Scraper.tagbase + "revision").find(
                        Scraper.tagbase + "text").text
                pagedict[title.text] = text
        return pagedict

    def getdata(self, xmlpath):
        tree = etree.parse(xmlpath)
        root = tree.getroot()
        return tree, root

    def splitcode(self, pagekey):
        rexp = re.compile("}}.*header\|")
        sections = re.split("=={{header\|(.*)}}==", self.pages[pagekey])
        description = sections[0]
        body = sections[1:]
        codedict = {}
        for ix in range(0,len(body),2):
            langarr = re.split(rexp,body[ix])
            for lang in langarr:
                codedict[lang] = body[ix+1]
        return description, codedict

    def parse(self):
        self.tree, self.root = self.getdata(self.xmlpath)
        self.pages = self.xml2dict(self.root)

def build_sql_objects(scraper):
    langset = set()
    tasks = []
    langs = []
    codes = []

    for task, pagetext in scraper.pages.items():
        description, codedict = scraper.splitcode(task)
        tasks.append(Task(name=task, description=description))
        for (lang, text) in codedict.items():
            langset.add(lang)
            codes.append(Code(text=text, language=lang, task=task))

    for lang in langset:
        langs.append(Lang(name=lang))
    return tasks, langs, codes

def main():
    #parse xml
    scraper = Scraper()
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



if __name__ == "__main__":
    main()



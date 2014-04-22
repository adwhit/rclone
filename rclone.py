from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for
from model import Lang, Task, Code, connect_to_db
from sqlalchemy import or_, and_, func
from sqlalchemy.orm.exc import NoResultFound
import argparse
import sys

app = Flask(__name__)

#globals
class gb():
    nullstr = "--"
    notfounderr = "No page found. You may be able to find it on <a href=http://www.rosettacode.org" \
            "/wiki/%s>RosettaCode.org</a>.  <a href='javascript:history.back()'> Back</a>. "\
            "<span id=why><small><a href='/faq#why'>Why did this happen?</a></small></span>"
    pageitems = "task lang1 lang2 hide".split()

    snippetdict = {}
    taskdict = {}
    task2lang = defaultdict(set)
    lang2task = defaultdict(set)
    task_filters = {}
    lang_filters = {}
    link_guesses = {}
    Session = None
    
def init_globals(dbpath):
    _, gb.Session = connect_to_db(dbpath)

    session = gb.Session()

    #build task2lang and lang2task maps
    l2t = gb.lang2task
    t2l = gb.task2lang
    alltasks = set()
    alllangs = set()
    qry= session.query(Code.language, Code.task)
    for (l,t) in qry:
        l2t[l].add(t)
        t2l[t].add(l)
        alltasks.add(t)
        alllangs.add(l)
    gb.task_filters["all"] = alltasks
    gb.lang_filters["all"] = alllangs

    #populate filters
    top_tasks = session.query(Code.task, func.count(Code.task)).\
                group_by(Code.task).order_by(func.count(Code.task).desc()).limit(30).all()

    gb.task_filters["top"] = set([r[0] for r in top_tasks])

    #gb.lang_filters["top"] = set([r[0] for r in 
    #    session.query(Code.language, func.count(Code.language)).group_by(Code.language).limit(20).all()])

    gb.lang_filters["top"] = set("C,C++,JavaScript,Java,Python,D,Objective-C,PHP,Ruby,\
                 Go,Rust,Julia,Haskell,Clojure,C#,UNIX shell,Perl".split(","))
    gb.lang_filters["python"] = set(["Python"])


@app.route("/app/")
def handler():
    pagedata = get_form_data()
    filters = get_filters()
    get_content(pagedata)
    filter_content(pagedata, filters)
    return render_template("app.html", **pagedata)

@app.route("/app/<path:link>")
def wikilink(link):
    guess = guess_link(link)
    if guess:
        return redirect("/app/?task=%s" % guess_link(link))
    else:
        return redirect("/app/?task=%s" % link)


@app.route("/faq/")
def faq():
    return render_template("faq.html")

def get_form_data():
    formdata = {}
    for item in gb.pageitems:
        formdata[item] = notnull(request.args.get(item))
    return formdata

def get_filters():
    taskfilters = []
    lang1filters = []
    lang2filters = []

    for filter in gb.task_filters:
        if request.args.get(filter):
            taskfilters.append(filter)

    for filter in gb.lang_filters:
        if request.args.get("l1" + filter):
            lang1filters.append(filter)
        if request.args.get("l2" + filter):
            lang2filters.append(filter)

    return {"task": taskfilters, "lang1": lang1filters, "lang2" :lang2filters}

@app.route("/")
def toindex():
    return redirect("/app/")

def notnull(s):
    if s == gb.nullstr:
        return None
    else:
        return s

def get_content(content):

    task = content["task"]
    lang1 = content["lang1"]
    lang2 = content["lang2"]
    

    tasklist = gb.task_filters["all"].copy()
    langlist = gb.lang_filters["all"].copy()

    if task:
        content["rclink"] = task2link(task)
        langlist &= get_langlist(task)
        content["taskdesc"] = get_task_desc(task)

    if lang1:
        tasklist &= get_tasklist(lang1)
        if task:
            content["lang1code"] = get_snippet(task, lang1)

    if lang2:
        tasklist &= get_tasklist(lang2)
        if task:
            content["lang2code"] = get_snippet(task, lang2)

    content["tasklist"] = [gb.nullstr] + sorted(tasklist)
    content["lang1list"] = langlist
    content["lang2list"] = langlist.copy()
    return content

def filter_content(content, filters):
    for tf in filters["task"]:
        content["tasklist"] &= gb.task_filters[tf]
        content[tf] = True
    for l1f in filters["lang1"]:
        content["lang1list"] &= gb.lang_filters[l1f]
        content["l1" + l1f] = True
    for l2f in filters["lang2"]:
        content["lang2list"] &= gb.lang_filters[l2f]
        content["l2" + l2f] = True

    content["lang1list"] = [gb.nullstr] + sorted(content["lang1list"])
    content["lang2list"] = [gb.nullstr] + sorted(content["lang2list"])


def get_snippet(task, lang):
    snippet = gb.notfounderr % task
    if (task, lang) in gb.snippetdict:
        return gb.snippetdict[task,lang]
    if lang in gb.lang_filters["all"]:
        session = gb.Session()
        snippet = session.query(Code).filter(and_(Code.language==lang, Code.task==task.title())).one().text
    gb.snippetdict[task,lang] = snippet    #cache
    return snippet


def get_task_desc(task):
    #assume not found, then lookup
    taskdesc = gb.notfounderr % task
    if task in gb.taskdict:
        return gb.taskdict[task]
    if task in gb.task_filters["all"]:
        session = gb.Session()
        taskdesc = session.query(Task).filter_by(name=task.title()).one().description
    gb.taskdict[task] = taskdesc
    return taskdesc


def get_tasklist(lang):
    return gb.lang2task[lang]


def get_langlist(task):
    return gb.task2lang[task]


def filter_list(list1, set1):
    return [l for l in list1 if l in set1]

def guess_link(link):
    if link in gb.task_filters["all"]:
        return link
    elif link in gb.link_guesses:
        return gb.link_guesses[link]
    else:
        score = 1000
        guess = ""
        sl = set(link.lower())
        ll = len(link)
        for task in gb.task_filters["all"]:
            scr = len(set(task.lower()).symmetric_difference(sl)) + abs(len(task) - ll)
            if scr < score:
                score = scr
                guess = task
        print "Guessing link: %s, Guess: %s, Score: %s" % (link, guess, score)
        if score < 4:
            gb.link_guesses[link] = guess
            return guess
        else:
            gb.link_guesses[link] = None
            return None


def task2link(task):
    link = "/".join([t.capitalize() for t in task.replace(" ","_").split("/")])
    return "http://rosettacode.org/wiki/"+link

def main(dbpath, debug):
    init_globals(dbpath)
    if debug:
        app.run(debug=True, port = 3000)
    else:
        app.run(host="0.0.0.0")

def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="data/data.sqlite")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    return(args.database, args.debug)

if __name__ == "__main__":
    main(*argparser())

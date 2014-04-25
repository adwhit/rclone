from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for
from model import Lang, Task, Code, connect_to_db
from sqlalchemy import or_, and_, func
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.contrib.fixers import ProxyFix
import argparse
import sys

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

#globals
class gb():
    nullstr = ""
    notfounderr = "No page found. You may be able to find it on <a href=http://www.rosettacode.org" \
            "/wiki>RosettaCode.org</a>.<br><a href='javascript:history.back()'> Go back</a> "\
            "<span id=why><small><a href='/faq#why'>Why did this happen?</a></small></span>"
    pageitems = "task lang1 lang2 hide".split()

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

    gb.lang_filters["popular"] = set([r[0] for r in 
        session.query(Code.language, func.count(Code.language)).\
                group_by(Code.language).order_by(func.count(Code.language).desc()).limit(20).all()])

    gb.lang_filters["top"] = set("C,C++,JavaScript,Java,Python,D,Objective-C,PHP,Ruby,\
                 Go,Rust,Julia,Haskell,Clojure,C#,UNIX shell,Perl".split(","))
    gb.lang_filters["python"] = set(["Python", "Ruby"])

@app.route("/app/")
def handler():
    pagedata = get_form_data()
    get_filters(pagedata)
    get_content(pagedata)
    filter_content(pagedata)
    pagedata["langfiltlist"] = gb.lang_filters.keys()
    pagedata["taskfiltlist"] = gb.task_filters.keys()
    print pagedata["langfiltlist"]
    print pagedata["taskfiltlist"]
    print pagedata["l1filters"]
    print pagedata["l2filters"]
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

def get_filters(content):
    content["taskfilters"] = request.args.getlist("taskfilt")
    content["l1filters"] = request.args.getlist("l1filt")
    content["l2filters"] = request.args.getlist("l2filt")

@app.route("/")
def toindex():
    return redirect("/app/?l1top=true&l2top=true")

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

    content["tasklist"] = tasklist
    content["lang1list"] = langlist
    content["lang2list"] = langlist.copy()
    return content

def filter_content(content):
    for tf in content["taskfilters"]:
        if tf in gb.task_filters:
            content["tasklist"] &= gb.task_filters[tf]
    for l1f in content["l1filters"]:
        if l1f in gb.lang_filters:
            content["lang1list"] &= gb.lang_filters[l1f]
    for l2f in content["l2filters"]:
        if l2f in gb.lang_filters:
            content["lang2list"] &= gb.lang_filters[l2f]

    content["tasklist"] = [gb.nullstr] + sorted(content["tasklist"])
    content["lang1list"] = [gb.nullstr] + sorted(content["lang1list"])
    content["lang2list"] = [gb.nullstr] + sorted(content["lang2list"])


def get_snippet(task, lang):
    snippet = gb.notfounderr
    if lang in gb.lang_filters["all"]:
        session = gb.Session()
        snippet = session.query(Code).filter(and_(Code.language==lang, Code.task==task.title())).one().text
    return snippet


def get_task_desc(task):
    #assume not found, then lookup
    taskdesc = gb.notfounderr
    if task in gb.task_filters["all"]:
        session = gb.Session()
        taskdesc = session.query(Task).filter_by(name=task.title()).one().description
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

def main(dbpath, debug, profile):
    init_globals(dbpath)
    host = "0.0.0.0"
    port = 80
    if debug:
        host = "127.0.0.1"
        port = 3000
    if profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [30])
        app.config['PROFILE'] = True
    app.run(host=host, debug=debug, port=port)

def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="data/data.sqlite")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-p", "--profile", action="store_true")
    args = parser.parse_args()
    return(args.database, args.debug, args.profile)


if __name__ == "__main__":
    main(*argparser())
else:
    init_globals("data/data.sqlite")

from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for
import db
from db import Lang, Task, Code
from sqlalchemy import or_, and_, func
import argparse
import sys

#globals
class gb():
    nullstr = "--"
    urlplaceholder = "0"
    slashsub = "."
    spacesub = "_"
    snippetdict = {}
    taskdict = {}
    task2lang = defaultdict(set)
    lang2task = defaultdict(set)
    task_filters = {}
    lang_filters = {}
    Session = None
    
def init_globals(dbpath):
    _, gb.Session = db.connect_to_db(dbpath)

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

    gb.lang_filters["top"] = set([r[0] for r in 
        session.query(Code.language, func.count(Code.language)).group_by(Code.language).all()])
    gb.lang_filters["popular"] = set("C,C++,JavaScript,Java,Python,D,Objective-C,PHP,Ruby,\
                 Go,Rust,Julia,Haskell,Clojure,C#,UNIX shell,Perl".split(","))

app = Flask(__name__)

@app.route("/app")
def handler():
    print request.form
    formdata = get_form_data()
    content = get_content(**formdata)
    if formdata["ncols"] == 1:
        return render_template("onecol.html", **content)
    elif formdata["ncols"] == 2:
        return render_template("twocol.html", **content)

def get_form_data():
    #update formdata fields
    formdata = defaultdict(str)

    formdata["task"] = notnull(request.args.get("task"))
    formdata["taskfilter"] = request.args.get("taskfilter")

    formdata["lang1"] = notnull(request.args.get("lang1"))
    formdata["lang1filter"] = request.args.get("lang1filter")

    ncols = request.args.get("ncols")
    ncols = int(ncols) if ncols else 2
    formdata["ncols"] = ncols

    if ncols == 2:
        formdata["lang2"] = notnull(request.args.get("lang2"))
        formdata["lang2filter"] = request.args.get("lang2filter")
    else:
        formdata["lang2"] = None

    print formdata
    return formdata


@app.route("/")
def toindex():
    u = gb.urlplaceholder
    return redirect("/app?ncols=2&task=%s&lang1=%s&lang2=%s" % (
        u, u, u))

def notnull(s):
    if s == gb.nullstr or s == gb.urlplaceholder:
        return ""
    else:
        return s

def get_content(ncols, task, lang1, lang2, **kwargs):
    content = {"task": task, "lang1": lang1, "lang2": lang2}
    tasklist = gb.task_filters["all"].copy()
    langlist = gb.lang_filters["all"].copy()


    if lang1:
        tasklist &= get_tasklist(lang1)
        if task:
            content["lang1code"] = get_snippet(task, lang1)

    if task:
        langlist &= get_langlist(task)
        content["taskdesc"] = get_task_desc(task)

    if lang2:
        tasklist &= get_tasklist(lang2)
        if task:
            content["lang2code"] = get_snippet(task, lang2)

    content["tasklist"] = [gb.nullstr] + sorted(tasklist)
    content["langlist"] = [gb.nullstr] + sorted(langlist)

    for k,v in content.iteritems():
        print k
        if v: print len(v)

    return content


def get_snippet(task, lang):
    if (task, lang) in gb.snippetdict:
        return gb.snippetdict[task,lang]
    else:
        session = gb.Session()
        snippet = session.query(Code).filter(and_(Code.language==lang, Code.task==task)).one().text
        gb.snippetdict[task,lang] = snippet    #cache
        return snippet


def get_task_desc(task):
    if task in gb.taskdict:
        return gb.taskdict[task]
    session = gb.Session()
    taskdesc = session.query(Task).filter_by(name=task).one().description
    gb.taskdict[task] = taskdesc
    return taskdesc


def get_tasklist(lang):
    return gb.lang2task[lang]


def get_langlist(task):
    return gb.task2lang[task]

def clean_string(s):
    return s.replace(" ",gb.spacesub).replace("/",gb.slashsub)

def clean_strings(l):
    return map(clean_string,l)

def unclean_string(s):
    return s.replace(gb.spacesub," ").replace(gb.slashsub,"/")

def unclean_strings(l):
    return map(unclean_string,l)



def filter_list(list1, set1):
    return [l for l in list1 if l in set1]

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

from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for
from db import Lang, Task, Code, Session
from sqlalchemy import or_, and_, func

lang_filters = { 
             }

class gb():
    nullstr = "--"
    snippetdict = {}
    taskdict = {}
    task2lang = defaultdict(set)
    lang2task = defaultdict(set)
    task_filters = {}
    lang_filters = {}
    
def set_globals():
    session = Session()

    #build task2lang and lang2task maps
    l2t = gb.lang2task
    t2l = gb.task2lang
    qry= session.query(Code.language, Code.task)
    for (l,t) in qry:
        l2t[l].add(t)
        t2l[t].add(l)


    #populate filters
    top_tasks = session.query(Code.task, func.count(Code.task)).\
                group_by(Code.task).order_by(func.count(Code.task).desc()).limit(30).all()
    gb.task_filters["top"] = set([r[0] for r in top_tasks])

    gb.lang_filters["top"] = set([r[0] for r in 
        session.query(Code.language, func.count(Code.language)).group_by(Code.language).all()])
    gb.lang_filters["popular"] = set("C,C++,JavaScript,Java,Python,D,Objective-C,PHP,Ruby,\
                 Go,Rust,Julia,Haskell,Clojure,C#,UNIX shell,Perl".split(","))

app = Flask(__name__)

@app.route("/<task>/<lang1>/", methods=["POST", "GET"])
def one_lang(task,lang1):
    if method == POST:
        #process and redirect
        formdata = get_form_data(1)
        return redirect(get_redirect(formdata))
    
    formdata["taskname"] = task
    formdata["lang1"] = lang1
    formdata["numcols"] = 1
    content = get_content(formdata)
    return render_template("onecol.html", **content)

@app.route("/<task>/<lang1>/<lang2>/")
def two_lang(task, lang1, lang2):
    if method == POST:
        #process and redirect
        formdata = get_form_data(1)
        return redirect(get_redirect(formdata))
    
    formdata["taskname"] = task
    formdata["lang1"] = lang1
    formdata["numcols"] = 1
    contents = get_content(formdata)

def get_form_data(numcols):
    #update formdata fields
    formdata = defaultdict(str)
    formdata["taskname"] = notnull(request.form.get("taskname"))
    formdata["taskfilter"] = request.form.get("taskfilter")

    formdata["lang1"] = notnull(request.form.get("col1"))
    formdata["lang1filter"] = request.form.get("lang1filter")

    formdata["numcols"] = request.form.get("numcols")

    if numcols == 2:
        formdata["lang2"] = notnull(request.form.get("col2"))
        formdata["lang2filter"] = request.form.get("lang2filter")

    return formdata


@app.route("/")
def toindex():
    return redirect(url_for("twocol"))

def notnull(s):
    if s == gb.nullstr:
        return ""
    else:
        return s

def get_content(formdata):
    content = {}

    lang1 = formdata["lang1"]
    lang2 = formdata["lang2"]
    task = formdata["task"]

    if lang1:
        content["tasklist"] = get_tasklist(lang1)
        if task:
            content["lang1"] = get_snippet(task, lang1)

    if task:
        content["taskdesc"] = get_task_desc(task)

    if lang2 and formdata["numcols"] == 2:
        content["tasklist"] &= get_tasklist(lang2)
        if task:
            content["lang2"] = get_snippet(task, lang2)

    return content


def get_snippet(task, lang):
    if (task, lang) in gb.snippetdict:
        return gb.snippetdict[task,lang]
    else:
        session = Session()
        snippet = session.query(Code).filter(and_(Code.language==lang, Code.task==task)).one().text
        gb.snippetdict[task,lang] = snippet    #cache
        return snippet


def get_task_desc(task):
    if task in gb.taskdict:
        return gb.taskdict[task]
    session = Session()
    taskdesc = session.query(Task).filter_by(name=task).one().description
    gb.taskdict[task] = taskdesc
    return taskdesc


def get_tasklist(lang):
    return gb.lang2task[lang]


def get_langlist(task):
    return gb.task2lang[task]


def filter_list(list1, set1):
    return [l for l in list1 if l in set1]


if __name__ == "__main__":
    set_globals()
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "-d":  #debug mode
        app.run(debug=True, port = 3000)
    else:
        app.run(host="0.0.0.0")

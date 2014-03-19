from flask import Flask, render_template, request
import db
import code_format
from db import Lang, Task, Code
from sqlalchemy import or_, and_, func


class gb():
    langlist = None
    tasklist = None
    nullstr = "--"
    snippetdict = {}
    taskdict = {}
    langlistdict = {}
    tasklistdict = {}
    pop_langs = None 
    
def set_globals():
    session = db.Session()
    gb.langlist = [l.name for l in session.query(Lang).order_by(Lang.name).all()]
    gb.tasklist = [t.name for t in session.query(Task).order_by(Task.name).all()]
    top_langs = session.query(Code.language, func.count(Code.language)).group_by(Code.language).all()
    top_tasks = session.query(Code.task, func.count(Code.task)).\
    group_by(Code.task).order_by(func.count(Code.task).desc()).limit(30).all()
    gb.toptasks = set([r[0] for r in top_tasks])
    gb.poplangs = set([x.replace("_"," ") for x in sorted(
                       "C C++ Javascript Java Python D Objective-C PHP Ruby \
                       Go Rust Julia Haskell Clojure C# UNIX_shell Perl".split())])

app = Flask(__name__)

@app.route("/index", methods = ["GET", "POST"])
def index():

    #defaults:
    content = {
            "taskdesc": "",
            "taskname": "",
            "tasklist": "",
            "code1": "",
            "css1": "",
            "code2": "",
            "css2": "",
            "lang1": "",
            "lang2": "",
            "langlist1": "",
            "langlist2": "",
            "taskfilter": "all",
            "lang1filter": "all",
            "lang2filter": "all",
            }

    if request.method == "POST":
        #update content fields
        #print(request.form)
        content["lang1"] = notnull(request.form.get("col1"))
        content["lang2"] = notnull(request.form.get("col2"))
        content["taskname"] = notnull(request.form.get("taskname"))
        content["taskfilter"] = request.form.get("taskfilter")
        content["lang1filter"] = request.form.get("lang1filter")
        content["lang2filter"] = request.form.get("lang2filter")
        get_content(content)
    elif request.method == "GET":
        content["langlist1"] = get_langlist_notask(content["lang1filter"])
        content["langlist2"] = get_langlist_notask(content["lang2filter"])
        content["tasklist"] = get_tasklist_noway(content["taskfilter"])
        # do some init stuff?

    return render_template("index.html", **content)

def notnull(s):
    if s == gb.nullstr:
        return ""
    else:
        return s

def get_content(content):

    if content["taskname"]:
        #get codes
        content["taskdesc"] =  get_task_desc(content["taskname"])
        content["langlist1"] = get_langlist(content["taskname"], content["lang1filter"])
        content["langlist2"] = get_langlist(content["taskname"], content["lang2filter"])
        if content["lang1"]:
            (content["code1"], content["css1"]) = get_snippet(content["taskname"], content["lang1"])
        if content["lang2"]:
            (content["code2"], content["css2"]) = get_snippet(content["taskname"], content["lang2"])
    else:
        content["langlist1"] = get_langlist_notask(content["lang1filter"])
        content["langlist2"] = get_langlist_notask(content["lang2filter"])
    #get tasklist
    if content["lang1"] and content["lang2"]:
        content["tasklist"] = get_tasklist_twoway(content["lang1"], content["lang2"], content["taskfilter"])
    elif content["lang1"]:
        content["tasklist"] = get_tasklist_oneway(content["lang1"], content["taskfilter"])
    elif content["lang2"]:
        content["tasklist"] = get_tasklist_oneway(content["lang2"], content["taskfilter"])
    else:
        content["tasklist"] = get_tasklist_noway(content["taskfilter"])

    """for k, v in content.items():
        if isinstance(v, str):
            print(k,v)
        else:
            print(k, v[:10])
    """
            
    return content

def get_snippet(task, lang):
    if (task, lang) in gb.snippetdict:
        return gb.snippetdict[task,lang]
    else:
        session = db.Session()
        snippet = session.query(Code).filter(and_(Code.language==lang, Code.task==task)).one().text
        (html, css) = code_format.formatter(snippet, lang)
        gb.snippetdict[task,lang] = (html, css)
        return (html, css)

def get_task_desc(task):
    if task in gb.taskdict:
        return gb.taskdict[task]
    session = db.Session()
    taskdesc = session.query(Task).filter_by(name=task).one().description
    taskdesc = code_format.md_format(taskdesc, task)
    gb.taskdict[task] = taskdesc
    return taskdesc

def get_tasklist_oneway(lang, taskfilter):
    if (lang, taskfilter) in gb.tasklistdict:
        return gb.tasklistdict[lang, taskfilter]
    session = db.Session()
    result = session.query(Code.task).filter_by(language=lang).all()
    tasklist = sorted([r for (r,) in result])
    if taskfilter== "top":
        tasklist = filter_list(tasklist, gb.toptasks)
    tasklist.insert(0,gb.nullstr)
    gb.tasklistdict[lang,taskfilter] = tasklist
    return tasklist

def get_tasklist_noway(taskfilter):
    tasklist = gb.tasklist[:]
    if taskfilter== "top":
        tasklist = filter_list(tasklist, gb.toptasks)
    tasklist.insert(0,gb.nullstr)
    return tasklist


def filter_list(list1, set1):
    return [l for l in list1 if l in set1]

def get_tasklist_twoway(lang1, lang2, taskfilter):
    s1 = set(get_tasklist_oneway(lang1, taskfilter))
    s2 = set(get_tasklist_oneway(lang2, taskfilter))
    return sorted(s1 & s2)

def get_langlist(task, langfilter):
    if (task, langfilter) in gb.langlistdict:
        return gb.langlistdict[task, langfilter]
    session = db.Session()
    results =  session.query(Code.language).filter_by(task=task).order_by(Code.language).all()
    langlist = [r for (r,) in results]
    if langfilter == "top":
        langlist = filter_list(langlist, gb.poplangs)
    langlist.insert(0,gb.nullstr)
    gb.langlistdict[task, langfilter] = langlist
    return langlist

def get_langlist_notask(langfilter):
    langlist = gb.langlist[:]
    if langfilter == "top":
        langlist = filter_list(langlist, gb.poplangs)
    langlist.insert(0,gb.nullstr)
    return langlist


def replace_newline(s):
    s = s.replace("\n\n", "<br>")
    return s.replace("\n", "<br>")

if __name__ == "__main__":
    #app.run(host="0.0.0.0")
    set_globals()
    app.run(debug=True, port = 3000)

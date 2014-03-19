from flask import Flask, render_template, request
import db
import code_format
from db import Lang, Task, Code
from sqlalchemy import or_, and_


class gb():
    all_langs = None
    all_tasks = None
    nullstr = "--"
    snippetdict = {}
    taskdict = {}
    langlistdict = {}
    tasklistdict = {}


def set_globals():
    session = db.Session()
    all_langs = sorted([l.name for l in session.query(Lang).all()])
    all_tasks = sorted([t.name for t in session.query(Task).all()])
    gb.langlist = [gb.nullstr]
    gb.langlist.extend(all_langs)
    gb.tasklist = [gb.nullstr]
    gb.tasklist.extend(all_tasks)


app = Flask(__name__)

@app.route("/index", methods = ["GET", "POST"])
def index():

    #defaults:
    content = {
            "taskdesc": "",
            "taskname": "",
            "tasklist": gb.tasklist,
            "code1": "",
            "css1": "",
            "code2": "",
            "css2": "",
            "lang1": "",
            "lang2": "",
            "langlist1": gb.langlist,
            "langlist2": gb.langlist
            }

    if request.method == "POST":
        #update content fields
        #print(request.form)
        content["lang1"] = notnull(request.form.get("col1"))
        content["lang2"] = notnull(request.form.get("col2"))
        content["taskname"] = notnull(request.form.get("taskname"))
        get_content(content)
    elif request.method == "GET":
        # do some init stuff?
        pass

    return render_template("index.html", **content)

def notnull(s):
    if s == gb.nullstr:
        return ""
    else:
        return s

def get_content(content):

    if content["taskname"]:
        content["taskdesc"] =  get_task_desc(content["taskname"])
        content["langlist1"] = get_langlist(content["taskname"])
        content["langlist2"] = get_langlist(content["taskname"])
        if content["lang1"]:
            (content["code1"], content["css1"]) = get_snippet(content["taskname"], content["lang1"])
        if content["lang2"]:
            (content["code2"], content["css2"]) = get_snippet(content["taskname"], content["lang2"])
    if content["lang1"] and content["lang2"]:
        content["tasklist"] = get_tasklist_twoway(content["lang1"], content["lang2"])
    elif content["lang1"]:
        content["tasklist"] = get_tasklist_oneway(content["lang1"])
    elif content["lang2"]:
        content["tasklist"] = get_tasklist_oneway(content["lang2"])

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
    else:
        session = db.Session()
        taskdesc = session.query(Task).filter_by(name=task).one().description
        taskdesc = code_format.md_format(taskdesc, task)
        gb.taskdict[task] = taskdesc
        return taskdesc

def get_tasklist_oneway(lang):
    if lang in gb.tasklistdict:
        return gb.tasklistdict[lang]
    else:
        session = db.Session()
        result = session.query(Code.task).filter_by(language=lang).all()
        tasklist = [r for (r,) in result]
        tasklist.insert(0,gb.nullstr)
        gb.tasklistdict[lang] = tasklist
        return tasklist

def get_tasklist_twoway(lang1, lang2):
    s1 = set(get_tasklist_oneway(lang1))
    s2 = set(get_tasklist_oneway(lang2))
    return sorted(s1.intersection(s2))

def get_langlist(task):
    if task in gb.langlistdict:
        return gb.langlistdict[task]
    else:
        session = db.Session()
        results =  session.query(Code.language).filter_by(task=task).order_by(Code.language).all()
        langlist = [r for (r,) in results]
        langlist.insert(0, gb.nullstr)
        gb.langlistdict[task] = langlist
        return langlist

def replace_newline(s):
    s = s.replace("\n\n", "<br>")
    return s.replace("\n", "<br>")

if __name__ == "__main__":
    #app.run(host="0.0.0.0")
    set_globals()
    app.run(debug=True, port = 3000)

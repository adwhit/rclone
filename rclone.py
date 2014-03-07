from flask import Flask, render_template, request
import db
from db import Lang, Task, Code
from sqlalchemy import or_, and_


class gb():
    all_langs = None
    all_tasks = None
    nullstr = "--"
    snippetdict = {}
    taskdict = {}


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

    content = {
            "taskdesc": "",
            "taskname": "",
            "tasklist": gb.tasklist,
            "code1": "",
            "code2": "",
            "lang1": "",
            "lang2": "",
            "langlist1": gb.langlist,
            "langlist2": gb.langlist
            }

    if request.method == "POST":
        print(request.form)
        content["lang1"] = notnull(request.form.get("col1"))
        content["lang2"] = notnull(request.form.get("col2"))
        content["taskname"] = notnull(request.form.get("taskname"))
        get_content(request.form, content)
    elif request.method == "GET":
        pass

    return render_template("index.html", **content)

def notnull(s):
    if s == gb.nullstr:
        return ""
    else:
        return s

def get_content(form, content):

    if content["taskname"]:
        content["taskdesc"] =  get_task_desc(content["taskname"])
        if content["lang1"]:
            content["code1"] = get_snippet(content["taskname"], content["lang1"])
        if content["lang2"]:
            content["code2"] = get_snippet(content["taskname"], content["lang2"])

    for k, v in content.items():
        if isinstance(v, str):
            print(k,v)
        else:
            print(k, v[:10])
            
    return content

def get_snippet(task, lang):
    if (task, lang) in gb.snippetdict:
        return gb.snippetdict[task,lang]
    else:
        session = db.Session()
        snippet = session.query(Code).filter(and_(Code.language==lang, Code.task==task)).one().text
        gb.snippetdict[task,lang] = snippet
        return snippet

def get_task_desc(task):
    if task in gb.taskdict:
        return gb.taskdict[task]
    else:
        session = db.Session()
        taskdesc = session.query(Task).filter_by(name=task).one().description
        gb.taskdict[task] = taskdesc
        return taskdesc

if __name__ == "__main__":
    #app.run(host="0.0.0.0")
    set_globals()
    app.run(debug=True, port = 3000)

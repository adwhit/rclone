from flask import Flask, render_template, request
import db
from db import Lang, Task, Code
from sqlalchemy import or_


class gb():
    all_langs = None
    all_tasks = None

def get_globals():
    session = db.Session()
    gb.all_langs = [l.name for l in session.query(Lang).all()]
    gb.all_tasks = [t.name for t in session.query(Task).all()]

app = Flask(__name__)

@app.route("/index", methods = ["GET", "POST"])
def index():
    langs1 = gb.all_langs
    langs2 = gb.all_langs
    tasks = gb.all_tasks
    session = db.Session()
    code = session.query(Code).filter(or_(Code.language=="Rust",Code.language=="Python")).\
            filter_by(task="Combinations").all()
    return render_template("index.html", tasks=tasks,langs1=langs1, langs2=langs2,
            code1=code[0].text, code2=code[1].text)

if __name__ == "__main__":
    #app.run(host="0.0.0.0")
    get_globals()
    app.run(debug=True, port = 3000)

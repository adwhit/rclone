from flask import Flask, render_template, request
import db
from db import Lang, Task, Code

session = db.Session()

app = Flask(__name__)

@app.route("/index", methods = ["GET", "POST"])
def index():
    code = session.query(Code).filter(Code.language=="Rust").\
            filter(Code.task=="Combinations").one().text
    return render_template("index.html", code=code)

if __name__ == "__main__":
    #app.run(host="0.0.0.0")
    app.run(debug=True, port = 3000)

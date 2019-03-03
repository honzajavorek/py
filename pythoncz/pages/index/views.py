from flask import render_template

from pythoncz import app


@app.route('/')
def index():
    return render_template('index.html')

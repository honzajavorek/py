from flask import render_template

from pythoncz import app


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/en/')
def index_en():
    return render_template('index.html')

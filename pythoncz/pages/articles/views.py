from pathlib import Path

import arrow
from flask import Response, render_template, jsonify

from pythoncz import app
from pythoncz.data import load_data


articles_data_path = Path(__file__).parent / 'articles_data.json'


@app.route('/articles/')
def articles():
    articles = load_data(articles_data_path, [], debug=app.debug)
    articles = articles[:10]
    return render_template('articles.html', articles=articles)


@app.route('/articles.xml')
def articles_rss():
    articles = load_data(articles_data_path, [], debug=app.debug)
    articles = articles[:50]
    rss_text = render_template('articles.xml',
                               date=arrow.utcnow(), articles=articles)
    return Response(rss_text, mimetype='application/xml')


@app.route('/articles.json')
def articles_json():
    articles = load_data(articles_data_path, [], debug=app.debug)
    return jsonify(list(articles))

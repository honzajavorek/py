from flask import Flask


app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False


import pythoncz.pages.index.views
import pythoncz.pages.events.views

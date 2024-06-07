from flask import Flask
import json

import TICSolver

app = Flask(__name__)


@app.route('/')
def index():
    return "waaaa"


@app.route('/TICSolver/<str:rowPag>')
def TICSolver(rowPag):
    rowPag = json.loads(rowPag)
    correct_answers = TICSolver.extract_correct_answers(rowPag)
    return json.dumps(correct_answers)


app.run(host='0.0.0.0', port=9000, ssl_context=(
    '/etc/letsencrypt/live/fdiaznem.me/fullchain.pem',
    '/etc/letsencrypt/live/fdiaznem.me/privkey.pem'))

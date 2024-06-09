from flask import Flask, render_template, request, redirect, url_for
import os
import tempfile
import json
import TICSolver



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/')
def index():
    return "waaaa"


@app.route('/ticsolver', methods=['GET', 'POST'])
def ticsolver():
    return render_template('upload.html')

@app.route('/ticsolver/results', methods=['POST'])
def results():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            rowpag_data = TICSolver.extract_html_data(file_path)
            os.remove(file_path)
            if rowpag_data:
                correct_answers = TICSolver.extract_correct_answers(rowpag_data)
                return render_template('results.html', answers=correct_answers)
            else:
                return "Error: No data extracted from the file."
        else:
            return "Error: No file uploaded."


# app.run(host='0.0.0.0', port=9000, ssl_context=(
#     '/etc/letsencrypt/live/fdiaznem.me/fullchain.pem',
#     '/etc/letsencrypt/live/fdiaznem.me/privkey.pem'))

app.run(port=4000)

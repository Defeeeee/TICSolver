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
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)

            rowpag_data = TICSolver.extract_html_data(filename)
            os.remove(filename)  # Delete file after processing

            if rowpag_data:
                correct_answers = TICSolver.extract_correct_answers(rowpag_data)
                return render_template('results.html', answers=correct_answers)
            else:
                return "No data extracted."

    return render_template('upload.html')


app.run(host='0.0.0.0', port=9000, ssl_context=(
    '/etc/letsencrypt/live/fdiaznem.me/fullchain.pem',
    '/etc/letsencrypt/live/fdiaznem.me/privkey.pem'))

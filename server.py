import os
import tempfile

from flask import Flask, render_template, request, redirect, url_for

import TICSolver

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


@app.route('/', methods=['GET', 'POST'])
def ticsolver():
    return render_template('upload.html')


@app.route('/results', methods=['POST'])
def results():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if not file.filename.lower().endswith('.html'):
                return render_template('error.html', error="Error: El archivo no es un archivo HTML.", isNotFound=True)
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
        except Exception as e:
            return render_template('error.html', error=str(e), isNotFound=("codec can't decode" in str(e)))

if __name__ == '__main__':
    app.run(debug=True)

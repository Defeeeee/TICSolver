[![Commit Check](https://github.com/commit-check/commit-check-action/actions/workflows/commit-check.yml/badge.svg)](https://github.com/commit-check/commit-check-action/actions/workflows/commit-check.yml)
# TICSolver - HTML Answer Extractor for TIC ORT

This Python script extracts correct answers from HTML files containing quiz or assessment data, specifically designed to
work with TIC ORT educational platform quizzes. It's designed to handle a variety of question formats, including
multiple-choice and matching questions.

## Features

* Extracts correct answers from TIC ORT HTML files in a structured format (JSON).
* Supports various question types:
    * MUL1R (single correct answer)
    * RELLE (multiple correct answers)
    * RELAC questions (various formats)
* Truncates long question titles for readability.
* Option to save extracted data to a JSON file or print it to the console.
* Robust error handling for JSON parsing.

## Web Application interface

No installation needed! Access TICSolver directly from your web browser
at [ticsolver.fdiaznem.me](https://ticsolver.fdiaznem.me)

## Prefer to run TICSolver locally? Here's a quick guide (requires Python 3):

### Requirements

* Python 3.x
* BeautifulSoup4 (`pip install beautifulsoup4`)

### Installation (Locally running)

1. Make sure you have Python 3 installed. You can check by running:

```bash
python --version
```

2. Install BeautifulSoup4:

```Bash
pip install beautifulsoup4
```

### Usage

Clone or download this repository:

```bash
git clone https://github.com/Defeeeee/TICSolver.git
```

Or download the ZIP file and extract it.

Navigate to the project directory:

```Bash
cd TICSolver
```

Run the script:

```Bash
python TICSolver.py
```

Enter the path to your HTML file:

You'll be prompted to enter the relative or absolute path to the HTML file containing the TIC ORT quiz data.

Save or print results:

The script will ask if you want to save the extracted data to a JSON file (correct_answers.json) or print it to the
console.

## How It Works

The script uses BeautifulSoup to parse the HTML file and locate the quiz data (often embedded in <script> tags or
specific HTML elements).
It extracts the relevant question data, including the question title, type, and correct answers.
Depending on the question type, it processes and formats the correct answers accordingly.
Finally, it provides options to save the structured data to a JSON file or print it directly.

### Example Output (JSON)

```JSON
[
  {
    "title": "What is the capital of France?",
    "correct_answer": [
      "Paris"
    ]
  },
  {
    "title": "Match the following countries...",
    "correct_answer": {
      "1": "Tokyo",
      "2": "Berlin"
    }
  }
]
```

## Disclaimer

This script is designed for educational purposes and to help with studying or reviewing quiz content from TIC ORT.
Please use it responsibly and with respect for intellectual property.

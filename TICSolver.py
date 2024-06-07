import json
from bs4 import BeautifulSoup


def extract_html_data(html_file):
    """
    Extracts and parses 'rowPag' data from an HTML file's script tag.

    Args:
        html_file (str): Path to the HTML file.

    Returns:
        dict: The parsed 'rowPag' data as a Python dictionary, or None if not found.
    """
    with open(html_file, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')

    for script in soup.find_all('script'):
        if 'rowPag' in script.text:
            try:
                # More robust extraction using slicing to find the start and end markers
                rowpag_data = json.loads(script.text.split('rowPag = ')[1].split('}]}}}};')[0] + '}]}}}}')
                return rowpag_data
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing 'rowPag' data: {e}")
                return None

    print("No 'rowPag' data found in the HTML file.")
    return None


def extract_correct_answers(data):
    """
    Extracts truncated titles and correct answers for various question types, reversing the answer format for RELLE and RELAC types.

    Args:
        data (dict): The loaded rowPag data.

    Returns:
        list: A list of dictionaries, each containing a truncated title and correct answer(s).
    """
    correct_answers = []

    for page_id, page_data in data.items():
        for question_id, question_data in page_data["questions"].items():
            title = question_data["title"][:100]  # Truncate title to 100 characters
            question_type = question_data["type"]
            correct_answer = []  # Initialize as a list

            # Common logic for MUL1R, MULNR
            if question_type in ["MUL1R", "MULNR"]:
                correct_answer = [opt["title"] for opt in question_data["options"] if opt.get("correct") == "true"]

            elif question_type == "RELLE":
                correct_answer = {opt["orden"]: opt["correct"] for opt in question_data["options"] if
                                  opt["correct"] != "null"}

            elif question_type == "RELAC":
                correct_answer = {int(opt["correct"]): opt["title"] for opt in question_data["options"] if
                                  opt["optionType"] == "3"}

            correct_answers.append({"title": title, "correct_answer": correct_answer})

    return correct_answers


def save_to_json(data, json_file):
    """Saves the extracted data to a JSON file."""
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data extracted and saved to '{json_file}'")


# Main execution
html_file_path = '/Users/defeee/Downloads/Función homográfica - Matematica - Campus Virtual ORT.html'
json_file_path = 'correct_answers.json'

rowpag_data = extract_html_data(html_file_path)
if rowpag_data:
    correct_answers = extract_correct_answers(rowpag_data)
    save_decision = input("Do you want to save the data to a JSON file? (y/n): ").lower()
    if save_decision == 'y':
        save_to_json(correct_answers, json_file_path)
    elif save_decision == 'n':
        print("Data not saved.")
        if input("Do you want to print the data? (y/n): ").lower() == 'y':
            print(json.dumps(correct_answers, indent=4))
else:
    print("No data to save.")

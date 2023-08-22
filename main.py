from bs4 import BeautifulSoup
import requests
import json
import re
import random

import tkinter as tk
import time


WORD_PATTERN = re.compile(r'(?<=\|).*?(?=])')
NON_ALPHA_PATTERN = re.compile(r'[^A-Za-z]')


def load_if_exists_else_blank(path: str) -> dict:
    try:
        with open(path, 'r') as infile:
            data = json.load(infile)
            # print(f'{path} already exists so will be updated with new words.\n'
            #       f'This will replace the existing language list if it already exists.')
            return data
    except FileNotFoundError:
        # print(f'{path} does not exist; creating.')
        return {}
    except json.JSONDecodeError:
        # print(f"{path} exists but can't be read as JSON. Will overwrite.")
        return {}


def save_to_file(data: str, path: str):
    with open(path, 'w') as outfile:
        outfile.write(data)


def fetch_api_json(wiki_api_link: str) -> dict:
    response = requests.get(wiki_api_link)
    # Check if the content type is JSON
    if 'application/json' in response.headers.get('Content-Type', ''):
        return response.json()

    # If not JSON, revert to the original method using BeautifulSoup
    soup = BeautifulSoup(response.content, features='html.parser')
    pre_text = soup.find('pre').text if soup.find('pre') else ""
    try:
        return json.loads(pre_text)
    except json.JSONDecodeError:
        return {}


def get_content_from_json(json_data: dict, keys: list) -> str:
    try:
        for key in keys:
            json_data = json_data[key]
        return json_data
    except (KeyError, IndexError, TypeError):
        return ""


def fetch_top_words_from_wiki(wiki_api_link: str) -> list:
    json_data = fetch_api_json(wiki_api_link)
    words_list = get_content_from_json(json_data, ['query', 'pages', 0, 'revisions', 0, 'slots', 'main', 'content'])
    return WORD_PATTERN.findall(words_list)


def get_single_words_from_list(input_list: list, shortest_word: int = 1) -> list:
    return [
        word for word in input_list
        if ' ' not in word and len(NON_ALPHA_PATTERN.sub('', word)) >= shortest_word
    ]


def save_words_list_with_update(words_list: list, language: str, save_path: str):
    existing_data = load_if_exists_else_blank(save_path)
    existing_data.update({language: words_list})
    save_to_file(json.dumps(existing_data, indent=4), save_path)


MAX_CHARACTERS_PER_LINE = 100


def generate_exercise(number_of_lines: int, top_n_words: int, language: str, ignore_characters_list: list = None) -> list:
    words_dict = load_if_exists_else_blank('filtered_keywords.json')
    if language not in words_dict:
        return []

    if ignore_characters_list is None:
        ignore_characters_list = []

    cleaned_words = get_word_list(words_dict[language][:top_n_words], ignore_characters_list)

    if not cleaned_words:
        return []

    generated_exercise = []
    new_line = []
    char_count = 0

    while len(generated_exercise) < number_of_lines:

        new_word = random.choice(cleaned_words)

        if char_count + len(new_word) + 1 > MAX_CHARACTERS_PER_LINE:
            generated_exercise.append(new_line)
            new_line = [new_word]
            char_count = len(new_word)
        else:
            new_line.append(new_word)
            char_count += len(new_word) + 1

    return generated_exercise


def get_word_list(words: list, ignore_list: list) -> list:
    ignore_set = set(ignore_list)
    return [word for word in words if not any(ignored_str in word for ignored_str in ignore_set)]


start_time = None

def start_test():
    global start_time
    start_time = time.time()
    # You can also change the state of the user_input text widget to 'normal' or 'disabled' as needed.
    user_input.config(state=tk.NORMAL)

def reset_test():
    user_input.delete(1.0, tk.END)
    result_display.config(text="Your result will be displayed here...")


def calculate_result(event):
    end_time = time.time()
    elapsed_time = end_time - start_time
    typed_text = user_input.get(1.0, tk.END).strip()
    wpm = (len(typed_text.split()) / elapsed_time) * 60
    # ... You'll also want to calculate accuracy here
    result_display.config(text=f"Your speed is: {wpm:.2f} WPM")



if __name__ == '__main__':
    # url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&titles=Wiktionary:Frequency_lists/English' \
    #       '/Wikipedia_(2016)&rvslots=*&rvprop=content&formatversion=2'
    # words = fetch_top_words_from_wiki(url)
    # save_words_list_with_update(words, 'english', 'raw_keywords.json')
    # save_words_list_with_update(get_single_words_from_list(words, 2), 'english', 'filtered_keywords.json')

    # for i in range(10):
    #     print('----')
    #     print(f'Top {(i + 1) * 100} words')
    #     print('----')
    #     exercise = generate_exercise(10, (i + 1) * 100, 'english', ['\'', '.', '-', '/', 'a', 'e', 'th'])
    #     for line in exercise:
    #         print(' '.join(line))
    #
    #     print('----')

    exercise = generate_exercise(10, 200, 'english', ['\'', '.', '-', '/'])

    root = tk.Tk()
    root.title("Typing Speed Test")

    # root.mainloop()
    test_text = tk.Label(root, text=f"{' '.join(exercise[0])}\n{' '.join(exercise[1])}", justify='left')
    test_text.pack()

    user_input = tk.Text(root, height=5, width=40)
    user_input.pack()

    start_button = tk.Button(root, text="Start", command=start_test)
    start_button.pack()

    reset_button = tk.Button(root, text="Reset", command=reset_test)
    reset_button.pack()

    result_display = tk.Label(root, text="Your result will be displayed here...")
    result_display.pack()
    user_input.bind('<Return>', calculate_result)

    root.mainloop()


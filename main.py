import string

from bs4 import BeautifulSoup
import requests
import json
import re
import random

import tkinter as tk
import time
from functools import partial
import copy

WORD_PATTERN = re.compile(r'(?<=\|).*?(?=])')
NON_ALPHA_PATTERN = re.compile(r'[^A-Za-z]')

FIRST_LINE = '1.0'
SECOND_LINE = '2.0'
HIGHLIGHT_TAG = 'highlight'
MISTYPED_TAG = 'mistyped'

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


def reset_test(result_display):
    user_input.delete(1.0, tk.END)
    result_display.config(text="Your result will be displayed here...")


def calculate_result(event, result_display):
    end_time = time.time()
    elapsed_time = end_time - start_time
    typed_text = user_input.get(1.0, tk.END).strip()
    wpm = (len(typed_text.split()) / elapsed_time) * 60
    # ... You'll also want to calculate accuracy here
    result_display.config(text=f"Your speed is: {wpm:.2f} WPM")


def add_tag(widget, tag_name, start_index, end_index):
    widget.tag_add(tag_name, f'1.{start_index}', f'1.{end_index}')


def remove_tag(widget, tag_name, start_index, end_index):
    widget.tag_remove(tag_name, f'1.{start_index}', f'1.{end_index}')


def on_key_release(event, text_widget, exercise, tracker, curr_line):
    typed = user_input.get().strip()

    curr_line = exercise[tracker['curr_line_index']]
    curr_word = curr_line[tracker['curr_word_index']]

    if not typed:
        start_index = 0 if tracker['curr_word_index'] == 0 else len(
            ' '.join(curr_line[:tracker['curr_word_index']])) + 1
        end_index = start_index + len(curr_word)
        remove_tag(text_widget, MISTYPED_TAG, start_index, end_index)
        user_input.delete(0, tk.END)
        return

    if event.keysym == 'space':
        is_correct = (typed == curr_word)
        tracker['typed_words'].append({'word': curr_word, 'spelling': typed, 'correct': is_correct})

        if (tracker['curr_word_index'] + 1) >= len(curr_line):
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(FIRST_LINE, SECOND_LINE)
            tracker['curr_line_index'] += 1
            tracker['curr_word_index'] = 0
            new_line = exercise[tracker['curr_line_index'] + 1]
            text_widget.insert(tk.END, '\n' + ' '.join(new_line))
            text_widget.config(state=tk.DISABLED)
            highlight_start = 0
            highlight_end = len(exercise[tracker['curr_line_index']][0])
        else:
            error_start = 0 if tracker['curr_word_index'] == 0 else len(' '.join(curr_line[:tracker['curr_word_index']])) + 1
            error_end = error_start + len(curr_word)
            if is_correct:
                remove_tag(text_widget, MISTYPED_TAG, error_start, error_end)
            else:
                add_tag(text_widget, MISTYPED_TAG, error_start, error_end)

            tracker['curr_word_index'] += 1
            highlight_start = len(' '.join(curr_line[:tracker['curr_word_index']])) + 1
            highlight_end = highlight_start + len(curr_line[tracker['curr_word_index']])

        text_widget.tag_remove(HIGHLIGHT_TAG, '1.0', tk.END)
        add_tag(text_widget, HIGHLIGHT_TAG, highlight_start, highlight_end)
        user_input.delete(0, tk.END)
        return

    is_correct_so_far = (typed == curr_word[:len(typed)])
    start_index = 0 if tracker['curr_word_index'] == 0 else len(' '.join(curr_line[:tracker['curr_word_index']])) + 1
    end_index = start_index + len(curr_word)
    if is_correct_so_far:
        remove_tag(text_widget, MISTYPED_TAG, start_index, end_index)
    else:
        add_tag(text_widget, MISTYPED_TAG, start_index, end_index)



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

    # root.mainloop()
    root = tk.Tk()
    root.title("Typing Test")

    # Label to display the text-to-copy
    text_to_copy = f'{" ".join(exercise[0])}\n{" ".join(exercise[1])}'
    # Text widget for displaying the text-to-copy
    text_widget = tk.Text(root, height=2, width=110)
    text_widget.insert("1.0", text_to_copy)
    text_widget.config(state=tk.DISABLED)  # make it read-only
    text_widget.pack(pady=20)

    # Style for highlighting
    text_widget.tag_configure("highlight", background="yellow")
    text_widget.tag_configure("mistyped", foreground="red")
    text_widget.tag_add("highlight", '1.0', f'1.{len(exercise[0][0])}')

    tracker = []
    tracker_2 = {'curr_line_index': 0, 'curr_word_index': 0, 'typed_words': []}
    current_line = []
    # Entry for the user to type into
    user_input = tk.Entry(root, width=50)
    user_input.pack(pady=20)
    user_input.bind('<KeyRelease>', partial(on_key_release, text_widget=text_widget, exercise=exercise, tracker=tracker_2, curr_line=current_line))
    root.mainloop()

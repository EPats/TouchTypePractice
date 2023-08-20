from bs4 import BeautifulSoup
import requests
import json
import re
import random


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


def generate_exercise(number_of_words: int, top_n_words: int, language: str) -> list:
    words_dict = load_if_exists_else_blank('filtered_keywords.json')
    if language not in words_dict:
        return []
    language_top_words = words_dict[language]
    top_words = language_top_words[:top_n_words]
    return [random.choice(top_words) for _ in range(number_of_words)]



if __name__ == '__main__':
    # url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&titles=Wiktionary:Frequency_lists/English' \
    #       '/Wikipedia_(2016)&rvslots=*&rvprop=content&formatversion=2'
    # words = fetch_top_words_from_wiki(url)
    # save_words_list_with_update(words, 'english', 'raw_keywords.json')
    # save_words_list_with_update(get_single_words_from_list(words, 2), 'english', 'filtered_keywords.json')
    for i in range(10):
        print(' '.join(generate_exercise(50, (i + 1) * 30, 'english')))
        print('----')


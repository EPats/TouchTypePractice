from bs4 import BeautifulSoup
import requests
import json
import re
import os.path


def load_if_exists_else_blank(path: str) -> dict:
    json_data = {}
    if os.path.isfile(path):
        try:
            with open(path, 'r') as infile:
                json_data = json.load(infile)
                print(f'{path} already exists so will be updated with new words.\n'
                      f'This will replace the existing language list if it already exists.')
        except:
            print(f"{path} exists but can't be read as JSON. Will overwrite")
    return json_data


def save_to_file(data: str, path: str):
    with open(path, 'w') as outfile:
        outfile.write(data)


def fetch_api_json(wiki_api_link: str) -> dict:
    response = requests.get(wiki_api_link)
    soup = BeautifulSoup(response.content, features='html.parser')
    return json.loads(soup.find('pre').text)


def recursive_get_from_json(json_data, keys: list, index: int = 0):
    if index >= len(keys):
        return json_data
    if (type(json_data) is dict and keys[index] not in json_data) \
            or (type(json_data) is list and type(keys[index]) is not int and keys[index] >= len(json_data)):
        return None
    return recursive_get_from_json(json_data[keys[index]], keys, index + 1)


def fetch_top_words_and_save(language: str, wiki_api_link: str, save_path: str) -> list:
    json_data = fetch_api_json(wiki_api_link)
    words_list = recursive_get_from_json(json_data, ['query', 'pages', 0, 'revisions', 0, 'slots', 'main', 'content'])
    if not words_list:
        return []
    most_common_words = re.findall(r'(?<=\|).*?(?=\])', words_list)
    raw_common_words_data = load_if_exists_else_blank(save_path)
    raw_common_words_data.update({language: most_common_words})
    save_to_file(json.dumps(raw_common_words_data, indent=4), save_path)
    return most_common_words


def get_single_words_from_list(input_list: list, shortest_word: int = 1) -> list:
    return [word for word in input_list if ' ' not in word and len(re.sub(r'[^A-Za-z]', '', word)) >= shortest_word]


url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&titles=Wiktionary:Frequency_lists/English' \
      '/Wikipedia_(2016)&rvslots=*&rvprop=content&formatversion=2'
words = fetch_top_words_and_save('english', url, 'raw_keywords.json')
print(get_single_words_from_list(words, 2))

import re

import requests

from search_params import HEADERS
from utils import get_file_path, load_previous_data, save_data_to_file


def get_manga_chapters():
    """Check for new chapters on comicpark.org.

    Returns:
        list: urls
    """
    base_url = 'https://comicpark.org'
    file_path = get_file_path('mangas.json')
    previous_chapters = load_previous_data(file_path)
    result = []
    for manga, previous_chapter in previous_chapters.items():
        manga_title = f'/title/{manga}'
        url = f'{base_url}{manga_title}'
        response = requests.get(url, headers=HEADERS)
        mathces = re.findall(rf'({re.escape(manga_title)}.*?)"', response.text)
        if mathces:
            last_chapter = mathces[-1]
            if last_chapter != previous_chapter:
                result.append(f'{base_url}{last_chapter}')
                previous_chapters[manga] = last_chapter       
    save_data_to_file(file_path, previous_chapters)
    return result
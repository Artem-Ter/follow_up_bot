import json
import os

from search_params import BACKUP_DIR


def save_data_to_file(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file)


def load_previous_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return dict()


def get_file_path(file_name):
    file_path = os.path.join(BACKUP_DIR, file_name)
    return file_path

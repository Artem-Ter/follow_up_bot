
import json
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from utils import (get_file_path,
                   load_previous_data,
                   save_data_to_file)
from search_params import (PRICES,
                           SEARCH_URLS,
                           BAIROS)


def get_ads(url):
    service = Service(executable_path=ChromeDriverManager().install())
    # Запуск веб-драйвера для Chrome.
    driver = webdriver.Chrome(service=service)
    # Открытие страницы по заданному адресу.
    driver.get(url)
    data = driver.page_source
    # Extracting JSON string from data
    start_index = data.find('{"props":{"pageProps":')
    end_index = data.find('</script>', start_index)
    json_data = data[start_index:end_index]
    # Loading JSON data
    parsed_data = json.loads(json_data)
    ads = parsed_data['props']['pageProps']['ads']
    driver.quit()
    return ads


def check_posts(url, previous_data, new_posts, last_update):
    flag = True
    page = 1
    while flag:
        check_url = f'{url}{page}'
        ads = get_ads(check_url)
        if not ads:
            break
        # Extract data from ads and update new_posts and previous_data
        for ad in ads:
            if 'subject' not in ad.keys():
                continue
            date = int(ad['date'])
            is_fixed_on_top = ad['fixedOnTop']
            # Check if the ad was publicated after last update
            if date <= last_update and not is_fixed_on_top:
                flag = False
                break
            subject = ad['subject']
            ad_url = ad['url']
            price = ad['price']
            image_count = int(ad['imageCount'])
            category = ad['category']
            location = ad['location']
            properties_dict = get_properties(ad['properties'])
            size = properties_dict['size']
            # CONSIDERATION:
            # Possibility to have same title for different posts is low
            title = f"{subject}_{price}_{size}_{image_count}"
            dict_value = previous_data.get(title, 'Not found')
            ad_data = {
                'location': location,
                'category': category,
                'url': ad_url,
                'price': price,
                'size': size,
                'condominio': properties_dict['condominio'],
                'iptu': properties_dict['iptu'],
            }
            # Add data if post is realy new
            if dict_value == 'Not found':
                for key, value in ad_data.items():
                    post_item = new_posts.get(key, [])
                    post_item.append(value)
                    new_posts[key] = post_item
            # Update old posts if they were refreshed
            # and add new ones to previous_data
            previous_data[title] = ad_data
        page += 1


def get_properties(ad_properties):
    result = {
        'condominio': 1,
        'iptu': 1,
        'size': 1,
    }
    for item in ad_properties:
        name = item['name']
        if result.get(name, 0):
            result[name] = item['value']
    return result


def get_url(value, region, key, details):
    url = (f'{value}{region}'
           f'?pe={PRICES[key][region]}'
           f'&ps={PRICES["min_price"]}')
    for code in details.values():
        url += f'&sd={code}'

    return f'{url}&sf=1&o='


def get_new_posts_file():
    date_file_path = get_file_path('last_update.json')
    last_update_dict = load_previous_data(date_file_path)
    last_update = int(last_update_dict['date'])
    ads_file_path = get_file_path('checked_ads.json')
    previous_data = load_previous_data(ads_file_path)
    new_posts = dict()
    start_update = int(datetime.now().timestamp())
    for key, value in SEARCH_URLS.items():
        for region, district in BAIROS.items():
            url = get_url(value, region, key, district)
            check_posts(url, previous_data, new_posts, last_update)

    file_name = 'new_posts.xlsx'
    if new_posts:
        # Convert dictionary to a DataFrame
        df = pd.DataFrame(new_posts)
        # Convert DataFrame to XLS file
        df.to_excel(file_name, index=False)

    save_data_to_file(ads_file_path, previous_data)
    last_update_dict['date'] = start_update
    save_data_to_file(date_file_path, last_update_dict)
    return file_name

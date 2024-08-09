import os
import csv
import logging
from session import kuma
from datetime import datetime


INFO_CSV = 'data/info.csv'
ITEMS = ['timestamp', 'time', 'foing', 'foer', 'tweets', 'media', 'likes']

scraper = kuma.scraper


def get_user_info(user_id: int) -> dict:
    data = scraper.users_by_ids([user_id])
    users_data = data[0]
    user = users_data['data']['users'][0]
    user_info = user['result']['legacy']
    return user_info


def init_user_info():
    with open(INFO_CSV, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=ITEMS)
        writer.writeheader()


def write_user_info(user_info: dict):
    if not os.path.isfile(INFO_CSV):
        init_user_info()

    now = datetime.now()

    with open(INFO_CSV, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([
            int(now.timestamp()),
            now.strftime('%Y-%m-%d %H:%M:%S'),

            user_info['friends_count'],
            user_info['followers_count'],

            user_info['statuses_count'],
            user_info['media_count'],
            user_info['favourites_count'],
        ])

    logging.warning('[followers]\t' + 'Count: ' + user_info["followers_count"])


def query_fo(user_id: int = 3703623798):
    usr_nfo = get_user_info(user_id)
    write_user_info(usr_nfo)


if __name__ == '__main__':
    query_fo()

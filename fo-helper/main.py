import os
import json
import base64
import pickle
import tweepy
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler


def read_file(filename, encrypt=False):
    if encrypt:
        with open(filename, 'rb') as f:
            return base64.b64decode(f.read()).decode('utf-8')
    else:
        with open(filename, 'r') as f:
            return f.read()


def query_token(token_id):
    return read_file(f'token_{token_id}', True)


def notify(text, user='Real'):
    text = f'\[{user}] {text}'
    return os.system(f'/usr/local/bin/notify \"{text}\"')


twitter_token = json.loads(query_token('twitter'))
auth = tweepy.OAuthHandler(twitter_token['consumer_key'], twitter_token['consumer_secret'])
auth.set_access_token(twitter_token['access_token'], twitter_token['access_token_secret'])
kuma = tweepy.API(auth, wait_on_rate_limit=True)

with open('real.p', 'rb') as real_api:
    real = pickle.load(real_api)


class Data:
    def __init__(self):
        self.data = {}

    def update(self, key, value):
        self.data[key] = value
        length = ''
        if type(value) is list:
            length = len(value)
        print('[db] u: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + f' l: {length}')

    def get(self, key):
        return self.data[key]


fo_data = Data()


def check_real():
    print('[real] ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    km_f = kuma.get_friend_ids()
    km_fo = []
    for fo in tweepy.Cursor(kuma.get_follower_ids).items():
        km_fo.append(fo)
    fo_data.update('km_f', km_f)
    fo_data.update('km_fo', km_fo)

    foing = real.get_friend_ids()
    foer = real.get_follower_ids()

    new_fo = list(set(foer) - set(foing))
    for user in new_fo:
        if user not in km_f:
            user_info = real.get_user(user_id=user)
            real.create_block(user_id=user)
            real.destroy_block(user_id=user)
            msg = f'Cleared [@{user_info.screen_name}](https://twitter.com/{user_info.screen_name})'
            notify(msg)
            print(f'    {msg}')
        else:
            try:
                user_info = real.get_user(user_id=user)
                real.create_friendship(user_id=user)
                msg = f'Followed [@{user_info.screen_name}](https://twitter.com/{user_info.screen_name})'
                notify(msg)
                print(f'    {msg}')
            except Exception as e:
                print('    Error:', str(e))

    one_way = list(set(foing) - set(foer))
    for user in one_way:
        user_info = real.get_user(user_id=user)
        real.destroy_friendship(user_id=user)
        msg = f'Unfollowed [@{user_info.screen_name}](https://twitter.com/{user_info.screen_name})'
        notify(msg)
        print(f'    {msg}')


def check_kuma():
    print('[kuma] ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    km_f = fo_data.get('km_f')
    km_fo = fo_data.get('km_fo')

    for user in km_f:
        if user not in km_fo:
            try:
                user_info = kuma.get_user(user_id=user)
                msg = f'!!! [@{user_info.screen_name}](https://twitter.com/{user_info.screen_name}) unfollowed you!'
                notify(msg, user='Kuma')
                print(f'    {msg}')
            except Exception as e:
                msg = f'Error: {str(e)}'
                # notify(msg, user='Kuma')
                print(f'    {msg}')


if __name__ == '__main__':
    # while 114514:
    #     check()
    #     time.sleep(3600)
    scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(check_real, 'cron', minute=0)
    scheduler.add_job(check_kuma, 'cron', hour=0, minute=30)
    scheduler.start()

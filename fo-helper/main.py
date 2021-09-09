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


def notify(text):
    text = f'[Real] {text}'
    return os.system(f'/usr/bin/notify {text}')


twitter_token = json.loads(query_token('twitter'))
auth = tweepy.OAuthHandler(twitter_token['consumer_key'], twitter_token['consumer_secret'])
auth.set_access_token(twitter_token['access_token'], twitter_token['access_token_secret'])
kuma = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


with open('real.p', 'rb') as f:
    real = pickle.load(f)


def check():
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    km_f = kuma.friends_ids()

    foer = real.followers_ids()
    foing = real.friends_ids()

    new_fo = list(set(foer) - set(foing))
    for user in new_fo:
        if user not in km_f:
            real.create_block(user)
            real.destroy_block(user)
            msg = f'Cleared {user}'
            notify(msg)
            print(f'    {msg}')
        else:
            try:
                real.create_friendship(user)
                msg = f'Followed {user}'
                notify(msg)
                print(f'    {msg}')
            except Exception as e:
                print('    Error:', str(e))

    one_way = list(set(foing) - set(foer))
    for user in one_way:
        real.destroy_friendship(user)
        msg = f'Unfollowed {user}'
        notify(msg)
        print(f'    {msg}')


if __name__ == '__main__':
    # while 114514:
    #     check()
    #     time.sleep(3600)
    scheduler = BlockingScheduler()
    scheduler.add_job(check, 'cron', minute=0)
    scheduler.start()

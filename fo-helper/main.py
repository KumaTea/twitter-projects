import json
import time
import base64
import pickle
import tweepy
from datetime import datetime


def read_file(filename, encrypt=False):
    if encrypt:
        with open(filename, 'rb') as f:
            return base64.b64decode(f.read()).decode('utf-8')
    else:
        with open(filename, 'r') as f:
            return f.read()
def query_token(token_id):
    return read_file(f'token_{token_id}', True)


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
            print('    Successfully cleared', user)
        else:
            try:
                real.create_friendship(user)
                print('    Successfully followed', user)
            except Exception as e:
                print('    Error:', str(e))

    one_way = list(set(foing) - set(foer))
    for user in one_way:
        real.destroy_friendship(user)
        print('    Successfully unfollowed', user)


if __name__ == '__main__':
    while 114514:
        check()
        time.sleep(3600)
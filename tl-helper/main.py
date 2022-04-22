# Twitter Timeline Helper
# This script regularly fetch timeline,
# get ids not in followers, and check if blocked.
# block back if so or mute otherwise


import json
import base64
import tweepy
import logging
from tweepy.errors import TweepyException as TweepError
from apscheduler.schedulers.blocking import BlockingScheduler


def query_token(token_id=None, filename=None):
    filename = filename or f'token_{token_id}'
    with open(filename, 'rb') as f:
        return base64.b64decode(f.read()).decode('utf-8')


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

twitter_token = json.loads(query_token('twitter'))
auth = tweepy.OAuthHandler(twitter_token['consumer_key'], twitter_token['consumer_secret'])
auth.set_access_token(twitter_token['access_token'], twitter_token['access_token_secret'])
kuma = tweepy.API(auth, wait_on_rate_limit=True)

try:
    kuma._me = kuma.me()  # noqa
except AttributeError:
    kuma._me = kuma.get_user(screen_name='KumaTea0')


class Data:
    def __init__(self):
        self.data = {}

    def update(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, None)


fo_data = Data()


def update_data():
    km_fo = []
    for fo in tweepy.Cursor(kuma.get_follower_ids).items():
        km_fo.append(fo)
    km_fo.append(kuma._me.id)  # noqa
    fo_data.update('km_fo', km_fo)

    km_m = []
    for m in tweepy.Cursor(kuma.get_muted_ids).items():
        km_m.append(m)
    fo_data.update('km_m', km_m)
    return logging.info('[data] updated')


def check_locked(host, user):
    target_id = None
    target_screen_name = None
    if type(user) is int:
        target_id = user
    else:
        target_screen_name = user
    result = host.get_friendship(
        source_id=host.id,
        target_id=target_id,
        target_screen_name=target_screen_name)
    if result[0].blocked_by:
        return 1
    else:
        return 0  # not -1 for identifying locked


def check_blocked(host, user):
    try:
        _ = host.user_timeline(user_id=user, exclude_replies=False, include_rts=True)
        return -1
    except TweepError as e:
        if 'blocked' in str(e):
            return 1
        elif 'authorized' in str(e):
            return check_locked(host, user)
        elif 'exist' in str(e):
            return 0
        else:
            raise RuntimeError('Unknown error:', str(e))


def check_kuma():
    km_fo = fo_data.get('km_fo')
    km_m = fo_data.get('km_m')
    last_id = fo_data.get('last_id') or 0

    to_mute = []
    tl = kuma.home_timeline(count=200, since_id=last_id)

    for tweet in tl:
        if tweet.user.id not in km_fo:
            to_mute.append((tweet.user.id, tweet.user.screen_name))
        if tweet.entities['user_mentions']:
            for user in tweet.entities['user_mentions']:
                if user['id'] not in km_fo:
                    to_mute.append((user['id'], user['screen_name']))

    if to_mute:
        for user in to_mute:
            blocked = check_blocked(kuma, user[0])
            if blocked == 1:
                kuma.create_block(user_id=user[0])
                logging.warning(f'[kuma] blocked @{user[1]}')
            else:
                if user not in km_m:
                    kuma.create_mute(user_id=user[0])
                    logging.warning(f'[kuma] muted @{user[1]}')

    tl = sorted(tl, key=lambda x: x.id, reverse=True)
    fo_data.update('last_id', tl[0].id)

    return logging.info('[kuma] checked')


if __name__ == '__main__':
    update_data()

    scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(check_kuma, 'cron', minute=0)
    scheduler.add_job(update_data, 'cron', hour=0, minute=30)
    scheduler.start()

# Twitter Timeline Helper
# This script regularly fetch timeline,
# get ids not in followers, and check if blocked.
# block back if so or mute otherwise


import os
import tweepy
import logging
# import pickle
import subprocess
import configparser
from tqdm import tqdm
from datetime import datetime
from tweepy.errors import TweepyException as TweepError
from apscheduler.schedulers.blocking import BlockingScheduler


max_thread_length = 10
default_max_tweets = 200
last_id_file = 'last_id.txt'

config = configparser.ConfigParser(interpolation=None)
config_file = 'config.ini'
config.read(config_file)

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%m-%d %H:%M')
logger = logging.getLogger(__name__)
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)


def inform(message, pbar=None):
    log_msg = datetime.now().strftime('%m-%d %H:%M') + '\t' + message
    if isinstance(pbar, tqdm):
        # tqdm progress bar description
        pbar.set_description(log_msg)
    else:
        logger.info(log_msg)


auth = tweepy.OAuth1UserHandler(
    config['twitter']['api_key'],
    config['twitter']['api_sec'],
    config['twitter']['acc_tok'],
    config['twitter']['acc_sec']
)
kuma = tweepy.API(auth, wait_on_rate_limit=True)

safe_auth = tweepy.OAuth1UserHandler(
    config['twitter']['api_key'],
    config['twitter']['api_sec'],
    config['safe']['acc_tok'],
    config['safe']['acc_sec']
)
safe = tweepy.API(safe_auth, wait_on_rate_limit=True)


try:
    kuma._me = kuma.me()  # noqa
except AttributeError:
    kuma._me = kuma.get_user(screen_name='KumaTea0')


class TwitterDB:
    def __init__(self):
        self.last_id = 0
        self.cached_tweets = {}
        self.cache_hits = 0
        self.data = {}

    def update(self, key, value):
        self.data[key] = value
        # logger.info('[db] Updated {}.'.format(key))

    def get(self, key):
        # logger.info('[db] Got {}, len:{}.'.format(key, len(self.data.get(key, []))))
        return self.data.get(key, None)

    def reset(self, last_id):
        if last_id > self.last_id:
            self.last_id = last_id
            with open(last_id_file, 'w') as f:
                f.write(str(last_id))

        # logger.info('[db] Cached tweets: {}, cache hits: {}'.format(len(self.cached_tweets), self.cache_hits))
        self.cached_tweets = {}
        self.cache_hits = 0
        # return logger.info('[db] Reset.')


kuma_db = TwitterDB()


def get_tweet(tweet_id):
    # inform(f'[twi] Getting tweet {tweet_id}', pbar)
    if tweet_id in kuma_db.cached_tweets:
        kuma_db.cache_hits += 1
        return kuma_db.cached_tweets[tweet_id]
    else:
        try:
            tweet = kuma.get_status(tweet_id)
            kuma_db.cached_tweets[tweet_id] = tweet
            return tweet
        except tweepy.errors.Forbidden:
            return 'locked'
        except tweepy.errors.Unauthorized:
            return 'blocked'
        except tweepy.errors.NotFound:
            return 'deleted'


def get_tweet_type(tweet):
    # text, photo, video, gif
    if getattr(tweet, 'extended_entities', None):
        if tweet.extended_entities['media'][0]['type'] == 'photo':
            return 'photo'
        elif tweet.extended_entities['media'][0]['type'] == 'video':
            return 'video'
        elif tweet.extended_entities['media'][0]['type'] == 'animated_gif':
            return 'gif'
    return 'text'


def update_fo():
    # debug
    # if os.path.isfile('km_fo.p'):
    #     with open('km_fo.p', 'rb') as f:
    #         km_fo = pickle.load(f)
    #         kuma_db.update('km_fo', km_fo)
    #         return logging.info('[data] km_fo loaded from pickle')

    km_fo = []
    for fo in tweepy.Cursor(kuma.get_follower_ids).items():
        km_fo.append(fo)
    km_fo.append(kuma._me.id)
    kuma_db.update('km_fo', km_fo)

    # debug
    # with open('km_fo.p', 'wb') as f:
    #     pickle.dump(km_fo, f)

    return logging.info('[data] km_fo updated')


def startup():
    # read last mentioned id from file
    if os.path.exists(last_id_file):
        with open(last_id_file, 'r') as f:
            # do not use `write_last_id()` to avoid writing again
            kuma_db.last_id = int(f.read())

    update_fo()
    return logger.info('Startup complete.')


def check_locked(host, user):
    target_id = None
    target_screen_name = None
    if type(user) is int:
        target_id = user
    else:
        target_screen_name = user
    try:
        result = host.get_friendship(
            source_id=host._me.id,
            target_id=target_id,
            target_screen_name=target_screen_name)
        if result[0].blocked_by:
            return 1
        else:
            return 0  # not -1 for identifying locked
    except:
            return 0


def check_blocked(host, user):
    # inform(f'[twi] Checking {user}...', pbar)
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


# def check_status(host, user):
#     result = check_blocked(host, user)
#     if result == 1:
#         return 'blocked'
#     elif result == 0:
#         return 'locked'
#     elif result == -1:
#         return 'ok'


def check_muting(source_id=kuma._me.id, source_screen_name=kuma._me.screen_name, target_id=0, target_screen_name=None):
    assert target_id or target_screen_name
    result = kuma.get_friendship(
        source_id=source_id,
        source_screen_name=source_screen_name,
        target_id=target_id,
        target_screen_name=target_screen_name
    )[0]
    # there is a `blocking` and `blocked_by` attribute
    # but check if block is not achieved here
    return result.muting


def get_user_by_tweet_id(tweet_id):
    # since main account is block
    # we use the safe auth to check
    tweet = safe.get_status(tweet_id)
    return tweet.user


def get_thread_tweets(tweet_id, pbar=None):
    thread = []
    while len(thread) < max_thread_length:
        tweet = get_tweet(tweet_id)
        if type(tweet) is str:
            # inform(f'[twi] Tweet {tweet_id} status: {tweet}', pbar)
            if tweet == 'blocked':
                inform(f'[twi] Tweet {tweet_id} status: {tweet}', pbar)
                tweet_user = get_user_by_tweet_id(tweet_id)
                relationship = kuma.get_friendship(source_id=kuma._me.id, target_id=tweet_user.id)[0]
                if not relationship.blocking:
                    kuma.create_block(user_id=tweet_user.id)
                    subprocess.run([
                        '/usr/bin/notify',
                        '[tl] Found and blocked back: https://twitter.com/{}'.format(tweet_user.screen_name)])
                    logger.warning(f'[twi] Found and blocked {tweet_user.screen_name} (id: {tweet_user.id})', pbar)
                else:
                    # subprocess.run([
                    #     '/usr/bin/notify',
                    #     '[tl] Found already blocked: https://twitter.com/{}'.format(tweet_user.screen_name)])
                    logger.info(f'[twi] Already blocked {tweet_user.screen_name} (id: {tweet_user.id})', pbar)
            break
        thread.append(tweet)
        if tweet.in_reply_to_status_id:
            # inform(f'[twi] Found reply: {tweet.in_reply_to_status_id} -> {tweet.id}', pbar)
            tweet_id = tweet.in_reply_to_status_id
        # if quote
        elif tweet.is_quote_status:
            # inform(f'[twi] Found quote: {tweet.quoted_status_id} -> {tweet.id}', pbar)
            tweet_id = tweet.quoted_status_id
        else:
            break

    thread.sort(key=lambda x: x.id, reverse=False)  # sort by oldest first
    return thread


def clean_tl():
    km_fo = kuma_db.get('km_fo')
    last_id = kuma_db.last_id or None
    # logger.info(f'[twi] Last id: {last_id} (from db)')

    to_mute = {}
    to_mute_ids = []
    tl = kuma.home_timeline(count=default_max_tweets, since_id=last_id)
    # logger.info(f'[twi] Got {len(tl)} tweets.')

    if not tl:
        return None

    now_str = datetime.now().strftime('%m-%d %H:%M')
    # pbar = tqdm(tl, desc=now_str + '\t' + '[twi] Processing tweets')
    for tweet in tl:
        kuma_db.cached_tweets[tweet.id] = tweet
        thread = get_thread_tweets(tweet.id)
        for t in thread:
            if get_tweet_type(t) == 'text':
                if t.entities and t.entities['user_mentions']:
                    for user in t.entities['user_mentions']:
                        if user['id'] not in km_fo:
                            # inform(f'[twi] Found mention: @{user["screen_name"]} in {t.id}', pbar)
                            to_mute[user['id']] = user['screen_name']
                            to_mute_ids.append(user['id'])
                if t.user.id not in km_fo:
                    # inform(f'[twi] Found text: @{t.user.screen_name} in {t.id}', pbar)
                    to_mute[t.user.id] = t.user.screen_name
                    to_mute_ids.append(t.user.id)
    to_mute_ids = list(set(to_mute_ids))
    if to_mute_ids:
        logging.warning(f'[twi] Found {len(to_mute_ids)} users to mute.')
        for user in to_mute_ids:
            blocked = check_blocked(kuma, user)
            if blocked == 1:
                kuma.create_block(user_id=user)
                logging.warning(f'[kuma] blocked @{to_mute[user]}')
            else:
                try:
                    kuma.create_mute(user_id=user)
                    logging.warning(f'[kuma] muted @{to_mute[user]}')
                except:
                    logger.error(f'[kuma] Failed to mute @{to_mute[user]}')
    if tl:
        tl = sorted(tl, key=lambda x: x.id, reverse=True)
        kuma_db.reset(last_id=tl[0].id)

    # return logging.info('[kuma] checked')


if __name__ == '__main__':
    startup()
    clean_tl()

    scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(clean_tl, 'cron', minute='*/5')
    scheduler.add_job(update_fo, 'cron', hour=0, minute=30)
    scheduler.start()

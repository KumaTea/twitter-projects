import time
import logging
from session import kuma


il_kw = [
    # common keywords in bio of illustrators

    # drawing
    '绘', '絵', '描',
    'rkgk', 'らくがき',
    'illust',
    '創作',

    # platforms
    'pixiv',
    'skeb',

    # copyright
    '転載',
    'AI',
]


def get_tl() -> list[dict]:
    return kuma.account.home_timeline()


def get_tl_tweets() -> list[dict]:
    tl = get_tl()
    tweets = []
    for tl_part in tl:
        tweets_entries = tl_part['data']['home']['home_timeline_urt']['instructions'][0]['entries']
        tweets.extend(tweets_entries)
    return tweets


def is_valid_tweet(tweet: dict) -> bool:
    return 'itemContent' in tweet['content'] and 'tweet_results' in tweet['content']['itemContent']


def get_tweet_result(tweet: dict) -> dict:
    tweet_result = tweet['content']['itemContent']['tweet_results']['result']
    if 'tweet' in tweet_result:
        tweet_result = tweet_result['tweet']
    return tweet_result


def get_tweet_user(tweet_result: dict) -> dict:
    user_result = tweet_result['core']['user_results']['result']
    return user_result


def get_user_type(user_result: dict) -> str:
    legacy = user_result['legacy']

    followed_by: bool = 'followed_by' in legacy and legacy['followed_by']
    if followed_by:
        return 'follower'

    # following = 'following' in legacy and legacy['following']
    muting: bool = 'muting' in legacy and legacy['muting']
    if muting:
        return 'muted'

    description: str = legacy['description']
    # for kw in il_kw:
    #     if kw in description:
    if any(kw in description for kw in il_kw):
        return 'illustrator'

    return 'unknown'


def get_user_id(user_result: dict) -> str:
    return user_result['rest_id']


def mute_user(user_result: dict) -> bool:
    user_type = get_user_type(user_result)

    if user_type == 'illustrator':
        return False
    elif user_type == 'follower':
        return False
    elif user_type == 'muted':
        return False
    else:
        # user_id = get_user_id(user_result)
        # kuma.account.mute(user_id)
        return True


def clean_tl():
    tweets = get_tl_tweets()
    users_to_mute = []
    for tweet in tweets:
        if not is_valid_tweet(tweet):
            continue

        tweet_result = get_tweet_result(tweet)
        user_result = get_tweet_user(tweet_result)
        user_muting = mute_user(user_result)
        if user_muting:
            user_name = user_result['legacy']['name']
            user_username = user_result['legacy']['screen_name']
            tweet_text = tweet_result['legacy']['full_text']
            tweet_text = tweet_text.replace('\n', ' ')
            logging.warning(f'[cleaner]\tMuting: {user_name} (@{user_username[:16]:<16})\t{tweet_text[:32]}')
            user_id = get_user_id(user_result)
            users_to_mute.append(user_id)

    for user_id in users_to_mute:
        kuma.account.mute(user_id)
        time.sleep(1)

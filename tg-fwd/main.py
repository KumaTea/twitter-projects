# Forward tweets to a Telegram channel


import os
import sys
import json
import base64
import tweepy
import logging
from zoneinfo import ZoneInfo
from telegram import Bot, InputMediaPhoto
from telegram.utils.helpers import escape_markdown


twitter_id = 1243884873451835392  # @realKumaTea
tg_bot_id = 781791363  # @KumaTea_bot
channel_id = -1001713500645  # @KumaLogs
last_id_file = 'last_id.txt'
delay_time = 60 * 60  # 1 hour

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def query_token(token_id=None, filename=None):
    filename = filename or f'token_{token_id}'
    with open(filename, 'rb') as f:
        return base64.b64decode(f.read()).decode('utf-8')


twitter_token = json.loads(query_token('twitter'))
auth = tweepy.OAuthHandler(twitter_token['consumer_key'], twitter_token['consumer_secret'])
auth.set_access_token(twitter_token['access_token'], twitter_token['access_token_secret'])
twi = tweepy.API(auth, wait_on_rate_limit=True)

tg = Bot(query_token(tg_bot_id))


def get_latest_tweet_id(user_id):
    return twi.user_timeline(user_id=user_id, count=1)[0].id


def get_new_tweets(user_id, last_id):
    return twi.user_timeline(user_id=user_id, since_id=last_id, exclude_replies=True, include_rts=False)


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


def get_tweet_photos(tweet):
    # assert that the tweet has photos
    return [i['media_url_https'] for i in tweet.extended_entities['media']]


def get_tweet_video(tweet):
    return tweet.extended_entities['media'][0]['video_info']['variants'][0]['url']


def get_tweet_gif(tweet):
    # same as video!
    return get_tweet_video(tweet)


def get_media_entities_url(tweet):
    return tweet.entities['media'][0]['url']


def get_urls_in_tweet(tweet):
    if getattr(tweet, 'entities', None):
        if tweet.entities.get('urls', None):
            return [
                {'url': url['url'],
                 'display_url': url['display_url'],
                 'expanded_url': url['expanded_url']
                 } for url in tweet.entities['urls']
            ]
    return []


def prepare_album(tweet, caption=None, parse_mode=None):
    album = [InputMediaPhoto(i) for i in get_tweet_photos(tweet)]
    if caption:
        album[0] = InputMediaPhoto(get_tweet_photos(tweet)[0], caption=caption, parse_mode=parse_mode)
    return album


def get_tweet_time(tweet):
    tweet_time = tweet.created_at.astimezone(tz=ZoneInfo('Asia/Shanghai'))
    tweet_time_str = tweet_time.strftime('%m/%d %H:%M')
    return tweet_time_str


def forward_tweet(tweet, no_notify=True):
    tweet_type = get_tweet_type(tweet)
    urls = get_urls_in_tweet(tweet)

    tweet_text = tweet.text
    tweet_text = escape_markdown(tweet_text, version=2)

    if urls:
        for url in urls:
            tweet_text.replace(url['url'], f'[{url["display_url"]}]({url["expanded_url"]})')

    tweet_time = get_tweet_time(tweet)
    tweet_url = f'https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}'
    text = f'[里推 {tweet_time}]({tweet_url})\n\n{tweet_text}'

    if tweet_type == 'text':
        tg.send_message(
            channel_id,
            text,
            disable_web_page_preview=True,
            disable_notification=no_notify,
            parse_mode='MarkdownV2'
        )
    else:
        # check if pure media without text
        # in this case text is media url
        if tweet.text == get_media_entities_url(tweet):
            text = f'[里推 {tweet_time}]({tweet_url})'

        if tweet_type == 'photo':
            if len(get_tweet_photos(tweet)) > 1:
                tg.send_media_group(
                    channel_id,
                    prepare_album(tweet, caption=text, parse_mode='MarkdownV2'),
                    disable_notification=no_notify
                )
            else:
                tg.send_photo(
                    channel_id,
                    get_tweet_photos(tweet)[0],
                    caption=text,
                    disable_notification=no_notify,
                    parse_mode='MarkdownV2'
                )
        elif tweet_type == 'video':
            tg.send_video(
                channel_id,
                get_tweet_video(tweet),
                caption=text,
                disable_notification=no_notify,
                parse_mode='MarkdownV2'
            )
        else:  # gif
            tg.send_animation(
                channel_id,
                get_tweet_gif(tweet),
                caption=text,
                disable_notification=no_notify,
                parse_mode='MarkdownV2'
            )

    logging.info(f'Forwarded {tweet_type} tweet: {tweet.id}')
    return True


def sync_tweets(user_id, last_id):
    # forward tweet in reverse order
    for tweet in reversed(get_new_tweets(user_id, last_id)):
        if forward_tweet(tweet, no_notify=True):
            last_id = tweet.id
    return last_id


def main():
    if os.path.isfile(last_id_file):
        with open(last_id_file, 'r') as f:
            last_id = int(f.read())
        to_sync = True
    else:
        # initialize last_id
        last_id = get_latest_tweet_id(twitter_id)
        with open(last_id_file, 'w') as f:
            f.write(str(last_id))
        to_sync = False

    if to_sync:
        last_id = sync_tweets(twitter_id, last_id)
        with open(last_id_file, 'w') as f:
            f.write(str(last_id))

    return True


if __name__ == '__main__':
    main()
    sys.exit(0)

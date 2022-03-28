import os
import json
import base64
import tweepy
import logging
from time import time, sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from apscheduler.schedulers.blocking import BlockingScheduler


try:
    from checkList import user_list
except ImportError:
    user_list = []


def read_file(filename, encrypt=False):
    if encrypt:
        with open(filename, 'rb') as f:
            return base64.b64decode(f.read()).decode('utf-8')
    else:
        with open(filename, 'r') as f:
            return f.read()


def query_token(token_id):
    return read_file(f'token_{token_id}', True)


def notify(text, task='Space'):
    text = f'\[{task}] {text}'
    return os.system(f'/usr/local/bin/notify \"{text}\"')


twitter_token = json.loads(query_token('twitter'))
auth = tweepy.OAuthHandler(twitter_token['consumer_key'], twitter_token['consumer_secret'])
auth.set_access_token(twitter_token['access_token'], twitter_token['access_token_secret'])
kuma = tweepy.API(auth, wait_on_rate_limit=True)

chrome_profile_path = '/home/kuma/data/chrome'
chromedriver_path = '/snap/bin/chromium.chromedriver'

options = webdriver.ChromeOptions()
# options.add_argument('--headless')
options.add_argument('--headless=chrome')
options.add_argument(f'--user-data-dir={chrome_profile_path}')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')


def get_driver():
    return webdriver.Chrome(service=Service(chromedriver_path), options=options)


def load_tweet_complete(driver):
    return 'data-testid="tweet"' in driver.page_source


def get_src(url, timeout=30):
    t0 = time()
    try:
        logging.debug("{:.3f}s: Task: {}".format(time()-t0, url))
        driver = get_driver()
        logging.debug("{:.3f}s: Get: driver".format(time()-t0))
        driver.get(url)
        logging.debug("{:.3f}s: Getting: {}".format(time()-t0, url))
        WebDriverWait(driver, timeout).until(load_tweet_complete)
        source = driver.page_source
        driver.quit()
        logging.debug("{:.3f}s: Quit".format(time()-t0))
        return source
    except Exception as e:
        logging.error('{:.3f}s: Error: {}'.format(time()-t0, str(e)))
        return None


def check_space(user_id):
    logging.info(f'Checking: {user_id}')
    try:
        user = kuma.get_user(user_id=user_id)
        user_name = user.screen_name
        user_url = 'https://twitter.com/' + user_name

        source = get_src(user_url)
        if source:
            if 'active Space' in source:
                logging.warning(f'@{user_name} is in a Space!')
                notify(
                    f'[@{user_name}]({user_url}) is in a Space!',
                )
                return True
        return False
    except tweepy.errors.NotFound:
        logging.error('User not found: {}'.format(user_id))
        return None


def check_space_list():
    for user_id in user_list:
        check_space(user_id)


config = {
    'lazy': {
        'time': '1-8',
        'freq': '*/30',
    },
    'normal': {
        'time': '8-17',
        'freq': '*/15',
    },
    'busy': {
        'time': '17-23,0-1',
        'freq': '*/5',
    }
}


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.warning('Checking: ' + ', '.join([str(i) for i in user_list]))
    scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(check_space_list, 'cron', hour=config['lazy']['time'], minute=config['lazy']['freq'])
    scheduler.add_job(check_space_list, 'cron', hour=config['normal']['time'], minute=config['normal']['freq'])
    scheduler.add_job(check_space_list, 'cron', hour=config['busy']['time'], minute=config['busy']['freq'])
    scheduler.start()

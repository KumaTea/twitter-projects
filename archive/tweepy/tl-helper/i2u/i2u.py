import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

delay = 2
tweet_url = "https://twitter.com/i/status/{}"


def get_tweet_username(tweet_id):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    url = tweet_url.format(tweet_id)
    driver.get(url)
    time.sleep(delay)
    new_url = driver.current_url
    driver.quit()
    username = new_url.split("/")[3]
    if username == 'i':
        return False
    else:
        return username

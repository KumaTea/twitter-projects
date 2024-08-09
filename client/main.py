from typing import Union
from twitter.account import Account
from twitter.scraper import Scraper


class Twitter:
    def __init__(self, cookies: Union[str, dict]):
        self.account = Account(cookies=cookies)
        self.scraper = Scraper(cookies=cookies)

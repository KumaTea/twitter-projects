import logging
from client import Twitter
from apscheduler.schedulers.blocking import BlockingScheduler


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')

kuma = Twitter(cookies='cookies.json')

scheduler = BlockingScheduler()

from session import scheduler
from stats.followers import query_fo
from timeline.cleaner import clean_tl


def add_jobs():
    scheduler.add_job(query_fo, 'cron', hour='*', minute='*/15')
    scheduler.add_job(clean_tl, 'cron', hour='*', minute=36)


if __name__ == '__main__':
    add_jobs()
    scheduler.start()

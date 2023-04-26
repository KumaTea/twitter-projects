import os
from flask import Flask, request
from i2u import get_tweet_username


app = Flask(__name__)
# token = os.environ.get('TOKEN')


@app.route('/')
def wrapper():
    if request.method != "GET":
        return "Method not allowed", 405
    args = request.args
    if not args:
        return "No args provided", 400
    # if args.get('token') != token:
    #     return "Unauthorized", 401
    
    tweet_id = args.get('tweet_id')
    if not tweet_id:
        return "No tweet id provided", 400
    
    username = get_tweet_username(tweet_id)
    if not username:
        return "Tweet not found", 404
    else:
        return username, 200

if __name__ == '__main__':
    app.run()

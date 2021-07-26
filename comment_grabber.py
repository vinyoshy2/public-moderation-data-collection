import os
import json
import praw
from pymongo import MongoClient
import argparse
import time
import pika
import sys
import signal

#Load in data from config file
with open(sys.argv[1] + "config.json") as f:
    config = json.load(f)
APP_ID = config["APP_ID"]
APP_SECRET = config["APP_SECRET"]
APP_AGENT = config["APP_AGENT"]
DB_CHANNEL = config["DB_CHANNEL"]
AUTHOR_CHANNEL = config["AUTHOR_CHANNEL"]
subreddits = config["SUBREDDITS"]
USERNAME=config["APP_USER"]
PASSWORD=config["APP_PW"]

#establish connection to message queue
mq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', heartbeat=0))
mq_channel = mq_connection.channel()
mq_channel.queue_declare(queue=DB_CHANNEL, durable=True)
mq_channel.queue_declare(queue=AUTHOR_CHANNEL)

#establish connection to Reddit API
r = praw.Reddit(client_id = APP_ID, client_secret=APP_SECRET, user_agent=APP_AGENT,
        username=USERNAME, password=PASSWORD)

#Closes connection to message queue when kill signal is sent
def graceful_exit(x,y):
    print("EXITING")
    mq_connection.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_exit)

# Continously streams comments posted to target subreddits. Separate processes write comment data to
# database, and handle survey distribution/collection of author participation metrics 
# asynchronously
while True:
    for comment in r.subreddit("+".join(subreddits)).stream.comments(skip_existing=True):
        post = comment.submission
        author = comment.author
        subreddit = comment.subreddit.name
        is_op = comment.is_submitter
        db_data = {
                    "_id": comment.id,
                    "subreddit": subreddit,
                    "text": comment.body,
                    "title": post.title,
                    "post_body": post.selftext,
                    "post_id": post.id,
                    "time_delay": comment.created_utc - post.created_utc,
                    "time": comment.created_utc,
                    "is_reply": int(comment.parent_id[1] == "1"),
                    "is_op": is_op
                    }
        mq_channel.basic_publish(exchange='', routing_key=DB_CHANNEL, body=json.dumps(db_data),
        						 properties=pika.BasicProperties(delivery_mode=2))
        mq_channel.basic_publish(exchange='', routing_key=AUTHOR_CHANNEL, body=author.name + "," + subreddit + "," + comment.id)


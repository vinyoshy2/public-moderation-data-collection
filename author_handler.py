import os
import praw
from pymongo import MongoClient
import pika
import pickle
import hashlib
import json
import signal
import time
import sys

with open(sys.argv[1] + "message.txt", "r") as f:
    SUBJECT = f.readline()
    MESSAGE = f.read()
with open(sys.argv[1] + "config.json", "r") as f:
    config = json.load(f)

MONGO_HOST = "mongodb+srv://user1:"+ config["MONGO_PW"] +"@reddittest.abmkq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_HOST)
db = client[config["DB_NAME"]]
collection = db[config["COLLECTION_NAME"]]

APP_ID = config["APP_ID"]
APP_SECRET = config["APP_SECRET"]
APP_AGENT = config["APP_AGENT"]
USERNAME = config["APP_USER"]
PASSWORD = config["APP_PW"]
AUTHOR_CHANNEL = config["AUTHOR_CHANNEL"]
SEEN_FILE = "seen_set.json"
SAVE_FREQUENCY = 2

mq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
mq_channel = mq_connection.channel()
mq_channel.queue_declare(queue=AUTHOR_CHANNEL)
r = praw.Reddit(client_id=APP_ID, client_secret=APP_SECRET, user_agent=APP_AGENT, 
        username=USERNAME, password=PASSWORD)

hash_fct = hashlib.sha256
count = 0
if os.path.exists(SEEN_FILE):
    with open(sys.argv[1] + SEEN_FILE, "r") as f:
        seen_users = json.load(f)
else:
    seen_users = {}

def graceful_exit(x,y):
    with open(sys.argv[1] + SEEN_FILE, "w+") as f:
        f.write(json.dumps(seen_users, indent=4))

    mq_connection.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_exit)

# Note: To comply with IRB guidelines, we are avoiding saving username data to cloud. Will only be stored
# locally on our server, and then deleted once participation metrics have been computed.

# Method handles username data. If survey distribution is enabled, checks to 
# see if user has received survey link already, and then sends link if not.
# Otherwise, computes cryptographic hash of user name to be stored in database alongside comment.
# Locally stores user names and hash so we can later compute participation metrics for all commentors
def handle_auth(ch, method, properties, body):
    data = body.decode('utf-8').split(",")
    user = data[0]
    subreddit=data[1]
    comment_id = data[2]
    user_hash = hash_fct(user.encode('utf-8')).hexdigest()
    collection.update_one({'_id': comment_id}, {"$set": {"author": user_hash}}, upsert=True)
    if user_hash in seen_users:
        return False
    else:
        global count
        count+=1
        seen_users[user_hash] = {
                                 "time": time.time(),
                                 "author": user
                                }
        if count % SAVE_FREQUENCY == 0:
            with open(SEEN_FILE, "w+") as f:
                f.write(json.dumps(seen_users, indent=4))
    if config["DISTRIBUTE_SURVEY"]:
        print("distributing survey")
        sub = list(r.info([data[1]]))
        sub = sub[0].display_name
        new_subject = SUBJECT.replace("r/[INSERT_SUBREDDIT_HERE]", sub)
        new_message = MESSAGE.replace("r/[INSERT_SUBREDDIT_HERE]", sub)
        participant = r.redditor(user).message(SUBJECT, new_message)
    return True
    
mq_channel.basic_consume(queue=AUTHOR_CHANNEL, on_message_callback=handle_auth, auto_ack=True)
mq_channel.start_consuming()


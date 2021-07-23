import os
import json
import praw
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import argparse
import time
from bson.objectid import ObjectId
import time 
import sys

with open(sys.argv[1]+"config.json") as f:
    config = json.load(f)
MONGO_HOST = "mongodb+srv://user1:"+ config["MONGO_PW"] +"@reddittest.abmkq.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_HOST)
db = client[config["DB_NAME"]]
collection = db[config["COLLECTION_NAME"]]

app_id = config["APP_ID"]
app_secret = config["APP_SECRET"]
app_agent = config["APP_AGENT"]
subreddits = config["SUBREDDITS"]
username = config["APP_USER"]
password = config["APP_PW"]

update_length = 43200
diff_coef = 0.15
diff_base = 1.5
hidden_window = 60
actions = ["removecomment", "approvecomment", "spamcomment"]

r = praw.Reddit(client_id = app_id, client_secret=app_secret, user_agent=app_agent,
        username=username, password=password)
sub = r.subreddit("+".join(subreddits))

# Updates database entries with information about relevant actions
def update_removal(_id, new_val):
    try:
        collection.update_one({'_id': _id}, {"$push": {"removed": new_val}}, upsert=True)
    except (DuplicateKeyError):
        collection.update_one({'_id': _id}, {"$push": {"removed": new_val}})


#streams data from modlog. If an action of interested is taken against a comment, we store this information
for log in sub.mod.stream.log(skip_existing=True):
    if log.action in actions:
        _id = log.target_fullname[3:]
        update_removal(_id, log.action+","+str(log.created_utc)+","+log._mod+","+log.details)


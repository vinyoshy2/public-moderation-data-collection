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
import hashlib
import random

with open(sys.argv[1]+"config.json") as f:
    config = json.load(f)
    
if not os.path.exists(sys.argv[1] + "salt.txt"):
    characters = [chr(i) for i in range(128)]
    SALT = ''.join(random.SystemRandom().choice(characters) for _ in range(32))
    with open(sys.argv[1] + "salt.txt", "w+") as f:
        f.write(SALT)
else:
    with open(sys.argv[1]+"salt.txt", "r") as f:
        SALT = f.read()

hash_fct = hashlib.sha256
        
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

comment_actions = ["removecomment", "approvecomment", "spamcomment"]
user_actions = ["banuser", "unbanuser"]
post_actions = ["removelink", "approvelink", "spamlink"]
actions = comment_actions+user_actions+post_actions

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
    print(vars(log))
    if log.action in actions:
        mod_name = SALT + log._mod
        mod_hash = hash_fct(mod_name.encode('utf-8')).hexdigest()
        details = log.details
        if details is None:
            details = ''
        if log.action in user_actions:
            user = log.target_author
            user_hash = hash_fct(user.encode('utf-8')).hexdigest()
            identifier = user_hash
        elif log.action in post_actions:
            identifier = log.target_fullname
        else:
            identifier = log.target_fullname[3:]
        update_removal(identifier, log.action+","+str(log.created_utc)+","+mod_hash+","+details)


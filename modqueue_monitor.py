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
password= config["APP_PW"]



r = praw.Reddit(client_id=app_id, client_secret=app_secret, user_agent=app_agent,
        username=username, password=password)
sub = r.subreddit("+".join(subreddits))

seen = {}
# Updates database entries with information about new reports
def update_reports(_id, new_val):
    if _id in seen:
        if all([elem in seen[_id] for elem in new_val]):
            return False
    seen[_id] = new_val
    try:
        collection.update_one({'_id': _id}, {"$set": {"reports": new_val}}, upsert=True)
    except (DuplicateKeyError):
        collection.update_one({'_id': _id}, {"$set": {"reports": new_val}})

    return True

#Scans modqueue for new reports.
while True:
    for item in sub.mod.modqueue(only="comments"):
        update_reports(item.id, [report[0]+","+str(report[1]) for report in item.user_reports])
               

                
    

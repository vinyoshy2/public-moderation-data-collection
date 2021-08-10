import os
import json
import praw
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import argparse
import time
from bson.objectid import ObjectId
import time
import hashlib
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
try:
    with open(sys.argv[1] + "salt.txt") as f:
        SALT = f.read()
except:
    print("NO SALT FILE FOUND\nEXITING...")
    sys.exit(1)

hash_fct = hashlib.sha256   

r = praw.Reddit(client_id=app_id, client_secret=app_secret, user_agent=app_agent,
        username=username, password=password)
sub = r.subreddit("+".join(subreddits))

seen = {}
# Updates database entries with information about new reports
def update_reports(_id, new_val, user=True):
    cur_time = time.time()
    print(_id)
    print(new_val)
    if _id in seen:
        print("seen it")   
        if all([seen[_id].count(elem) == new_val.count(elem) for elem in new_val]):
            return False
    key = "reports"
    if not user:
        key = "mod_" + key
    existing = collection.find_one({"_id": _id})
    if "reports" in existing:
        i,j = 0,0
        to_update = []
        while i < len(new_val) and j < len(existing["reports"]):
            print(new_val[i])
            print(",".join(existing["reports"][j].split(","))[:-1])
            if new_val[i] == ",".join(existing["reports"][j].split(",")[:-1]):
                to_update.append(existing["reports"][j])
                i += 1
                j += 1
            else:
                to_update.append(new_val[i]+","+str(cur_time))
                i += 1
        while i < len(new_val):
            to_update.append(new_val[i]+","+str(cur_time))
            i += 1
    else:
        to_update = [val+","+str(cur_time) for val in new_val]
    print("Adding to db: ")
    print(to_update)
    try:
        collection.update_one({'_id': _id}, {"$set": {key: to_update}}, upsert=True)
    except (DuplicateKeyError):
        collection.update_one({'_id': _id}, {"$set": {key: to_update}})
    seen[_id] = new_val
    return True

#Scans modqueue for new reports.
while True:
    for item in sub.mod.modqueue(only="comments"):
        update_reports(item.id, sum([[report[0]]*report[1] if report[0] is not None and report[1] is not None
		    else ["None"] for report in item.user_reports], start=[]))
        update_reports(item.id, [report[0]+","+hash_fct((SALT+report[1]).encode('utf-8')).hexdigest() if report[0] is not None and report[1] is not None
		    else "None, "+hash_fct((SALT+report[1]).encode('utf-8')).hexdigest()  for report in item.mod_reports], user=False)
               

                
    

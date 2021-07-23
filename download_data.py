import os
from bson.json_util import dumps
from pymongo import MongoClient
import json

with open("config.json") as f:
    config = json.load(f)
MONGO_HOST = "mongodb+srv://user1:"+ config["MONGO_PW"] +"@reddittest.abmkq.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_HOST)
db = client[config["DB_NAME"]]
collection = db[config["COLLECTION_NAME"]]

cursor = collection.find({})
#downloads data from mongoDB
with open('removal_classifier/science_removed.json', 'w+') as f:
    f.write('{ \'data\': [\n')
    for document in cursor:
        f.write(dumps(document, indent=4))
        f.write(',')
        f.write('\n')
    f.write(']}')
        


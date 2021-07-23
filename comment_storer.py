import os
import json
import praw
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import argparse
import time
import pika
import signal
import sys

with open(sys.argv[1] + "config.json") as f:
    config = json.load(f)

MONGO_HOST = "mongodb+srv://user1:"+ config["MONGO_PW"] +"@reddittest.abmkq.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_HOST)
db = client[config["DB_NAME"]]
collection = db[config["COLLECTION_NAME"]]
DB_CHANNEL = config["DB_CHANNEL"]

mq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
mq_channel = mq_connection.channel()
mq_channel.queue_declare(queue=DB_CHANNEL, durable=True)

def graceful_exit(x, y):
    mq_connection.close()
    print("GRACEFULLY EXITING")
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_exit)

#writes data collected from message queue to database
def write_to_db(ch, method, properties, body):
    data = json.loads(body)
    _id = data["_id"]
    data.pop("_id")
    try:
        collection.update_one({'_id': _id, 'title': {"$exists": False}}, {"$set": data}, upsert=True)
    except (DuplicateKeyError):
        collection.update_one({'_id': _id, 'title': {"$exists": False}}, {"$set": data})


mq_channel.basic_consume(queue=DB_CHANNEL, on_message_callback=write_to_db, auto_ack=True)
mq_channel.start_consuming()


import json
import praw
import time
import sys

sys.path.append("../../utils")

from praw_wrapper import PrawWrapper
from prawcore.exceptions import Forbidden
from pymongo import MongoClient

WINDOW = 31*24*60*60
with open("../config.json") as f:
    config = json.load(f)
SUBREDDITS = config["SUBREDDITS"]

MONGO_HOST = "mongodb+srv://user1:"+ config["MONGO_PW"] +"@reddittest.abmkq.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_HOST)
db = client[config["DB_NAME"]]

collection = db[config["COLLECTION_NAME"]]
adj_var_collection = db[config["ADJ_VAR_COLLECTION_NAME"]]

# Wrapper for handling exceptions the API throws
def wrapper(comment_iter, auth_name):
    while True:
        try:
            yield(next(comment_iter))
        except StopIteration:
            break
        except Forbidden as e:
            print("something went wrong with user: " + auth_name)
            break

# Determines whether comment is too old for consideration
def too_old(comment, start_time, window):
    if (start_time - comment.created_utc) > window:
        return True
    return False

#Queries Reddit API for general participation metrics
def compute_gen_stats(r, author_name, subreddits, window):
    auth_obj = r.redditor(author_name)
    try:
        start_time = auth_obj.created_utc
    except:
        return {}
    comment_iter = wrapper(auth_obj.comments.new(limit=None), author_name)
    comment = next(comment_iter, None)
    cur_time = time.time()
    try:
        sub_ids = [r.subreddit(subreddit).id for subreddit in subreddits]
    except:
        return {}
    num_gen = 0
    num_gen_removed = 0
    while comment != None and not too_old(comment, cur_time, window):
        try:
            sub_flag = comment.subreddit_id[3:] in sub_ids
        except:
            continue
        if not sub_flag:
            removed_flag = r.comment(comment.id).body == "[removed]"
            num_gen += 1
            num_gen_removed += int(removed_flag)
        else:

        comment = next(comment_iter, None)
    stats =  {"com_gen": num_gen, 
            "rem_gen": num_gen_removed,
            "age": cur_time - start_time,
            "is_mod": auth_obj.is_mod()}
    return stats
# Looks at our database of stored comments to compute subreddit specific metrics
def compute_sub_stats(user_hash, subreddits, window):
    com_sub = {}
    rem_sub = {}
    for elem in subreddits:
        com_sub[elem] = 0
        rem_sub[elem] = 0
	for elem in collection.find({"author": user_hash}):
	    com_sub[elem["subreddit"]] += 1
	    if elem["removed"][-1] == "removecomment":
	        rem_sub[elem["subreddit"]] +=1
	final = {}
	for key, val in com_sub.items():
	    final["com_sub_" + key] = com_sub[key]
	for key, val in rem_sub.items():
	    final["rem_sub_" + key] = rem_sub[key]
	return final

# Collects participation metrics for each user who commented in one of the 
# target subreddits in the last month
def gen_auths_data(save, source, dest, subreddits, window):
    r = PrawWrapper().r
    with open(source) as src:
        data = json.load(src)
    with open(save, "r") as sv:
        participation_data = json.load(sv)
    count = 0
    for user_hash, entry in data.items():
        if count % 1000 == 0:
            with open(save, "w+") as sv:
                sv.write(json.dumps(auth_data))
        author_name = entry["author"]
        if author_name not in auth_data:
            gen_stats = compute_gen_stats(r, author_name, subreddits, window)
            sub_stats = compute_sub_stats(user_hash, subreddits, window)
            for subreddit in subreddits:
                gen_stats["com_gen"] += sub_stats["com_sub_"+subreddit]	
                gen_stats["rem_gen"] += sub_stats["rem_sub_"+subreddit]
            stats = {**gen_stats, **sub_stats}
            auth_data[user_hash] = stats
        count += 1
    with open(dest, "w+") as dst:
        dst.write(json.dumps(auth_data, indent=4))

gen_auths_data("auths_saved.json", "../seen_set.json", "participation_metrics.json", SUBREDDITS, WINDOW)

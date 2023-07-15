from bson import ObjectId
from pymongo import ReturnDocument

from db.db import get_database

db = get_database()
log_collection = db['request_logs']

def insert_log(process_id, request_id, start_time, end_time, image_ids, success, failure):
    doc = {
        "request_id": request_id,
        "process_id": process_id,
        "type": "bib",
        "start_time": start_time,
        "end_time": end_time,
        "image_ids": image_ids,
        "success": success,
        "failure": failure
    }

    result = log_collection.insert_one(doc)
    return result
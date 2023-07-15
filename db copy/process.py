from bson import ObjectId
from pymongo import ReturnDocument

from db.db import get_database

db = get_database()
process_collection = db['processes']


def update_bib_process(process_id, image_count):
    document_to_find = {
        "process_id": process_id,
    }

    update = {
        "$set": {
            "bib_detected": image_count
        }
    }

    result = process_collection.find_one_and_update(document_to_find, update,
                                                    return_document=ReturnDocument.AFTER)
    return result

import pickle
from datetime import datetime

import numpy as np
import pymongo
from pymongo import ReturnDocument

from db.db import get_database
from bson import json_util

db = get_database()
photo_collection = db['photos']


def parse_detect_item(detect_item):
    new_item = []

    for dict in detect_item:
        new_dict = {}
        for key, value in dict.items():
            if key == 'bound':
                if isinstance(value, np.ndarray):
                    new_dict[key] = value.tolist() if value is not None else None
                else:
                    new_dict[key] = value
            else:
                new_dict[key] = value
        new_item.append(new_dict)

    return new_item


def parse_detect(detect):
    if detect is None:
        return None

    bibs = parse_detect_item(detect.get('bibs'))
    texts = parse_detect_item(detect.get('texts'))
    faces = parse_detect_item(detect.get('faces'))
    objects = parse_detect_item(detect.get('objects'))
    people = parse_detect_item(detect.get('people'))

    return {
        'bibs': bibs,
        'texts': texts,
        'faces': faces,
        'objects': objects,
        'people': people,
    }


def insert_photo(event_id, file_info, detect=None):
    document_to_find = {'event_id': event_id, 'filename': file_info.get('filename')}

    photo_data = {
        'filename': file_info.get('filename'),
        'size': file_info.get('size'),
        'width': file_info.get('width'),
        'height': file_info.get('height'),
        'mime_type': file_info.get('mime_type'),
        'upload_url': file_info.get('upload_url'),
        'created_at': datetime.utcnow(),
        'event_id': event_id,
        'detect': parse_detect(detect)
    }
    update = {"$set": photo_data}

    result = photo_collection.find_one_and_update(document_to_find, update, upsert=True,
                                                  return_document=ReturnDocument.AFTER)
    return result


def update_photo_detect(photo_id, text, bib, obj, person, face):
    photo_to_update = {'_id': photo_id}
    update = {
        "$set": {
            "detect": {
                'text': text,
                'bib': bib,
                'object': obj,
                'person': person,
                'face': face,
            }
        }
    }

    result = photo_collection.find_one_and_update(photo_to_update, update, return_document=ReturnDocument.AFTER)
    return result


def update_photo_adjust_url(photo_id, adjust_url):
    photo_to_update = {'_id': photo_id}
    update = {
        "$set": {
            "adjust_url": adjust_url
        }
    }
    result = photo_collection.find_one_and_update(photo_to_update, update, return_document=ReturnDocument.AFTER)
    return result


def get_photos(event_id, search, offset, limit):
    rs = []
    photo_filter = {
        "filename": {"$regex": f".*{search}.*", "$options": 'i'},
        "event_id": event_id
    }

    projection = {
        "detect": 0
    }

    total = photo_collection.count_documents(photo_filter)
    photo_cursor = photo_collection.find(photo_filter, projection).skip(offset).limit(limit)
    for doc in photo_cursor:
        photo = parse_photo_from_mongo(doc)
        rs.append(photo)

    return {
        'total': total,
        'data': rs
    }


def parse_photo_from_mongo(photo):
    return {
        "id": str(photo.get('_id')),
        'event_id': photo.get('event_id'),
        "upload_url": photo.get('upload_url'),
        'size': photo.get('size'),
        'width': photo.get('width'),
        'height': photo.get('height'),
        'mime_type': photo.get('mime_type'),
        'created_at': photo.get('created_at').isoformat(),
        'detect': photo.get('detect'),
    }

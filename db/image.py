from __future__ import annotations

from typing import List, Optional

import numpy as np
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

from db.bib import insert_bibs
from db.db import get_database
from process.image_quality import detect_image_quality
from bson import ObjectId

db = get_database()
image_collection = db['photos']


class ImageEntity(BaseModel):
    id: Optional[str] = None
    event_id: Optional[str]
    url: Optional[str]
    width: Optional[int]
    height: Optional[int]
    user_id: Optional[str]
    name: Optional[str]
    size: Optional[int]
    mime_type: Optional[str]

    class Config:
        arbitrary_types_allowed = True


class RequestImage(BaseModel):
    id: str = Field(alias="_id", description="Mongodb id of image")
    event_id: Optional[str] = Field(alias="event_id", description="Event id.")
    url: str
    width: int
    height: int
    user_id: Optional[str] = Field(alias="userId")
    name: str


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


def update_image_detect(detect, event_id):
    image_id = detect.get('id')
    image_to_update = {'_id': ObjectId(image_id)}
    formatted_detect = parse_detect(detect)
    bibs = formatted_detect.get('bibs')

    map_bib_match = detect_image_quality(detect)

    def parse_bib_info(bib):
        return {
            'image_id': image_id,
            'bib_value': bib.get('value')
        }

    def parse_bib_image(bib):
        bib_value = bib.get('value')
        blur = None
        brightness = None

        image_quality = map_bib_match[bib_value]
        if image_quality is not None:
            blur = image_quality.blur
            brightness = image_quality.brightness

        return {
            'value': bib.get('value'),
            'confidence': bib.get('confidence'),
            'blur': blur,
            'brightness': brightness,
            'find_by_bib': True,
            'find_by_face': False
        }

    bib_infos = list(map(parse_bib_info, bibs))
    list_bibs = list(map(parse_bib_image, bibs))

    update = {
        "$set": {
            "detect": formatted_detect,
            "bibs": list_bibs
        },
    }

    result = image_collection.find_one_and_update(image_to_update, update, return_document=ReturnDocument.AFTER)

    # insert in bib table

    if len(bib_infos) > 0:
        insert_bibs(bib_infos, event_id)

    return result


def get_photos_by_ids(ids: [str]) -> List[ImageEntity]:
    rs = []
    object_ids = list(map(ObjectId, ids))
    photo_filter = {
        "_id": {"$in": object_ids},
    }

    projection = {
        "detect": 0
    }

    photo_cursor = image_collection.find(photo_filter, projection)

    for doc in photo_cursor:
        doc_id = doc.pop('_id', None)
        event_id = doc.pop('event_id', None)
        user_id = doc.pop('user_id', None)
        doc_dict = {'id': str(doc_id), 'event_id': str(event_id), 'user_id': str(user_id)}
        doc_dict.update(doc)
        rs.append(ImageEntity.parse_obj(doc_dict))

    return rs


def update_blur_brightness(image_id, blur, brightness):
    doc_filter = {'_id': ObjectId(image_id)}
    update = {
        '$set': {
            'blur': blur,
            'brightness': brightness
        }
    }
    image_collection.update_one(doc_filter, update)


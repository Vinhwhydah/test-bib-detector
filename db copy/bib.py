from bson import ObjectId
from pymongo import ReturnDocument, UpdateOne
from db.db import get_database

db = get_database()
bib_collection = db['bibs']
image_collection = db['images']


def insert_bib(bib_value, event_id, image_id):
    bib_to_find = {'value': bib_value, 'event_id': event_id}
    update = {"$addToSet": {
        'images': ObjectId(image_id)
    }}

    result = bib_collection.find_one_and_update(bib_to_find, update, upsert=True,
                                                  return_document=ReturnDocument.AFTER)

    # update image collection bib value

    image_to_find = {'_id': image_id}

    image_update = {"$addToSet": {
        'bibs': bib_value
    }}

    image_collection.find_one_and_update(image_to_find, image_update,
                                       return_document=ReturnDocument.AFTER)

    return result


def insert_bibs(bib_infos, event_id):
    writes = []
    for info in bib_infos:
        image_id = info.get('image_id')
        bib_value = info.get('bib_value')

        bib_to_find = {'value': bib_value, 'event_id': ObjectId(event_id)}
        update = {"$addToSet": {
            'images': ObjectId(image_id)
        }}
        writes.append(UpdateOne(bib_to_find, update, upsert=True))

        # bib_collection.update_one(bib_to_find, update, upsert=True,
        #                                               return_document=ReturnDocument.AFTER)

    bib_collection.bulk_write(writes)

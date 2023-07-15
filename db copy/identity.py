from bson import ObjectId
from db.db import get_database
from datetime import datetime

db = get_database()
identity_collection = db['identities']


def insert_identities(detect_matches):
    created_at = datetime.now()

    if len(detect_matches) > 0:
        list_identities = []

        for detect_match in detect_matches:
            event_id = detect_match.get('event_id')
            image_id = detect_match.get('image_id')
            image_url = detect_match.get('image_url')

            for match in detect_match.get('matches'):
                bib = match.bib
                find_by_bib = True if bib is not None else False

                if bib is None:
                    continue

                list_identities.append({
                    'created_at': created_at,
                    'updated_at': created_at,
                    'bib': bib,
                    'face': match.face,
                    'blur': match.blur,
                    'person': match.person,
                    'brightness': match.brightness,
                    'find_by_bib': find_by_bib,
                    'find_by_face': False,
                    'image_id': ObjectId(image_id),
                    'event_id': ObjectId(event_id),
                    'image_url': image_url,
                })

        if len(list_identities) > 0:
            identity_collection.insert_many(list_identities)

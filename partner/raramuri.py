import asyncio
import re

from db.image import ImageEntity
from dotenv import load_dotenv
import requests
from db.partner import find_partner_by
from db.event import find_event_by_id

from urllib.parse import urlparse

load_dotenv()


def notify_new_image(images: list[ImageEntity], detect_results) -> bool:
    is_success = True

    # create map detect with id
    try:
        map_detected_gb_id = {}

        for index, detect in enumerate(detect_results):
            map_detected_gb_id[detect.get('id')] = detect

        map_bib_images_detected = {}

        for _, image in enumerate(images):
            image_detected_data = map_detected_gb_id[image.id]
            if not image_detected_data or image_detected_data is None:
                continue

            bib_detected_ids = image_detected_data.get('bibs')

            for _, bib in enumerate(bib_detected_ids):
                bib_value = bib.get('value')
                event_id = image.event_id
                key = event_id+"-"+bib_value

                bib_image_detected = map_bib_images_detected.get(key)

                if not bib_image_detected or bib_image_detected is None:
                    bib_image_detected = {
                        'bib': bib_value,
                        'event_id': image.event_id,
                        'image_urls': [image.url]
                    }

                    map_bib_images_detected[key] = bib_image_detected
                else:
                    bib_image_detected['image_urls'].append(image.url)
                    map_bib_images_detected[key] = bib_image_detected

        call_api(map_bib_images_detected)

    except Exception as e:
        print(
            f"Error when call notify to partner error: {str(e)}")

        is_success = False

    finally:
        return is_success


def call_api(map_bib_images_detected):
    map_event = {}
    map_event_not_support = {}
    map_partner_detected = {}
    map_partner = {}

    for key in map_bib_images_detected:
        bib_detected = map_bib_images_detected[key]
        event_id = bib_detected.get('event_id')

        if map_event_not_support.get(event_id) is not None:
            continue
        elif map_event.get(event_id) is None:
            event = find_event_by_id(event_id)

            if event is not None and event.partner_event_id is not None and event.created_by is not None:
                partner = find_partner_by(event.created_by)

                if partner is not None:
                    map_partner_detected[partner.ping_notify_url] = [bib_detected]
                    map_partner[partner.ping_notify_url] = partner
                    map_event[event_id] = event
                else:
                    map_event_not_support[event_id] = event

            else:
                map_event_not_support[event_id] = event
        else:
            map_partner_detected[partner.ping_notify_url].append(bib_detected)

    for url in map_partner_detected:
        bib_images_detected = map_partner_detected[url]
        partner = map_partner[url]

        # populate header authentication
        headers = {
            'content-type': 'application/json',
            'Authorization': partner.secret_key,
            'clientID': partner.name,
        }

        # sending post request and saving response as response object
        requests.post(url=partner.ping_notify_url, json={'data': bib_images_detected}, headers=headers)

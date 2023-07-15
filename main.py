import base64
import traceback
from datetime import datetime
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db.identity import insert_identities
from db.image import update_image_detect, get_photos_by_ids
from db.log import insert_log
from db.process import update_bib_process
from process.image_quality import detect_image_quality_batch
from detect.bib import detect_batch_image_uris
from partner.raramuri import notify_new_image
from asyncio import sleep as async_sleep
from starlette.concurrency import run_in_threadpool
from typing import List
from threading import Thread

is_stress_test = os.environ.get('IS_STRESS_TEST')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.post('/{event_id}/handleSubscription', tags=["BIB Detect"])
# async def bib_detects(file: UploadFile, event_id: str):
#     file_info = await handle_upload_file(file, event_id)
#     photo = insert_photo(file_info, event_id)
#     return JSONResponse(content={'data': parse_photo_from_mongo(photo)})


@app.post('/handleSubscription', tags=["BIB Detect"])
async def receive_messages_handler(request: Request):
    message = await request.json()
    start_time = datetime.now()
    err = None

    # data here is a string of array ids, which split by , character
    data = message.get('message').get('data')
    decoded_payload = base64.b64decode(data)
    message_string = decoded_payload.decode('utf-8')

    splits = message_string.split(',')
    ids = splits[1:]

    key = splits[0]
    process_id = key.split('|')[0]
    request_id = key.split('|')[1]

    print(
        f"handle process id: {process_id} - request id : {request_id} - images ids: {ids} - start_time: {start_time.isoformat()}")

    try:
        if not is_stress_test or is_stress_test == 'false':
            err = await run_in_threadpool(process_detect_images, ids, process_id)
        else:
            await async_sleep(len(ids))

    finally:
        end_time = datetime.now()
        success_count = 0
        err_message = "process error"

        if err is None:
            success_count = len(ids)
            err_message = "process success"

        if process_id is not None and request_id is not None:
            insert_log(
                process_id=process_id,
                request_id=request_id,
                start_time=start_time,
                end_time=end_time,
                image_ids=ids,
                success=0,
                failure=len(ids) - success_count
            )

        print(
            f"Handle {err_message} take : {(end_time - start_time).total_seconds()} seconds, id: {process_id} - "
            f"request id : {request_id} - images ids: {ids} - start_time: {start_time.isoformat()} - end_time: "
            f"{end_time.isoformat()} - error: {str(err)}")

    if err is None:
        return 'OK', 200
    else:
        return 'INTERNAL_ERROR', 500


class TryRequest(BaseModel):
    ids: List[str]


@app.post('/try', tags=["BIB Detect"])
async def bib_detects(request: TryRequest):
    images = get_photos_by_ids(request.ids)
    detect_results = await detect_batch_image_uris(images)

    detect_matches = []
    rs = []

    for detect in detect_results:
        event_id = detect.get('event_id')
        img = update_image_detect(detect, event_id)
        image_id = detect.get('id')

        created_at = img.get('created_at')
        updated_at = img.get('updated_at')
        img.update({
            '_id': str(image_id),
            'created_at': created_at.isoformat() if created_at is not None else None,
            'updated_at': updated_at.isoformat() if updated_at is not None else None,
            'event_id': str(detect.get('event_id')),
            'user_id': str(detect.get('user_id'))
        })
        img.pop('detect', None)
        rs.append(img)

        matches = detect.get('matches')
        image_url = detect.get('image_url')
        detect_matches.append(
            {
                "matches": matches,
                "image_id": image_id,
                "event_id": event_id,
                "image_url": image_url,
            },
        )

    insert_identities(detect_matches)

    return JSONResponse(content={'data': rs})


# @app.post('/push-handlers/receive_messages', tags=["BIB Detect"])
# async def receive_messages_handler(request: Request):
#     # TODO handle the JWT token
#     message = await request.json()
#     attributes = message.get('message').get('attributes')
#     object_id = attributes.get('objectId')
#     event_type = attributes.get('eventType')
#     credentials = Credentials.from_service_account_file('./gcs_credential.json')
#     storage_client = storage.Client(credentials=credentials)
#     bucket = storage_client.bucket(bucket_name)
#
#     # TODO find with regular expression for more accuracy
#     if object_id.find('/') > -1:
#         match event_type:
#             case 'OBJECT_FINALIZE':
#                 # if is_valid_image(filename):
#                 folder, filename = object_id.rsplit('/', 1)
#
#                 if is_valid_image(filename):
#                     blob = bucket.get_blob(object_id)
#                     if blob is None:
#                         return {'status': 'error', 'message': 'Object not found'}
#
#                     url = blob.public_url
#                     image_bytes = io.BytesIO(blob.download_as_bytes())
#                     image = Image.open(image_bytes)
#                     size = blob.size
#                     width, height = image.size
#                     mime_type = blob.content_type
#
#                     # detect_result = detect_batch_image_uri(url)
#
#                     print(f"New image added: {filename}, width: {width}, height: {height}, size: {size}, url {url} mime type {mime_type}")
#
#                 else :
#                     print(f"not handle object_id {object_id}")
#
#             case 'OBJECT_DELETE':
#                 print("delete case, not handle")
#             case _:
#                 print(f"Not handle the event type ${event_type}")
#
#
#     # Returning any 2xx status indicates successful receipt of the message.
#     return 'OK', 200

# def is_valid_image(filename):
#     # Split the file name and extension
#     basename, extension = os.path.splitext(filename)
#     # Check if the extension is valid
#     return extension.lower() in ('.jpg', '.jpeg', '.png')

def process_detect_images(ids, process_id):
    try:
        images = get_photos_by_ids(ids)
        detected_images = detect_batch_image_uris(images)
        detect_matches = []

        for detect in detected_images:
            event_id = detect.get('event_id')
            update_image_detect(detect, event_id)

            image_id = detect.get('id')

            # detect blur and brightness here
            # faces_detect = detect.get('faces')

            matches = detect.get('matches')
            image_url = detect.get('image_url')
            detect_matches.append(
                {
                    "matches": matches,
                    "image_id": image_id,
                    "event_id": event_id,
                    "image_url": image_url,
                },
            )

        # detect blur
        detect_image_quality_batch(detect_matches, process_id)

        # loop and adjust image if needed
        insert_identities(detect_matches)

        # update process and log
        update_bib_process(process_id, len(ids))

        notify_new_image(images, detected_images)

        return None

    except Exception as e:
        print(traceback.format_exc())

        return e

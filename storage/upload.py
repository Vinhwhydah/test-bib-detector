import os
from storage.delete import delete_file_from_server
from storage.gcs import upload_file_gcs
from datetime import datetime
from PIL import Image

from google.cloud import storage
from google.oauth2.service_account import Credentials


async def handle_upload_file(file, event_id):
    temp_upload_folder = 'temp-uploads'
    filename = file.filename
    mime_type = file.content_type

    file_path = f"{temp_upload_folder}/{filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    with Image.open(file_path) as img:
        width, height = img.size

    size = os.path.getsize(file_path)
    upload_url = upload_file_gcs(file_path, event_id, filename)

    delete_file_from_server(file_path)

    return {
        'size': size,
        'width': width,
        'height': height,
        'mime_type': mime_type,
        'upload_url': upload_url,
        'filename': filename,
        'event_id': event_id
    }


async def handle_upload_files(files, event_id: str):
    temp_upload_folder = 'temp-uploads'
    files_info = []

    if not os.path.exists(temp_upload_folder):
        os.mkdir(temp_upload_folder)

    for file in files:
        file_info = await handle_upload_file(file, event_id)
        files_info.append(file_info)

    return files_info

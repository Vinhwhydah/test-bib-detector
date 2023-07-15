from google.cloud import storage
from google.oauth2.service_account import Credentials
import time

credentials = Credentials.from_service_account_file('./bib_detector_credential.json')
storage_client = storage.Client(credentials=credentials)


def upload_file_gcs(source_file_name, folder_name, destination_blob_name, bucket_name='iml.whydah.xyz'):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"{folder_name}/{destination_blob_name}")

    max_retries = 3

    # Upload the file with retry logic.
    for i in range(max_retries):
        try:
            print("start upload")
            blob.upload_from_filename(source_file_name)
            return blob.public_url
        except Exception as e:
            print(f"Upload failed on attempt {i + 1}: {e}")
            if i < max_retries - 1:
                print(f"Retrying upload file gcs in 5 seconds...")
                time.sleep(5)

    print("last try upload")
    blob.upload_from_filename(source_file_name)
    return blob.public_url


def upload_blob_from_memory(contents, folder_name, destination_blob_name, content_type='image/jpeg', bucket_name='iml.whydah.xyz'):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"{folder_name}/{destination_blob_name}")

    blob.upload_from_string(contents, content_type)

    return blob.public_url

import pprint

from google.cloud import storage
from google.oauth2.service_account import Credentials


BUCKET = 'iml.whydah.xyz'
TOPIC = 'bib-detect'

def create_bucket_notifications(bucket_name = BUCKET, topic_name = TOPIC):
    credentials = Credentials.from_service_account_file('./bib_detector_credential.json')
    print(f"credentials {credentials}")
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)

    notification = bucket.notification(topic_name=topic_name)
    notification.create()

    print(f"Successfully created notification with ID {notification.notification_id} for bucket {bucket_name}")


def print_pubsub_bucket_notification(bucket_name = BUCKET, notification_id = ''):
    credentials = Credentials.from_service_account_file('./bib_detector_credential.json')
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)

    notification = bucket.get_notification(notification_id)
    # pprint.pprint(notification)
    print(f"Notification ID: {notification.notification_id}")
    print(f"Topic Name: {notification.topic_name}")
    print(f"Event Types: {notification.event_types}")
    print(f"Custom Attributes: {notification.custom_attributes}")
    print(f"Payload Format: {notification.payload_format}")
    print(f"Blob Name Prefix: {notification.blob_name_prefix}")
    print(f"Etag: {notification.etag}")
    print(f"Self Link: {notification.self_link}")


def delete_bucket_notification(bucket_name = BUCKET, notification_id = ''):
    credentials = Credentials.from_service_account_file('./bib_detector_credential.json')
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    notification = bucket.notification(notification_id=notification_id)
    notification.delete()

    print(f"Successfully deleted notification with ID {notification_id} for bucket {bucket_name}")


def list_bucket_notifications(bucket_name = BUCKET):
    credentials = Credentials.from_service_account_file('./bib_detector_credential.json')
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    notifications = bucket.list_notifications()

    for notification in notifications:
        print(f"Notification ID: {notification.notification_id}")
        print(f"Topic Name: {notification.topic_name}")
        print(f"Event Types: {notification.event_types}")
        print(f"Custom Attributes: {notification.custom_attributes}")
        print(f"Payload Format: {notification.payload_format}")
        print(f"Blob Name Prefix: {notification.blob_name_prefix}")
        print(f"Etag: {notification.etag}")
        print(f"Self Link: {notification.self_link}")

# from google.oauth2 import service_account
import re

from bson import ObjectId
from google.cloud import vision
from google.cloud import vision_v1
import time
from google.oauth2 import service_account

from db.image import ImageEntity
from detect.face import handle_face_annotation
from detect.object_localization import handle_object_localozation_annotation
from detect.text import handle_full_text_annotation
from matcher.matcher import match

creds = service_account.Credentials.from_service_account_file('./bib_detector_credential.json')
client = vision.ImageAnnotatorClient(credentials=creds)


def handle_annotations(full_text_annotation,face_annotations, object_localization_annotations,image_uri, width, height):
    bibs, texts = handle_full_text_annotation(full_text_annotation, width=width, height=height)
    faces = handle_face_annotation(face_annotations, image_uri=image_uri, width=width, height=height)
    objects, people = handle_object_localozation_annotation(object_localization_annotations)
    matches = match(people, faces, bibs)

    return {
        'bibs': bibs,
        'texts': texts,
        'faces': faces,
        'objects': objects,
        'people': people,
        'matches': matches
    }


def detect_batch_image_uri(image_uri, width, height):
    features = [
        {"type_": vision_v1.Feature.Type.DOCUMENT_TEXT_DETECTION},
        {"type_": vision_v1.Feature.Type.FACE_DETECTION},
        {"type_": vision_v1.Feature.Type.OBJECT_LOCALIZATION},
    ]

    image = {"source": {"image_uri": image_uri}}
    request = {"image": image, "features": features}

    response = client.annotate_image(request)

    face_annotations = response.face_annotations
    full_text_annotation = response.full_text_annotation
    object_localization_annotations = response.localized_object_annotations

    detect_result = handle_annotations(
        full_text_annotation=full_text_annotation,
        face_annotations=face_annotations,
        object_localization_annotations=object_localization_annotations,
        image_uri=image_uri.replace('storage.cloud.google', 'storage.googleapis'),
        width=width,
        height=height
    )

    return detect_result


def detect_batch_image_uris(images: list[ImageEntity]):
    start_time = time.time()

    features = [
        {"type_": vision_v1.Feature.Type.DOCUMENT_TEXT_DETECTION},
        {"type_": vision_v1.Feature.Type.FACE_DETECTION},
        {"type_": vision_v1.Feature.Type.OBJECT_LOCALIZATION},
    ]

    requests = []

    for image_info in images:
        url = image_info.url.replace('storage.cloud.google', 'storage.googleapis')
        image = {"source": {"image_uri": url}}
        annotate_image_request = vision_v1.types.AnnotateImageRequest(
            image=image,
            features=features,
        )
        requests.append(annotate_image_request)

    batch_request = vision_v1.types.BatchAnnotateImagesRequest(requests=requests)

    response = client.batch_annotate_images(batch_request)
    end_time = time.time()
    print(f"Time taken to detect gg vision: {len(images)} images takes {end_time - start_time} seconds")

    detect_results = []
    start_time = time.time()
    for index, res in enumerate(response.responses):
        image_info = images[index]
        uri = image_info.url.replace('storage.cloud.google', 'storage.googleapis')
        width = image_info.width
        height = image_info.height
        image_id = image_info.id
        event_id = image_info.event_id

        full_text_annotation = res.full_text_annotation
        face_annotations = res.face_annotations
        object_localization_annotations = res.localized_object_annotations

        detect = handle_annotations(
            full_text_annotation=full_text_annotation,
            face_annotations=face_annotations,
            object_localization_annotations=object_localization_annotations,
            image_uri=uri,
            width=width,
            height=height
        )

        detect.update({'id': image_id, 'event_id': ObjectId(event_id), 'image_url': uri})

        detect_results.append(detect)

    end_time = time.time()
    print(f"Time taken to handle annotation and face encoding for: {len(images)} images takes {end_time - start_time} seconds")

    return detect_results


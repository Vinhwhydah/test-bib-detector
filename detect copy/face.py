from urllib.request import urlopen
import ssl
import urllib.parse

# import urllib
import face_recognition

import cv2
import numpy as np

from detect import model
from matcher.utils import normalized_bound, boundingpoly2rect
from utils.bounding import normalized_bounding_box_vertices

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE


def handle_face_annotation(face_annotation, image_uri, width, height):
    faces = []
    parsed_uri = urllib.parse.quote(image_uri, safe=':/')
    # http = urllib.PoolManager()
    url_response = urlopen(parsed_uri, context=context)
    image = cv2.imdecode(np.array(bytearray(url_response.read()), dtype=np.uint8), -1)
    # Names of likelihood from google.cloud.vision.enums

    for face in face_annotation:
        face_bound = normalized_bounding_box_vertices(face.bounding_poly, width, height)
        face_location = boundingpoly2rect(np.multiply(face_bound, image.shape[:2][::-1]))
        face_encoding = face_recognition.face_encodings(image, [face_location])[0]

        faces.append({
            'bound': face_bound,
            'confidence': face.detection_confidence,
            'encoding': face_encoding,
        })

    return faces

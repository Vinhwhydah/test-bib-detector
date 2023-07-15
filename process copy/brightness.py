import ssl
from urllib.parse import quote, urlparse
from urllib.request import urlopen

import numpy
import numpy as np
import os
import cv2
from dotenv import load_dotenv

from storage.gcs import upload_file_gcs
from utils.image import download_image_from_url

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
load_dotenv()
bucket = os.environ.get('BUCKET_NAME')


def get_brightness_hsv(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    brightness = hsv[:, :, 2].mean()
    return brightness


def get_brightness_grayscale(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = gray.mean()
    return brightness


def get_brightness(image_path):
    image = cv2.imread(image_path)
    grayscale = get_brightness_grayscale(image)
    hsv = get_brightness_hsv(image)
    return {
        'hsv': hsv,
        'grayscale': grayscale
    }


def get_brightness_url(url):
    encoded_url = quote(url, safe=':/')
    response = urlopen(encoded_url, context=context)
    image_array = bytearray(response.read())
    image = cv2.imdecode(np.asarray(image_array), cv2.IMREAD_COLOR)
    grayscale = get_brightness_grayscale(image)
    hsv = get_brightness_hsv(image)
    return {
        'hsv': hsv,
        'grayscale': grayscale
    }


def get_faces_brightness(filename, faces_count, face_folder_path):
    hsv_rs = []
    grayscale_rs = []

    for index in range(faces_count):
        face_file = f"{filename.replace('.JPG', '').replace('.jpg', '')}_{index}.jpg"
        face_file_path = os.path.join(face_folder_path, face_file)
        brightness_result = get_brightness(face_file_path)

        hsv = brightness_result.get('hsv')
        grayscale = brightness_result.get('grayscale')

        hsv_rs.append(hsv)
        grayscale_rs.append(grayscale)

    return {
        'hsv': hsv_rs,
        'grayscale': grayscale_rs
    }


def adjust_brightness_image(upload_url, name):
    img = download_image_from_url(upload_url)
    temp_adjust_images_folder = 'adjust_images'

    if not os.path.exists(temp_adjust_images_folder):
        os.makedirs(temp_adjust_images_folder)

    min_brightness = 0.7
    cols, rows, _ = img.shape
    brightness = numpy.sum(img) / (255 * cols * rows)
    ratio = brightness / min_brightness

    if ratio < 1:
        temp_name = "adjust_" + name

        adjusted_img = cv2.convertScaleAbs(img, alpha=1 / ratio, beta=1)
        output_path = os.path.join(temp_adjust_images_folder, temp_name)
        cv2.imwrite(output_path, adjusted_img)

        parsed_url = urlparse(upload_url)
        user_id = parsed_url.path.rsplit('/', 2)[1]
        folder_path = 'content/images/' + user_id

        upload_url = upload_file_gcs(source_file_name=output_path, folder_name=folder_path,
                                     destination_blob_name=temp_name,
                                     bucket_name=bucket)
        os.remove(output_path)
        return upload_url
    else:
        return None

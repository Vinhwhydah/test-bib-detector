import os
import shutil
import cv2
import requests
import numpy as np

from db.image import ImageEntity, update_blur_brightness
from process.image_quality import get_laplacian_from_url, get_faces_laplacian
from process.brightness import get_brightness_url, get_faces_brightness


# receive the detect from face detection
# and get other image info: name, width, height, url
# then do these step:
# loop each image and , and split faces
# loop each image again, get blur(laplacian), brightness for each image and base on name, get blur(laplacian) and brightness for each faces
# store all into db


async def process_image(images: list[ImageEntity], detect_results):
    faces_folder = 'temp_faces_split'
    for index, image in enumerate(images):
        # face_detect = detect_results[index].get('faces')
        # split_faces(image, face_detect, faces_folder)
        # faces_count = len(face_detect)
        # id = image.id
        url = image.url
        name = image.name

        image_blur_var = get_laplacian_from_url(url)
        image_brightness = get_brightness_url(url)
        # faces_variance = get_faces_laplacian(name, faces_count, faces_folder)

        blur = {
            'value': image_blur_var,
            # 'faces': faces_variance
        }

        # faces_brightness = get_faces_brightness(name, faces_count, faces_folder)

        brightness = {
            'hsv': image_brightness.get('hsv'),
            'grayscale': image_brightness.get('grayscale'),
            # 'faces_hsv': faces_brightness.get('hsv'),
            # 'faces_grayscale': faces_brightness.get('grayscale'),
        }

        update_blur_brightness(id, blur, brightness)

        print("name", name)
        print("blur", blur)
        print("brightness", brightness)
    # shutil.rmtree(faces_folder)



def split_faces(image: ImageEntity, face_detect, faces_folder = 'temp_faces_split'):
    url = image.url
    width = image.width
    height = image.height
    faces = face_detect
    name = image.name

    response = requests.get(url)
    image = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
    output_dir = faces_folder

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i, face in enumerate(faces):
        box = face.get('bound')
        x1_norm, y1_norm = box[0][0], box[0][1]
        x2_norm, y2_norm = box[2][0], box[2][1]
        left = int(x1_norm * width)
        top = int(y1_norm * height)
        right = int(x2_norm * width)
        bottom = int(y2_norm * height)
        face_image = image[top:bottom, left:right]
        format_name = name.replace('.JPG', '').replace('.jpg', '').replace('.png', '')
        filename = f"{output_dir}/{format_name}_{i}.jpg"
        cv2.imwrite(filename, face_image)

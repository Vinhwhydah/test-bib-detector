from urllib.request import urlopen
from urllib.parse import urlparse
import ssl
import urllib.parse
import cv2
import numpy as np


class RegionBox(object):
    def __init__(self, x1, y1, x2, y2, x3, y3, x4, y4):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3
        self.x4 = x4
        self.y4 = y4

    def __str__(self):
        attributes = vars(self)
        attributes_str = ", ".join(
            [f"{key}={value}" for key, value in attributes.items()]
        )
        return f"RegionBox: {attributes_str}"


def download_image_from_url(url):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    parsed_uri = urllib.parse.quote(url, safe=":/")
    # http = urllib.PoolManager()
    url_response = urlopen(parsed_uri, context=context)
    image = cv2.imdecode(np.array(bytearray(url_response.read()), dtype=np.uint8), -1)
    return image


def get_face_image(image, face):
    if face is None:
        return

    segment = parse_region(face.get("bound"))
    x1 = min(segment.x1, segment.x2, segment.x3, segment.x4)
    y1 = min(segment.y1, segment.y2, segment.y3, segment.y4)
    x2 = max(segment.x1, segment.x2, segment.x3, segment.x4)
    y2 = max(segment.y1, segment.y2, segment.y3, segment.y4)

    # Crop image
    height, width, _ = image.shape
    left_pixel = int(min(x1, x2) * width)
    upper_pixel = int(min(y1, y2) * height)
    right_pixel = int(max(x1, x2) * width)
    lower_pixel = int(max(y1, y2) * height)

    return image[upper_pixel:lower_pixel, left_pixel:right_pixel]


def parse_region(bound):
    x1, y1 = bound[0][0], bound[0][1]
    x2, y2 = bound[1][0], bound[1][1]
    x3, y3 = bound[2][0], bound[2][1]
    x4, y4 = bound[3][0], bound[3][1]
    segment = RegionBox(x1, y1, x2, y2, x3, y3, x4, y4)
    return segment


def get_image_name_info(image_url, bib):
    parts = urlparse(image_url).path.rsplit("/", 1)
    image_name = "adjust_brightness_" + bib + "_" + parts[1]
    path = parts[0].split("/", 2)[2]

    return path, image_name

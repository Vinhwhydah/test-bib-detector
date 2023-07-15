import copy
import ssl
from urllib.parse import quote
from urllib.request import urlopen
from utils.image import get_face_image, download_image_from_url, get_image_name_info
from storage.gcs import upload_blob_from_memory

from datetime import datetime
import numpy as np
import os
import cv2

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

blur_threshold = int(os.environ.get('BLUR_THRESHOLD'))
brightness_low_threshold = int(os.environ.get('BRIGHTNESS_THRESHOLD_LOW'))
brightness_high_threshold = int(os.environ.get('BRIGHTNESS_THRESHOLD_HIGH'))
bucket = os.environ.get('BUCKET_NAME')


def get_laplacian_variance(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def get_laplacian_from(image_path):
    image = cv2.imread(image_path)
    variance = get_laplacian_variance(image)
    return variance


def get_laplacian_from_url(url):
    encoded_url = quote(url, safe=':/')
    response = urlopen(encoded_url, context=context)
    image_array = bytearray(response.read())

    # Decode the image array using OpenCV
    image = cv2.imdecode(np.asarray(image_array), cv2.IMREAD_COLOR)
    variance = get_laplacian_variance(image)
    return variance


def get_faces_laplacian(filename, faces_count, face_folder_path='mtb_faces'):
    rs = []

    for index in range(faces_count):
        face_file = f"{filename.replace('.JPG', '').replace('.jpg', '')}_{index}.jpg"
        face_file_path = os.path.join(face_folder_path, face_file)
        var = get_laplacian_from(face_file_path)
        rs.append(var)

    return rs


def detect_image_quality_batch(detect_matches, process_id):
    start_time = datetime.now()
    face_count = 0

    for detect_match in detect_matches:
        image_url = detect_match.get('image_url')
        image = download_image_from_url(image_url)

        for match in detect_match.get('matches'):
            if match.face is None or match.bib is None:
                continue

            face_count += 1

            processed_img = pre_process_image(image, match.face)
            match.blur = get_blur_score(processed_img)
            match.brightness = get_brightness_score(processed_img, image, image_url, match.bib.get('value'))

    print(
        f"Time taken to detect blur - process_id:{process_id} - {face_count} face to detect {(datetime.now() - start_time).total_seconds()} seconds")


def detect_image_quality(detect):
    image_url = detect.get('image_url')
    image = download_image_from_url(image_url)
    map_detect = {}

    for match in detect.get('matches'):
        if match.bib is None:
            continue

        map_detect[match.bib.get('value')] = match
        if match.face is None or match.bib is None:
            continue

        processed_img = pre_process_image(image, match.face)
        match.blur = get_blur_score(processed_img)
        match.brightness = get_brightness_score(processed_img, image, image_url, match.bib.get('value'))

    return map_detect


def pre_process_image(image, face):
    face_image = get_face_image(image, face)
    img_150 = cv2.resize(face_image, (150, 150), cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img_150, cv2.COLOR_BGR2GRAY)

    return gray


def get_blur_score(face_image):
    score = cv2.Laplacian(face_image, cv2.CV_64F).var()
    is_blur = bool(score <= blur_threshold)

    return {'score': score, 'is_blur': is_blur}


def get_brightness_score(face_image, image, image_url, bib):
    score = np.mean(face_image)
    status = 'normal'
    adjusted_image_url = None

    if score > brightness_high_threshold:
        status = 'high'
        adjusted_image_url = adjust_image_quality(score, image, image_url, bib)
    elif score < brightness_low_threshold:
        status = 'low'
        adjusted_image_url = adjust_image_quality(score, image, image_url, bib)

    return {'score': score, 'status': status, 'processed_url': adjusted_image_url}



def brightness_adjustment(image, gamma):
    """Adjust image brightness based on calibrated gamme factor

    Args:
        image (_type_): image as cv2 matrix
        gamma (_type_): gamma brightness factor

    Returns:
        _type_: brightness adjusted cv2 matrix
    """
    gamma_corrected = np.power(image / 255.0, gamma)
    adjusted_image = (gamma_corrected * 255).astype(np.uint8)

    return adjusted_image


"""
TEST saturation_factor:
    1.5 => too vibrant
    1.2 => Best result
"""
def saturation_adjustment(image, saturation_factor=1.2):
    """Adjust saturation of image using specified saturation factor

    Args:
        image (_type_): iamge cv2 matrix form
        saturation_factor (_type_): saturation factor

    Returns:
        _type_: saturation adjusted cv2 matrix
    """
    # Convert the image to the HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Split the HSV image into individual channels
    h, s, v = cv2.split(hsv_image)

    # Adjust the saturation channel by scaling it with the saturation factor
    s = np.clip(s * saturation_factor, 0, 255).astype(np.uint8)

    # Merge the modified channels back into the HSV image
    hsv_modified = cv2.merge([h, s, v])

    # Convert the modified HSV image back to the BGR color space
    modified_image = cv2.cvtColor(hsv_modified, cv2.COLOR_HSV2BGR)

    return modified_image


"""
TESTED CONFIG
cliplimit | tileGridSize | alpha
2.0       | (4,4)        | 1.2 => BEST RESULT
2.0       | (2,2)        | 1.2 => no significant different
2.0       | (2,2)        | 1.8 => extremly flare
2.0       | (2,2)        | 0.9 => extremly deglow
2.0       | (2,2)        | 1.15 => minimal different
"""
def flare_adjustment(image, alpha=1.15, clip_limit=1.5, tile_grid_size=(4, 4)):
    """Adjust image flare with specified alpha value

    Args:
        image (_type_): image cv2 matrix form
        alpha (float, optional): flare correction value. Defaults to 1.15.
        clip_limit (float, optional): clip limit for CLAHE object. Defaults to 1.5.
        tile_grid_size (tuple, optional): tile grid size for CLAHE object. Defaults to (4, 4).

    Returns:
        _type_: adjusted flare cv2 matrix
    """
    # create a CLAHE object (Arguments are optional).
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl1 = clahe.apply(gray_image)
    enhanced_image = cv2.cvtColor(cl1.astype(np.uint8), cv2.COLOR_GRAY2BGR)

    # Blend the enhanced image with the original image
    alpha = alpha  # Adjust the blending factor as desired
    blended_image = cv2.addWeighted(image, alpha, enhanced_image, 1 - alpha, 0)
    return blended_image


"""
TEST VALUE CONFIG: 0.9 -> 0.98 yield good result
"""
def contrast_adjustment(image, alpha=0.95):
    """Adjust contrast with given alpha

    Args:
        image (_type_): image cv2 matrix form
        alpha (_type_): contrast value. Note:  low contrast < 1.0 < high contrast

    Returns:
        _type_: Adjusted contrast cv2 matrix
    """
    adjusted_image = cv2.convertScaleAbs(image, alpha=alpha, beta=0)
    return adjusted_image


"""
TESTED CONFIG
amount | radius
1.1    | 1.5
1.1    | 1.2  => decent
"""
def sharpen_adjustment(image, amount=1.1, radius=1.2):
    """Adjust sharpeness of image

    Args:
        image (_type_): image cv2 matrix form
        amount (float, optional): intensity of sharpening. Defaults to 1.1.
        radius (float, optional): radius of detail to be sharpened. Defaults to 1.2.

    Returns:
        _type_: adjusted sharpen cv2 matrix
    """
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=radius, sigmaY=radius)
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
    return sharpened


def image_enhancement(
    image,
    brightness_gamma,
    contrast_alpha=0.95,
    sharpen_amount=1.1,
    sharpen_radius=1.2,
    flare_alpha=1.15,
    saturation_factor=1.2,
):
    """An assembly chain of image enhancement techniques

    Args:
        image (_type_): image cv2 matrix form
        brightness_gamma (_type_): brightness gamma value
        contrast_alpha (float, optional): contrast alpha value. Defaults to 0.95.
        sharpen_amount (float, optional): sharpen intensity value. Defaults to 1.1.
        sharpen_radius (float, optional): sharpen radius value. Defaults to 1.2.
        flare_alpha (float, optional): flare alpha value. Defaults to 1.15.
        saturation_factor (float, optional): saturation factor. Defaults to 1.2.

    Returns:
        _type_: quality enhanced image cv2 form
    """
    try:
        brightness_ạdjusted_image = brightness_adjustment(image, gamma=brightness_gamma)
        contrast_adjusted_image = contrast_adjustment(
            brightness_ạdjusted_image, alpha=contrast_alpha
        )
        sharpen_adjusted_image = sharpen_adjustment(
            contrast_adjusted_image, amount=sharpen_amount, radius=sharpen_radius
        )
        saturation_adjusted_image = saturation_adjustment(
            sharpen_adjusted_image, saturation_factor=saturation_factor
        )
        final_result = flare_adjustment(saturation_adjusted_image, alpha=flare_alpha)
        return final_result
    
    except Exception as e:
        raise(e)


def adjust_image_quality(bright_score, image, image_url, bib):
    gamma = gamma_mapping(bright_score)
    image_copy = copy.deepcopy(image)
    
    # Pass through image enhancement channel
    adjusted_image = image_enhancement(image_copy, brightness_gamma = gamma)
    
    # Convert the image to bytes
    image_bytes = cv2.imencode('.jpg', adjusted_image)[1].tobytes()

    path, name = get_image_name_info(image_url, bib)

    adjusted_image_url = upload_blob_from_memory(image_bytes, path, name, bucket_name=bucket)

    return adjusted_image_url


def gamma_mapping(score, in_min=0, in_max=255, out_min=0, out_max=2, desired_gamma: float = 1.1):
    adjust_delta = 0
    # Normalize the value within the input range
    normalized_value = (score - in_min) / (in_max - in_min)

    # Map the normalized value to the output range
    gamma = (normalized_value * (out_max - out_min)) + out_min

    # Get current off value
    adjust_delta = desired_gamma * (desired_gamma - gamma) / desired_gamma

    if gamma > desired_gamma:
        return round(1 - adjust_delta, 2)

    return round(adjust_delta, 2)

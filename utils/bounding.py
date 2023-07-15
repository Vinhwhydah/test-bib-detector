import numpy as np


def normalized_bounding_box_vertices(bounding_box, width, height):
    return np.array(list(map(lambda v: [v.x / width, v.y / height], bounding_box.vertices)))
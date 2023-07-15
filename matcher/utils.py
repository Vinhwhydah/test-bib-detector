import numpy as np


def normalized_bound(bound, img_height, img_width):
    return np.array([(v['x'] / img_width, v['y'] / img_height) if type(v['x']) is int
                     else (v['x'], v['y']) for v in bound])


def computeIoU(bound1, bound2):
    x_left = max(bound1[0, 0], bound2[0, 0])
    x_right = min(bound1[2, 0], bound2[2, 0])
    y_top = max(bound1[0, 1], bound2[0, 1])
    y_bottom = min(bound1[2, 1], bound2[2, 1])

    if x_right <= x_left or y_bottom <= y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    area1 = np.prod(bound1[2] - bound1[0])
    area2 = np.prod(bound2[2] - bound2[0])

    iou = intersection_area / float(area1 + area2 - intersection_area)
    
    return iou

def remove_duplicate(objects, threshold=0.8):
    res = []
    for i in range(len(objects)):
        ok = True
        for j in range(i):
            if computeIoU(objects[i]['bound'], objects[j]['bound']) > threshold:
                ok = False
                break
        if ok:
            res.append(objects[i])

    return res


def boundingpoly2rect(bound):
    top = np.min(bound[:, 1])
    bottom = np.max(bound[:, 1])
    left = np.min(bound[:, 0])
    right = np.max(bound[:, 0])
    return list(map(int, (top, right, bottom, left)))

import numpy as np


def handle_object_localozation_annotation(object_locallization_annotation):
    objects = []
    people = []

    for object_ in object_locallization_annotation:
        data = {
            'value': object_.name,
            'confidence': object_.score,
            'bound': np.array(list(map(lambda v: [v.x, v.y], object_.bounding_poly.normalized_vertices)))
        }
        objects.append(data)

        if object_.name == 'Person':
            people.append(data)

    return objects, people


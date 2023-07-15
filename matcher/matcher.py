import face_recognition
import numpy as np

from matcher.utils import remove_duplicate, normalized_bound, boundingpoly2rect

INF = 1e9


class Runner:
    def __init__(self, bib, person, face, blur=None, brightness=None):
        self.bib = bib
        self.person = person
        self.face = face
        self.blur = blur
        self.brightness = brightness

        if self.bib is not None:
            self.bib['bound'] = self.bib['bound'].tolist()

        if self.person is not None:
            self.person['bound'] = self.person['bound'].tolist()

        if self.face is not None:
            self.face['bound'] = self.face['bound'].tolist()
            self.face['encoding'] = self.face['encoding'].tolist()


def compute_position_and_width(target_bound, person_bound):
    center = np.mean(target_bound[[0, 2]], axis=0)
    position = (center - person_bound[0]) 
    width = (target_bound[2, 0] - target_bound[0, 0])
    if np.min(position) - width / 6 < 0 or np.max(position) + width / 6 > 1:
        return None, None
    return position / (person_bound[2] - person_bound[0]), width / (person_bound[2, 0] - person_bound[0, 0])


def matching_distance(position, width, estimated_position, estimated_width, weight_position=2, weight_width=5):
    return weight_position * np.linalg.norm(position - estimated_position) \
           + weight_width * abs(width - estimated_width)


def find_best_match(persons, candidates, used, estimated_position, estimated_width):
    positions = [list(map(lambda candidate, u: (None, None) if u
    else compute_position_and_width(candidate['bound'], person['bound']),
                          candidates, used)) for person in persons]

    matching_distances = [list(map(lambda x: INF if x[0] is None
    else matching_distance(x[0], x[1], estimated_position, estimated_width),
                                   ps)) for ps in positions]

    indices = [(i, j) for i in range(len(persons)) for j in range(len(candidates))]
    indices.sort(key=lambda e: matching_distances[e[0]][e[1]])

    res = [None] * len(persons)

    for i, j in indices:
        if matching_distances[i][j] > 2:
            break
        if res[i] is not None or used[j]:
            continue
        res[i] = j
        used[j] = True

    return res


def match(persons, faces, bibs):
    persons = remove_duplicate(persons)

    res = []

    face_used = [False] * len(faces)
    bib_used = [False] * len(bibs)
    match_face_indices = find_best_match(persons,
                                         faces,
                                         face_used,
                                         np.array([0.5, 0.1]),
                                         0.4)
    match_bib_indices = find_best_match(persons,
                                        bibs,
                                        bib_used,
                                        np.array([0.5, 0.6]),
                                        0.25)
    for person_bound, face_idx, bib_idx in zip(persons, match_face_indices, match_bib_indices):
        p = Runner(None if bib_idx is None else bibs[bib_idx],
                   person_bound,
                   None if face_idx is None else faces[face_idx],
                   )
        res.append(p)

    for i in range(len(faces)):
        if face_used[i]:
            continue
        bib_idx = None
        for j in range(len(bibs)):
            if bib_used[j]:
                continue
            if abs(np.mean(faces[i]['bound'][:, 0]) - np.mean(bibs[j]['bound'][:, 0])) \
                    < faces[i]['bound'][2, 0] - faces[i]['bound'][0, 0] \
                    and faces[i]['bound'][2, 1] < bibs[j]['bound'][0, 1]:
                if bib_idx is None or bibs[j]['bound'][0, 1] < bibs[bib_idx]['bound'][0, 1]:
                    bib_idx = j
        if bib_idx is not None:
            bib_used[bib_idx] = True

        p = Runner(None if bib_idx is None else bibs[bib_idx],
                   None,
                   faces[i]
                   )
        res.append(p)

    for i in range(len(bibs)):
        if bib_used[i]:
            continue
        p = Runner(bibs[i],
                   None,
                   None,
                   )
        res.append(p)

    return res


def preprocess(db_persons, db_faces, db_bibs, image):
    height, width, _ = image.shape

    persons = []
    for person_bound, person in zip(db_persons['bounds'], db_persons['points']):
        persons.append({
            'bound': normalized_bound(person_bound, height, width),
            'confidence': person['score'],
        })

    faces = []
    for face_bound, confidence in zip(db_faces['bounds'], db_faces['confidence']):
        face_bound = normalized_bound(face_bound, height, width)
        face_location = boundingpoly2rect(np.multiply(face_bound, image.shape[:2][::-1]))
        face_encoding = face_recognition.face_encodings(image, [face_location])[0]

        faces.append({
            'bound': face_bound,
            'confidence': confidence,
            'encoding': face_encoding,
        })

    bibs = []
    for bib_bound, bib_point in zip(db_bibs['bounds'], db_bibs['points']):
        bibs.append({
            'bound': normalized_bound(bib_bound, height, width),
            'value': bib_point['value'],
            'confidence': bib_point['score'],
            'match_type': bib_point['match_type'],
        })

    return persons, faces, bibs

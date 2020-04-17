import detection
import ipautils as ipa
import cv2 as cv


def nothing(*args):
    pass


def get_master(pieces):
    if len(pieces) == 1:
        return pieces[0]

    sorted_x = sorted(pieces, key=lambda x: x.corners[0, 0])

    candidate_index = 0
    new_candidate = 0
    while candidate_index < len(pieces):

        candidate_pos = sorted_x[candidate_index].corners[0]
        for i in xrange(candidate_index + 1, len(pieces)):
            next_pos = sorted_x[i].corners[0]

            if candidate_pos[1] > next_pos[1]:
                y_dist = abs(candidate_pos[1] - next_pos[1])
                x_dist = abs(candidate_pos[0] - next_pos[0])

                if x_dist > y_dist:
                    continue

                new_candidate = i
                break

        if new_candidate == candidate_index:
            return sorted_x[candidate_index]
        else:
            candidate_index = new_candidate

    return pieces[candidate_index]


cv.namedWindow("Out")
cv.createTrackbar('Layer', 'Out', 0, 100, nothing)
cv.createTrackbar('Layer 2', 'Out', 0, 100, nothing)

while True:
    d_min = cv.getTrackbarPos('Layer', 'Out')
    d_max = cv.getTrackbarPos('Layer 2', 'Out')
    p = detection.get_pieces(-1, d_min, d_max)
    if len(p) == 2:
        master = get_master(p)
        m_index = p.index(master)

        if m_index != 0:
            p[0], p[m_index] = p[m_index], p[0]

        print ipa.distance(p[0].corners[1], p[1].corners[0])


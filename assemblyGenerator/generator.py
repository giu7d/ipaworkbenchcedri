import ipautils as ipa
import json


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


def get_relation(master, piece):
    min_dist = 400
    master_ref = -1
    piece_ref = -1

    for i in xrange(0, 4):
        for j in xrange(0, 4):
            dist = ipa.distance(master.corners[i], piece.corners[j])
            if dist < min_dist:
                min_dist = dist
                master_ref = i
                piece_ref = j

    if (master_ref == -1) or (piece_ref == -1):
        print ">> FATAL ERROR <<"

    x_distance = piece.corners[piece_ref, 1] - master.corners[master_ref, 1]
    y_distance = piece.corners[piece_ref, 0] - master.corners[master_ref, 0]
    domination = x_distance - y_distance

    if domination < 2:
        movement = -1
    else:
        movement = 0 if domination > 0 else 1

    return min_dist, master_ref, piece_ref, movement


def generate(pieces, layer, last_master):
    if len(pieces) == 0:
        return

    result = {"layer": layer, "assembly": {}}

    master = pieces[0]

    if len(pieces) > 1:
        master = get_master(pieces)
        m_index = pieces.index(master)
        if m_index != 0:
            pieces[0], pieces[m_index] = pieces[m_index], pieces[0]

    # Create master
    result["assembly"]["0"] = {}
    result["assembly"]["0"]["master"] = True
    result["assembly"]["0"]["color"] = pieces[0].color
    result["assembly"]["0"]["orientation"] = pieces[0].orientation

    if layer != 0:
        distance, master_ref, piece_ref, movement = get_relation(last_master, master)
        result["assembly"]["0"]["distance"] = distance
        result["assembly"]["0"]["master_ref"] = master_ref
        result["assembly"]["0"]["piece_ref"] = piece_ref
        result["assembly"]["0"]["movement"] = movement

    for i in xrange(1, len(pieces)):
        si = str(i)
        piece = pieces[i]
        result["assembly"][si] = {}

        result["assembly"][si]["master"] = False
        result["assembly"][si]["color"] = piece.color
        result["assembly"][si]["orientation"] = piece.orientation

        distance, master_ref, piece_ref, movement = get_relation(master, piece)

        result["assembly"][si]["distance"] = distance
        result["assembly"][si]["master_ref"] = master_ref
        result["assembly"][si]["piece_ref"] = piece_ref
        result["assembly"][si]["movement"] = movement

    return master, result


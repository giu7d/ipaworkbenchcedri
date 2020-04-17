import ipautils as ipa

currentlayer = 0

delta_distance = 2


def process_assembly(pieces, assembly):

    # If the number os pieces detected is greater than expected, exit with error
    if len(pieces) != len(assembly):
        return None
        # throw exception too many pieces

    # Create the response array
    response = []

    # Loop through all the instructions and check if its detected
    for key in assembly:
        ins = assembly[key]
        # If the instruction is master, skip
        if ins["master"]:
            continue

        # Create the possible matches array
        matches = []

        # Store the master
        master = None

        # Get the references and distance from the instruction
        color_ref = ins["color"]
        orientation_ref = ins["orientation"]
        master_ref = ins["master_ref"]
        piece_ref = ins["piece_ref"]
        distance = ins["distance"]

        for (i, p) in enumerate(pieces):

            # If piece is master, store then jump to next piece
            if i == 0:
                master = p
                continue

            # If the piece has already matched with a instruction, jump to next piece
            if p.matched:
                continue

            # If the color of the current piece is different than the expected, jump to next piece
            if p.color != color_ref:
                continue

            # If the orientation of the current piece is different than the expected, jump to next piece
            if p.orientation != orientation_ref:
                continue

            # Calculate the distance between references
            distance_betweeen = ipa.distance(p.corners[piece_ref], master.corners[master_ref])

            # If the distance between is equal as the expected, append on the matches array
            if (distance - delta_distance) <= distance_betweeen <= (distance + delta_distance):
                matches.append(p)
            else:
                print "Distance Expected: " + str(distance) + " with delta: " + str(delta_distance)
                print "Found: " + str(distance_betweeen)

        # If no matches are found for this instruction, append false on the response array and continue
        # to next instruction
        if len(matches) == 0:
            response.append(False)
            continue

        # Else then there is a match, append true on response array
        response.append(True)

        # If has found a match with no ambiguiation, mark as matched and continue to next instruction
        if len(matches) == 1:
            matches[0].matched = True
            print "Matched >> " + str(distance_betweeen)
            continue

        # If it does not match any of the previous conditions then there are more than one piece as match
        # Proceed to disambiguiation

        # Method 1 - Check instruction for movement on x or y
        domination_array = []

        for p in matches:
            x_distance = p.corners[piece_ref, 1] - master.corners[master_ref, 1]
            y_distance = p.corners[piece_ref, 0] - master.corners[master_ref, 0]
            domination = x_distance - y_distance
            domination_array.append(domination)

        if ins[6] == 0:
            # Greater X
            match_index = domination_array.index(max(domination_array))
        else:
            # Greater Y
            match_index = domination_array.index(min(domination_array))

        match = matches[match_index]

        match.matched = True

    return response


def check_master(master, assembly):
    m_as = assembly["0"]

    if master.color != m_as["color"]:
        return False

    if master.orientation != m_as["orientation"]:
        return False

    return True


def check_new_layer(master, last_master, assembly):
    ins = assembly["0"]

    color_ref = ins["color"]
    orientation_ref = ins["orientation"]
    master_ref = ins["master_ref"]
    piece_ref = ins["piece_ref"]
    distance = ins["distance"]

    if master.color != color_ref:
        return False

    if master.orientation != orientation_ref:
        return False

    distance_betweeen = ipa.distance(master.corners[piece_ref], last_master.corners[master_ref])
    print "Distance between layer masters: " + str(distance_betweeen)
    if not (distance - delta_distance) <= distance_betweeen <= (distance + delta_distance):
        print "Distance Expected: " + str(distance) + " with delta: " + str(delta_distance)
        print "Found: " + str(distance_betweeen)
        return False

    movement_ref = ins["movement"]

    if movement_ref == -1:
        return True

    x_distance = master.corners[piece_ref, 1] - last_master.corners[master_ref, 1]
    y_distance = master.corners[piece_ref, 0] - last_master.corners[master_ref, 0]
    domination = x_distance - y_distance

    if domination > 0:
        return movement_ref == 0
    else:
        return movement_ref == 1



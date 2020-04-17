import detection
import json
import assemblyparser as ap
import requests as rq
from collections import deque

last_master = None
OFFLINE_MODE = False


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


get_url = "http://localhost/visualrecognition/public/api/getSequence"
send_url = "http://localhost/visualrecognition/public/api/sendSequenceValidation"


last_response = -1


def send_validation(seq_id, step, all_correct):
    global last_response

    if last_response == all_correct:
        return

    last_response = all_correct

    validation = str(seq_id)
    step = int(step)
    for x in xrange(0, step):
        if x == step - 1:
            validation += ",1" if all_correct else ",0"
        else:
            validation += ",1"

    print "Validation string: " + validation
    params = {"validation": validation}
    response = -1

    if OFFLINE_MODE:
        return

    while response != 200:
        data = rq.post(send_url, params)
        response = data.status_code


def reset():
    global last_master, current_layer
    last_master = None
    current_layer = 0


current_scenario = -1
current_step = -1
current_layer = 0
json_history = []


def get_data():
    global current_scenario, current_step, json_history
    print "Getting data from server..."
    response = -1
    data = ""
    while response != 200:
        data = rq.get(get_url)
        response = data.status_code
        print "Server response " + str(response)

    data = data.content.split(",", 2)

    if data[0] != current_scenario:
        reset()

    assembly = data[2]

    if assembly is None:
        assembly = get_data()

    json_data = json.loads(assembly)
    current_scenario = data[0]

    if current_step != data[1]:
        json_history.append(json_data)

    current_step = data[1]

    return json_data


responses = deque([])


def rescan_previous():
    global last_master
    print "Rescanning previous assembly..."
    while True:
        pieces = detection.get_pieces(current_layer - 1)
        if len(pieces) > 0:
            master = get_master(pieces)
            data = json_history[len(json_history) - 2]
            if not ap.check_master(master, data["assembly"]):
                continue

            if (current_step == 0) and (len(pieces) == 1):
                print "All correct, resuming..."
                break

            m_index = pieces.index(master)

            if m_index != 0:
                pieces[0], pieces[m_index] = pieces[m_index], pieces[0]

            response = ap.process_assembly(pieces, data["assembly"])

            if response is not None:
                if all(t for t in response):
                    print "All correct, resuming..."
                    last_master = master
                    break


def main():
    global current_layer, last_master, current_scenario, current_step, last_response, responses
    verify_new_layer = False
    while True:
        # Get instructions from server
        last_response = -1
        data = get_data()
        responses.clear()
        # Check for layer change
        try:
            new_layer = data["layer"]
        except TypeError:
            continue

        if new_layer != current_layer:
            verify_new_layer = True
            detection.attach_callback(rescan_previous)
            current_layer = new_layer

        while True:
            pieces = detection.get_pieces(current_layer)

            if len(responses) > 5:
                responses.popleft()

            if len(pieces) > 0:
                master = get_master(pieces)

                if verify_new_layer:
                    is_ok = ap.check_new_layer(master, last_master, data["assembly"])
                    responses.append(is_ok)

                    if len(responses) < 5:
                        continue

                    if all(t for t in responses):
                        verify_new_layer = False
                        detection.detach_callback()
                        send_validation(current_scenario, current_step, True)
                        last_master = master
                        break
                else:
                    if not ap.check_master(master, data["assembly"]):
                        send_validation(current_scenario, current_step, False)
                        responses.append(False)
                        continue

                    if(current_step == 0) and (len(pieces) == 1):
                        # send_validation(current_scenario, current_step, True)
                        responses.append(True)
                        # break
                    else:
                        m_index = pieces.index(master)

                        if m_index != 0:
                            pieces[0], pieces[m_index] = pieces[m_index], pieces[0]

                        response = ap.process_assembly(pieces, data["assembly"])

                        if response is not None:
                            if all(t for t in response):
                                responses.append(True)
                                # send_validation(current_scenario, current_step, True)
                                # last_master = master
                            else:
                                # send_validation(current_scenario, current_step, False)
                                responses.append(False)

                    # Check
                    if len(responses) < 5:
                        continue

                    if all(t for t in responses):
                        send_validation(current_scenario, current_step, True)
                        last_master = master
                        break
                    else:
                        send_validation(current_scenario, current_step, False)


if __name__ == "__main__":
    main()

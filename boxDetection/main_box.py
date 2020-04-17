import requests as rq
import json
import box_detection as detect


def all_same(items):
    return all(t == items[0] for t in items)


def routine():
    url_getsc = "http://localhost/visualrecognition/public/api/sendScenario"
    url_valid = "http://localhost/visualrecognition/public/api/sendScenarioValidation"
    url_update = "http://localhost/visualrecognition/public/api/updateScenario"

    tool = detect.Detection()

    last_detection = []

    while True:
        data = rq.post(url_getsc)
        while data.status_code != 200:
            data = rq.post(url_getsc)

        response = json.loads(data.content)
        sequence = response["order"]
        seq_id = response["id"]

        while True:
            detections = []
            for x in xrange(0, 20):
                colors = tool.detect_box()
                if colors is not None:
                    detections.append(colors)
                else:
                    detections.append(["A", "A", "A", "A"])

            ok_count = 0
            if all_same(detections):
                if detections[0] == ["A", "A", "A", "A"]:
                    print "Blocked, not sending..."
                    continue

                if detections == last_detection:
                    print "Same, not sending..."
                    continue

                last_detection = detections
                resp = str(seq_id) + ","
                for x in xrange(0, 4):
                    if detections[0][x] == sequence[x]:
                        resp += "1"
                        ok_count += 1
                    else:
                        resp += "0"

                    if x != 3:
                        resp += ","
                print resp
                response = {'validation': resp}

                data = rq.post(url_valid, response)
                while data.status_code != 200:
                    data = rq.post(url_valid, response)

                if ok_count == 4:
                    print "All correct..."
                    break

        while True:
            detections = []
            for x in xrange(0, 20):
                colors = tool.detect_box()
                if colors is not None:
                    detections.append(colors)
                else:
                    detections.append(["A", "A", "A", "A"])

            if all_same(detections):
                if detections[0] == ["X", "X", "X", "X"]:
                    print "Nova Caixa..."
                    break

        data = rq.post(url_update)
        while data.status_code != 200:
            data = rq.post(url_update)

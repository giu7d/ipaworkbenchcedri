import detection as dt
import cv2 as cv
import generator as gt
import json
import mysql.connector

json_strgs = []


def run_generator():
    current_layer = 0
    current_file = 0
    last_master = None
    while True:
        print "Getting pieces..."
        print "Current layer: " + str(current_layer)
        img, pieces = dt.get_pieces(current_layer)
        print "Confirm pieces with (K), (N) to try detection again or (C) to abort"
        key = cv.waitKey()

        if key == ord("k"):
            last_master, dct = gt.generate(pieces, current_layer, last_master)

            with open("Generated/assembly" + str(current_file) + ".json", "w") as file_w:
                json.dump(dct, file_w)

            cv.imwrite("Generated/assembly" + str(current_file) + ".jpg", img)

            json_strgs.append(json.dumps(dct))
            print "File saved, for a new layer press (L), for same layer press (N), to finalize press (X)"
            current_file += 1

            key = cv.waitKey()

            if key == ord("l"):
                current_layer += 1

            if key == ord("x"):
                return True

            continue

        if key == ord("c"):
            return False


def push_data():
    print "Pushing data to database..."
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="visualrecognition"
    )

    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT sequence FROM sequences ORDER BY id DESC")
    last_seq = cursor.fetchone()

    new_seq = last_seq[0] + 1
    img_prefix = "storage/Scenarios/s" + str(new_seq) + "/"
    sql_str = "INSERT INTO sequences (sequence, step, image, assembly) VALUES (%s, %s, %s, %s)"
    img_suffix = str(new_seq) + "_final.jpg"
    val = (new_seq, 0, img_prefix + img_suffix, "null")

    cursor.execute(sql_str, val)
    db.commit()

    for x in xrange(0, len(json_strgs)):
        img_suffix = "assembly" + str(x) + ".jpg"
        val = (new_seq, x + 1, img_prefix + img_suffix, json_strgs[x])
        cursor.execute(sql_str, val)
        db.commit()

    print "Data pushed to database!"


def main():
    result = run_generator()

    if result:
        push_data()


if __name__ == "__main__":
    main()

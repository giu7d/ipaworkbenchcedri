import pyrealsense2 as rs
import cv2 as cv
import numpy as np
import piece
import ipautils as ipa
from collections import deque

DS5_product_ids = ["0AD1", "0AD2", "0AD3", "0AD4", "0AD5", "0AF6", "0AFE", "0AFF", "0B00", "0B01", "0B03", "0B07",
                   "0B3A"]


def find_device_that_supports_advanced_mode():
    ctx = rs.context()
    devices = ctx.query_devices()
    for dev in devices:
        if dev.supports(rs.camera_info.product_id) and str(dev.get_info(rs.camera_info.product_id)) in DS5_product_ids:
            if dev.supports(rs.camera_info.name):
                print("Found device that supports advanced mode:", dev.get_info(rs.camera_info.name))
            return dev
    raise Exception("No device that supports advanced mode was found")


try:
    dev = find_device_that_supports_advanced_mode()
    advnc_mode = rs.rs400_advanced_mode(dev)
    print("Advanced mode is", "enabled" if advnc_mode.is_enabled() else "disabled")

    with open("hsat2.json") as fd:
        as_json_object = fd.read()

    # We can also load controls from a json string
    # For Python 2, the values in 'as_json_object' dict need to be converted from unicode object to utf-8
    # The C++ JSON parser requires double-quotes for the json object so we need
    # to replace the single quote of the pythonic json to double-quotes
    json_string = str(as_json_object).replace("'", '\"')
    advnc_mode.load_json(json_string)

except Exception as e:
    print(e)
    pass


kernal = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))

lower_red_1 = np.array([0, 146, 20])
upper_red_1 = np.array([7, 255, 255])

lower_red_2 = np.array([163, 146, 20])
upper_red_2 = np.array([189, 255, 255])

lower_blue = np.array([100, 100, 20])
upper_blue = np.array([125, 255, 255])

lower_green = np.array([50, 100, 20])
upper_green = np.array([77, 255, 255])

pipe = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
prof = pipe.start(config)

align_to = rs.stream.depth
align = rs.align(align_to)

colors = [(0, 0, 255), (255, 0, 0), (0, 255, 0)]

spatial = rs.spatial_filter(0.5, 20.0, 2.0, 0.0)
hole_filling = rs.hole_filling_filter()
temporal = rs.temporal_filter(0.4, 20.0, 3)
decimation = rs.decimation_filter(2.0)

for x in xrange(0, 60):
    pipe.wait_for_frames()

frames = deque([])

height_map = None

for x in xrange(0, 11):
    frameset_h = pipe.wait_for_frames()
    frameset_h = align.process(frameset_h)

    depth_frame_h = frameset_h.get_depth_frame()
    depth_frame_h = spatial.process(depth_frame_h)
    depth_frame_h = hole_filling.process(depth_frame_h)
    if len(frames) == 10:
        frames.append(depth_frame_h)
        for j in xrange(0, 10):
            height_map = temporal.process(frames[x])
    else:
        frames.append(depth_frame_h)

height_map = np.asanyarray(height_map.get_data())[160:720, 280:1200]
height_map = cv.rotate(height_map, cv.ROTATE_180)

print "Height Map created..."
colorizer_me = rs.colorizer()
frames = deque([])

layers = [[-1, 29], [26, 49], [44, 65], [60, 92], [86, 200]]


def nothing():
    return


CALLBACK_KEY = nothing


def get_pieces(layer, l_min=None, l_max=None):
    global CALLBACK_KEY
    frameset = pipe.wait_for_frames()
    frameset = align.process(frameset)

    depth_frame = frameset.get_depth_frame()
    depth_frame = spatial.process(depth_frame)
    depth_frame = hole_filling.process(depth_frame)

    if len(frames) == 10:
        frames.popleft()
        frames.append(depth_frame)
        for i in xrange(0, 10):
            depth_frame = temporal.process(frames[i])
    else:
        frames.append(depth_frame)

    color_frames = frameset.get_color_frame()

    depth_data = np.asanyarray(depth_frame.get_data())[160:720, 280:1200]
    depth_data = cv.rotate(depth_data, cv.ROTATE_180)

    img = np.asanyarray(color_frames.get_data())
    correction = img[160:720, 280:1200]
    correction = cv.rotate(correction, cv.ROTATE_180)

    height_data = height_map - depth_data

    d_min = layers[layer][0] if l_min is None else l_min
    d_max = layers[layer][1] if l_max is None else l_max

    d_mask_lower = height_data >= d_min
    d_mask_upper = height_data <= d_max

    depth_mask = np.bitwise_and(d_mask_lower, d_mask_upper)

    depth_mask = depth_mask.astype(np.uint8)
    depth_mask *= 255
    correction = cv.bitwise_and(correction, correction, mask=depth_mask)

    hsv = cv.cvtColor(correction, cv.COLOR_BGR2HSV)

    mask_1 = cv.inRange(hsv, lower_red_1, upper_red_1)
    mask_2 = cv.inRange(hsv, lower_red_2, upper_red_2)
    mask_red = cv.bitwise_or(mask_1, mask_2)
    mask_red = cv.morphologyEx(mask_red, cv.MORPH_CLOSE, kernal, iterations=3)
    mask_red = cv.morphologyEx(mask_red, cv.MORPH_OPEN, kernal, iterations=2)

    mask_blue = cv.inRange(hsv, lower_blue, upper_blue)

    mask_green = cv.inRange(hsv, lower_green, upper_green)

    contours_red, hie_r = cv.findContours(mask_red, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    contours_blue, hie_b = cv.findContours(mask_blue, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    contours_green, hie_g = cv.findContours(mask_green, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    contours = [contours_red, contours_blue, contours_green]
    points = []
    for (i, color) in enumerate(contours):
        for (k, c) in enumerate(color):
            piece_rect = cv.minAreaRect(c)
            piece_center = piece_rect[0]
            area = cv.contourArea(c)

            if (piece_rect[1][0] > 80) or (piece_rect[1][1] > 80):
                continue

            if area > 1500:
                if abs(piece_rect[1][0] - piece_rect[1][1]) < 25:
                    continue

            if (area < 500) or (area > 3000):
                continue

            piece_bp = cv.boxPoints(piece_rect)
            piece_bp = np.array(piece_bp, dtype="int")
            rect = ipa.order_points(piece_bp)

            xt = int(rect[2][0] - 5)
            yt = int(rect[2][1] - 5)

            if yt > 560:
                xt = int(rect[0][0] + 2)
                yt = int(rect[0][1] + 2)
            try:
                h = int(height_map[yt][xt]) - int(depth_data[yt][xt])
            except IndexError:
                print "Out of Bounds, yt = " + str(yt)
                continue

            piece_bp = cv.boxPoints(piece_rect)
            piece_bp = np.array(piece_bp, dtype="int")
            rect = ipa.order_points(piece_bp)

            cv.drawContours(correction, [piece_bp], -1, (0, 255, 0), 2)

            cv.putText(correction, str(h), (int(rect[0, 0]) - 10, int(rect[0, 1])),
                       cv.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255), 2)

            if i == 0:
                color = "R"
            elif i == 1:
                color = "B"
            else:
                color = "G"

            if area > 1200:
                height = ipa.distance(rect[0], rect[3])
                width = ipa.distance(rect[0], rect[1])

                int_orientation = 0 if width > height else 1
                orientation = "Horizontal" if int_orientation == 0 else "Vertical"
                cv.putText(correction, orientation, (int(rect[3, 0]) + 10, int(rect[3, 1]) + 10),
                           cv.FONT_HERSHEY_SIMPLEX,
                           0.5, (255, 255, 255), 2)

                points.append(piece.Piece(rect, color, h, int_orientation))
            else:
                points.append(piece.Piece(rect, color, h))

            cv.circle(correction, (int(rect[2, 0]) - 5, int(rect[2, 1]) - 5), 5, colors[i], -1)
    cv.imshow("Out", correction)
    key = cv.waitKey(1)
    if key == ord('r'):
        CALLBACK_KEY()
        return []

    return points


def attach_callback(callback):
    global CALLBACK_KEY
    CALLBACK_KEY = callback


def detach_callback():
    global CALLBACK_KEY
    CALLBACK_KEY = nothing
